# Mostly generated with Claude 3.5 Sonnet on 2024-12-09

import sqlite3
import random
import time
import os
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

class ProjectTimer:
    def __init__(self):
        self.conn = sqlite3.connect('projects.db')
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.current_project = None
        self.timer_active = False
        self.session_start = None

        # Check if notify-send is available
        self.has_notifications = os.system('which notify-send >/dev/null 2>&1') == 0

        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Project Timer")
        self.setup_gui()

    def setup_database(self):
        # Projects table with weight and last_picked timestamp
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                weight INTEGER DEFAULT 1,
                last_picked TIMESTAMP,
                parent_id INTEGER NULL,
                FOREIGN KEY (parent_id) REFERENCES projects (id)
            )
        ''')
        
        # History table with soft delete
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                start_time TIMESTAMP,
                duration_minutes FLOAT,
                notes TEXT,
                deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        self.conn.commit()

    def setup_gui(self):
        # Project management frame
        management_frame = ttk.LabelFrame(self.root, text="Project Management")
        management_frame.pack(padx=5, pady=5, fill="x")

        # Add project
        ttk.Label(management_frame, text="Project name:").grid(row=0, column=0, padx=5, pady=5)
        self.project_entry = ttk.Entry(management_frame)
        self.project_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(management_frame, text="Weight:").grid(row=0, column=2, padx=5, pady=5)
        self.weight_entry = ttk.Entry(management_frame, width=5)
        self.weight_entry.insert(0, "1")
        self.weight_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Parent project dropdown
        ttk.Label(management_frame, text="Parent:").grid(row=0, column=4, padx=5, pady=5)
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(management_frame, textvariable=self.parent_var)
        self.parent_combo['values'] = ['None']
        self.parent_combo.current(0)
        self.parent_combo.grid(row=0, column=5, padx=5, pady=5)
        
        ttk.Button(management_frame, text="Add Project", 
                  command=self.add_project).grid(row=0, column=6, padx=5, pady=5)

        # Timer frame
        timer_frame = ttk.LabelFrame(self.root, text="Timer")
        timer_frame.pack(padx=5, pady=5, fill="x")

        # Random duration toggle
        self.random_duration = tk.BooleanVar(value=False)
        ttk.Checkbutton(timer_frame, text="Random Duration", 
                       variable=self.random_duration).grid(row=0, column=0, padx=5, pady=5)

        # Min time
        ttk.Label(timer_frame, text="Min Minutes:").grid(row=0, column=1, padx=5, pady=5)
        self.min_time_var = tk.StringVar(value="15")
        ttk.Entry(timer_frame, textvariable=self.min_time_var, width=5).grid(row=0, column=2, padx=5, pady=5)

        # Max time
        ttk.Label(timer_frame, text="Max Minutes:").grid(row=0, column=3, padx=5, pady=5)
        self.max_time_var = tk.StringVar(value="45")
        ttk.Entry(timer_frame, textvariable=self.max_time_var, width=5).grid(row=0, column=4, padx=5, pady=5)
        
        self.timer_label = ttk.Label(timer_frame, text="00:00")
        self.timer_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Timer control buttons
        button_frame = ttk.Frame(timer_frame)
        button_frame.grid(row=0, column=6, padx=5, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="Start New Session", 
                                     command=self.start_new_session)
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Session", 
                                    command=self.stop_session, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=2)

        # Project tree
        self.project_tree = ttk.Treeview(self.root, columns=("Weight", "Last Picked"), 
                                       show="tree headings")
        self.project_tree.heading("Weight", text="Weight")
        self.project_tree.heading("Last Picked", text="Last Picked")
        self.project_tree.pack(padx=5, pady=5, fill="both", expand=True)

        # Project tree context menu
        self.project_menu = tk.Menu(self.root, tearoff=0)
        self.project_menu.add_command(label="Edit", command=self.edit_project)
        self.project_menu.add_command(label="Delete", command=self.delete_project)
        
        self.project_tree.bind("<Button-3>", self.show_project_menu)
        self.project_tree.bind("<Double-1>", self.edit_project)

        # History frame
        history_frame = ttk.LabelFrame(self.root, text="Session History")
        history_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(history_controls, text="Undo Deletions", 
                  command=self.undo_deletions).pack(side=tk.RIGHT, padx=5)
        ttk.Button(history_controls, text="Clear All History", 
                  command=self.clear_history).pack(side=tk.RIGHT, padx=5)
        ttk.Button(history_controls, text="Delete Selected", 
                  command=self.delete_selected_history).pack(side=tk.RIGHT, padx=5)
        
        # History tree
        self.history_tree = ttk.Treeview(history_frame, 
                                        columns=("Project", "Start Time", "Duration", "Notes"),
                                        show="headings")
        self.history_tree.heading("Project", text="Project")
        self.history_tree.heading("Start Time", text="Start Time")
        self.history_tree.heading("Duration", text="Duration (min)")
        self.history_tree.heading("Notes", text="Notes")
        self.history_tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        self.update_project_list()
        self.update_history()

    def stop_session(self):
        if not self.timer_active:
            return
            
        self.timer_active = False
        elapsed_minutes = (time.time() - (self.end_time - (self.session_duration * 60))) / 60
        
        response = messagebox.askyesnocancel("Stop Session", 
            "Do you want to save this session to history?\n\n"
            f"Elapsed time: {elapsed_minutes:.1f} minutes")
        
        if response is None:  # Cancel - resume timer
            self.timer_active = True
            self.update_timer()
            return
            
        if response:  # Yes - save to history
            self.cursor.execute('''
                INSERT INTO history (project_id, start_time, duration_minutes, notes)
                VALUES (?, ?, ?, ?)
            ''', (self.current_project[0], self.session_start, elapsed_minutes, "Session stopped early"))
            self.conn.commit()
            self.update_history()
            
        # Reset timer state
        self.timer_label.config(text="00:00")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.current_project = None
        self.session_start = None


    def clear_history(self):
        if messagebox.askyesno("Clear History", 
                             "Are you sure you want to delete ALL session history?"):
            now = datetime.now()
            self.cursor.execute('''
                UPDATE history 
                SET deleted = 1, deleted_at = ?
                WHERE deleted = 0
            ''', (now,))
            self.conn.commit()
            self.update_history()

    def delete_selected_history(self):
        selected_items = self.history_tree.selection()
        if not selected_items:
            return
            
        if messagebox.askyesno("Delete Sessions", 
                              f"Delete {len(selected_items)} selected sessions?"):
            now = datetime.now()
            for item in selected_items:
                values = self.history_tree.item(item)['values']
                self.cursor.execute('''
                    UPDATE history 
                    SET deleted = 1, deleted_at = ?
                    WHERE project_id IN (SELECT id FROM projects WHERE name = ?) 
                    AND start_time = ? 
                    AND duration_minutes = ?
                    AND deleted = 0
                ''', (now, values[0], values[1], values[2]))
            
            self.conn.commit()
            self.update_history()

    def undo_deletions(self):
        # Show dialog with recent deletions
        dialog = tk.Toplevel(self.root)
        dialog.title("Recover Deleted Sessions")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create treeview for deleted sessions
        deleted_tree = ttk.Treeview(dialog, 
                                  columns=("Project", "Start Time", "Duration", "Deleted At"),
                                  show="headings")
        deleted_tree.heading("Project", text="Project")
        deleted_tree.heading("Start Time", text="Start Time")
        deleted_tree.heading("Duration", text="Duration (min)")
        deleted_tree.heading("Deleted At", text="Deleted At")
        deleted_tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Get deleted sessions
        self.cursor.execute('''
            SELECT p.name, h.start_time, h.duration_minutes, h.deleted_at
            FROM history h
            JOIN projects p ON h.project_id = p.id
            WHERE h.deleted = 1
            ORDER BY h.deleted_at DESC
        ''')
        
        for session in self.cursor.fetchall():
            deleted_tree.insert("", "end", values=session)
        
        def recover_selected():
            selected = deleted_tree.selection()
            if not selected:
                return
                
            for item in selected:
                values = deleted_tree.item(item)['values']
                self.cursor.execute('''
                    UPDATE history 
                    SET deleted = 0, deleted_at = NULL
                    WHERE project_id IN (SELECT id FROM projects WHERE name = ?) 
                    AND start_time = ? 
                    AND duration_minutes = ?
                    AND deleted_at = ?
                ''', (values[0], values[1], values[2], values[3]))
            
            self.conn.commit()
            self.update_history()
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Recover Selected", 
                  command=recover_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def update_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        self.cursor.execute('''
            SELECT p.name, h.start_time, h.duration_minutes, h.notes
            FROM history h
            JOIN projects p ON h.project_id = p.id
            WHERE h.deleted = 0
            ORDER BY h.start_time DESC
            LIMIT 100
        ''')
        
        for session in self.cursor.fetchall():
            self.history_tree.insert("", "end", values=session)

    def start_timer(self, minutes):
        if self.timer_active:
            return

        self.timer_active = True
        self.session_start = datetime.now()
        self.session_duration = minutes
        self.end_time = time.time() + (minutes * 60)
        self.stop_button.config(state="normal")
        self.update_timer()

    def update_timer(self):
        if not self.timer_active:
            return

        remaining = max(0, self.end_time - time.time())
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        if remaining <= 0:
            self.timer_active = False
            
            # Log session in history
            self.cursor.execute('''
                INSERT INTO history (project_id, start_time, duration_minutes, notes)
                VALUES (?, ?, ?, ?)
            ''', (self.current_project[0], self.session_start, self.session_duration, None))
            self.conn.commit()
            
            self.update_history()
            self.alert_time_up(self.current_project[1])
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.current_project = None
            self.session_start = None
            return
            
        self.root.after(1000, self.update_timer)

    def alert_time_up(self, project_name):
        try:
            subprocess.run([
                'notify-send',
                'Time Up!',
                f'Project "{project_name}" timer has finished',
                '-u', 'critical'  # Makes it more prominent
            ])
        except FileNotFoundError:
            # Fallback to regular messagebox if notify-send isn't available
            messagebox.showinfo("Time's Up!", f"Time's up for {project_name}!")

        # Audio alert - try to play from local alerts folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # alerts_dir = os.path.join(script_dir, 'alerts')

        # Look for an audio file in the alerts folder
        #@TODO Maybe

        # Audio alert - using paplay (comes with PulseAudio) or aplay
        #@SCAFFOLDING youtube-hyoshigi.opus just something I swiped off internet

        audio_file = os.path.join(script_dir, 'youtube-hyoshigi.opus')
        
        try:
            subprocess.run(['paplay', audio_file])
        except FileNotFoundError:
            try:
                subprocess.run(['aplay', audio_file])
            except FileNotFoundError:
                pass  # No audio if neither is available

    def add_project(self):
        name = self.project_entry.get().strip()
        try:
            weight = int(self.weight_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Weight must be a number")
            return

        if name:
            parent_name = self.parent_var.get()
            parent_id = None
            
            if parent_name != 'None':
                self.cursor.execute('SELECT id FROM projects WHERE name = ?', (parent_name,))
                result = self.cursor.fetchone()
                if result:
                    parent_id = result[0]

            self.cursor.execute('''
                INSERT INTO projects (name, weight, last_picked, parent_id)
                VALUES (?, ?, NULL, ?)
            ''', (name, weight, parent_id))
            self.conn.commit()
            
            self.project_entry.delete(0, tk.END)
            self.weight_entry.delete(0, tk.END)
            self.weight_entry.insert(0, "1")
            self.update_project_list()


    def show_project_menu(self, event):
        item = self.project_tree.identify_row(event.y)
        if item:
            self.project_tree.selection_set(item)
            self.project_menu.post(event.x_root, event.y_root)

    def edit_project(self, event=None):
        if event:  # Called from double-click
            item = self.project_tree.identify_row(event.y)
            if not item:
                return
            self.project_tree.selection_set(item)
        
        selected = self.project_tree.selection()
        if not selected:
            return
            
        item = selected[0]
        project_name = self.project_tree.item(item)['text']
        
        # Get current project data
        self.cursor.execute('''
            SELECT id, name, weight, parent_id
            FROM projects
            WHERE name = ?
        ''', (project_name,))
        project = self.cursor.fetchone()
        
        if not project:
            return
            
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Project: {project_name}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Project name
        ttk.Label(dialog, text="Name:").pack(padx=5, pady=5)
        name_var = tk.StringVar(value=project[1])
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(padx=5, fill=tk.X)
        
        # Weight
        ttk.Label(dialog, text="Weight:").pack(padx=5, pady=5)
        weight_var = tk.StringVar(value=str(project[2]))
        weight_entry = ttk.Entry(dialog, textvariable=weight_var)
        weight_entry.pack(padx=5, fill=tk.X)
        
        # Parent project
        ttk.Label(dialog, text="Parent:").pack(padx=5, pady=5)
        parent_var = tk.StringVar()
        parent_combo = ttk.Combobox(dialog, textvariable=parent_var)
        
        # Get all possible parents (excluding self and children)
        self.cursor.execute('''
            SELECT name 
            FROM projects 
            WHERE id != ? AND id NOT IN (
                SELECT id FROM projects WHERE parent_id = ?
            )
        ''', (project[0], project[0]))
        
        parents = ['None'] + [row[0] for row in self.cursor.fetchall()]
        parent_combo['values'] = parents
        
        if project[3]:
            self.cursor.execute('SELECT name FROM projects WHERE id = ?', (project[3],))
            current_parent = self.cursor.fetchone()
            if current_parent:
                parent_var.set(current_parent[0])
        else:
            parent_var.set('None')
            
        parent_combo.pack(padx=5, fill=tk.X)
        
        def save_changes():
            try:
                new_weight = int(weight_var.get())
                if new_weight <= 0:
                    raise ValueError("Weight must be positive")
            except ValueError:
                messagebox.showerror("Error", "Weight must be a positive number")
                return
                
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty")
                return
                
            # Get parent_id
            new_parent = parent_var.get()
            if new_parent == 'None':
                parent_id = None
            else:
                self.cursor.execute('SELECT id FROM projects WHERE name = ?', (new_parent,))
                parent_result = self.cursor.fetchone()
                parent_id = parent_result[0] if parent_result else None
            
            # Update project
            self.cursor.execute('''
                UPDATE projects
                SET name = ?, weight = ?, parent_id = ?
                WHERE id = ?
            ''', (new_name, new_weight, parent_id, project[0]))
            
            self.conn.commit()
            self.update_project_list()
            dialog.destroy()
            
        ttk.Button(dialog, text="Save", command=save_changes).pack(pady=20)

    def delete_project(self):
        selected = self.project_tree.selection()
        if not selected:
            return
            
        item = selected[0]
        project_name = self.project_tree.item(item)['text']
        
        if messagebox.askyesno("Delete Project", 
                              f"Delete project '{project_name}' and all its children?"):
            self.cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
            project = self.cursor.fetchone()
            
            if project:
                # Recursively delete children
                def delete_children(parent_id):
                    self.cursor.execute('SELECT id FROM projects WHERE parent_id = ?', (parent_id,))
                    for child in self.cursor.fetchall():
                        delete_children(child[0])
                        self.cursor.execute('DELETE FROM projects WHERE id = ?', (child[0],))
                
                delete_children(project[0])
                self.cursor.execute('DELETE FROM projects WHERE id = ?', (project[0],))
                self.conn.commit()
                self.update_project_list()

    def update_project_list(self):
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
            
        # Update parent project dropdown
        self.cursor.execute('SELECT DISTINCT name FROM projects WHERE parent_id IS NULL')
        parents = ['None'] + [row[0] for row in self.cursor.fetchall()]
        self.parent_combo['values'] = parents
        
        # Populate tree with hierarchical project structure
        def add_projects_to_tree(parent_id=None, parent_item=""):
            self.cursor.execute('''
                SELECT id, name, weight, last_picked
                FROM projects
                WHERE parent_id IS ?
                ORDER BY name
            ''', (parent_id,))
            
            for project in self.cursor.fetchall():
                last_picked = project[3] if project[3] else "Never"
                item = self.project_tree.insert(parent_item, "end", 
                                              values=(project[2], last_picked),
                                              text=project[1])
                # Recursively add children
                add_projects_to_tree(project[0], item)
        
        add_projects_to_tree()

    def pick_project(self):
        # First pick a top-level project
        self.cursor.execute('''
            SELECT id, name, weight, last_picked
            FROM projects
            WHERE parent_id IS NULL
        ''')
        projects = self.cursor.fetchall()
        
        if not projects:
            return None

        # Calculate time-based weights
        now = datetime.now()
        weighted_projects = []
        
        for project in projects:
            base_weight = project[2]
            last_picked = datetime.strptime(project[3], '%Y-%m-%d %H:%M:%S.%f') if project[3] else None
            
            if last_picked:
                days_since = (now - last_picked).days
                time_weight = days_since / 7
            else:
                time_weight = 2
                
            total_weight = base_weight * (1 + time_weight)
            weighted_projects.append((project, total_weight))

        # Random selection based on weights
        total = sum(w for _, w in weighted_projects)
        r = random.uniform(0, total)
        upto = 0
        
        selected_project = None
        for project, weight in weighted_projects:
            upto += weight
            if upto > r:
                selected_project = project
                break
                
        if not selected_project:
            selected_project = weighted_projects[-1][0]

        # Check if selected project has children
        self.cursor.execute('''
            SELECT id, name, weight, last_picked
            FROM projects
            WHERE parent_id = ?
        ''', (selected_project[0],))
        
        children = self.cursor.fetchall()
        
        if children:
            # Randomly select a child project using the same weighting system
            child_weights = []
            for child in children:
                base_weight = child[2]
                last_picked = datetime.strptime(child[3], '%Y-%m-%d %H:%M:%S.%f') if child[3] else None
                
                if last_picked:
                    days_since = (now - last_picked).days
                    time_weight = days_since / 7
                else:
                    time_weight = 2
                    
                total_weight = base_weight * (1 + time_weight)
                child_weights.append((child, total_weight))

            total = sum(w for _, w in child_weights)
            r = random.uniform(0, total)
            upto = 0
            
            for child, weight in child_weights:
                upto += weight
                if upto > r:
                    return child
                    
            return child_weights[-1][0]
        
        return selected_project

    def start_new_session(self):
        try:
            if self.random_duration.get():
                min_time = float(self.min_time_var.get())
                max_time = float(self.max_time_var.get())
                if min_time > max_time:
                    min_time, max_time = max_time, min_time
                minutes = random.uniform(min_time, max_time)
            else:
                minutes = float(self.min_time_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid time value")
            return

        project = self.pick_project()
        if not project:
            messagebox.showinfo("No Projects", "Please add some projects first!")
            return

        self.current_project = project
        
        # Update last_picked timestamp
        self.cursor.execute('''
            UPDATE projects
            SET last_picked = ?
            WHERE id = ?
        ''', (datetime.now(), project[0]))
        self.conn.commit()
        
        self.update_project_list()
        self.start_button.config(state="disabled")
        
        messagebox.showinfo("New Project", f"Work on: {project[1]} for {minutes:.1f} minutes")
        self.start_timer(minutes)

    def run(self):
        self.root.mainloop()
    
if __name__ == "__main__":
    app = ProjectTimer()
    app.run()