import tkinter as tk
from tkinter import ttk, messagebox
import time

from lifeblocks.ui.dialogs.resistance_dialog import ResistanceDialog
from lifeblocks.ui.dialogs.completion_dialog import CompletionDialog
from lifeblocks.models.timeblock import TimeBlockState


class DurationDialog:
    def __init__(self, parent, initial_duration):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Set Duration")
        self.dialog.transient(parent)

        main_frame = ttk.Frame(self.dialog, padding="20", style="Card.TFrame")
        main_frame.pack(fill="both", expand=True)

        label = ttk.Label(main_frame, text="Duration (minutes):", style="TLabel")
        label.pack(pady=(0, 10))

        self.duration_var = tk.StringVar(value=str(initial_duration))
        self.entry = ttk.Entry(
            main_frame, textvariable=self.duration_var, width=10, justify="center"
        )
        self.entry.pack(pady=(0, 20))

        btn_frame = ttk.Frame(main_frame, style="Card.TFrame")
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.dialog.destroy,
        ).pack(side="right", padx=5)
        ttk.Button(
            btn_frame, text="Set", style="Accent.TButton", command=self.set_duration
        ).pack(side="right", padx=5)

        # Set geometry
        self.dialog.geometry("300x150")
        self.dialog.update_idletasks()

        # Center the dialog
        x = (
            parent.winfo_rootx()
            + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        )
        y = (
            parent.winfo_rooty()
            + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        )
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.grab_set()
        self.entry.focus_set()
        self.entry.selection_range(0, tk.END)

    def set_duration(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError
            self.result = duration
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number!")


class TimerFrame(ttk.Frame):
    def __init__(
        self,
        parent,
        timer_service,
        block_service,
        notification_service,
        history_frame,
    ):
        super().__init__(parent)
        self.timer_service = timer_service
        self.block_service = block_service
        self.notification_service = notification_service
        self.history_frame = history_frame
        self.current_block_queue = None
        self.current_block_index = 0
        self.current_block = None
        
        # Set up state change callback
        self.timer_service.set_state_change_callback(self.history_frame.refresh_history)
        
        self.setup_ui()
        
        # Initialize UI state based on timer service
        if self.timer_service.timer_active:
            self.current_block = self.timer_service.current_block
            # Create a single-block queue for the active block
            from lifeblocks.models.block_queue import BlockQueue
            self.current_block_queue = BlockQueue(self.current_block)
            self.current_block_index = 0
            self.block_var.set(f"{self.current_block.name} (1/1)")
            self.start_button.configure(text="Stop")
            self.pause_button.configure(state="normal")
            self.restart_button.configure(state="normal")
            if self.timer_service.paused:
                self.pause_button.configure(text="Resume")

    def setup_ui(self):
        self.configure(padding="20")

        # Get saved duration from settings
        default_duration = self.timer_service.get_default_duration()
        self.duration_var = tk.StringVar(value=str(default_duration))

        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)

        # Main container with light background
        main_container = ttk.Frame(self, style="Card.TFrame")
        main_container.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        main_container.grid_columnconfigure(1, weight=1)  # Center column expands

        # Left section - Block info
        block_frame = ttk.Frame(main_container)
        block_frame.grid(row=0, column=0, padx=20, sticky="w")

        ttk.Label(block_frame, text="Selected Block:").pack(anchor="w")
        self.block_var = tk.StringVar()
        self.block_label = ttk.Label(block_frame, textvariable=self.block_var)
        self.block_label.pack(pady=5, anchor="w")

        # Right section - Start button and timer
        control_frame = ttk.Frame(main_container)
        control_frame.grid(row=0, column=2, padx=20, sticky="e")

        # Timer display with label
        timer_frame = ttk.Frame(control_frame)
        timer_frame.pack(side="right", padx=20)

        ttk.Label(timer_frame, text="Time Remaining", font=("Helvetica", 8)).pack(
            anchor="e"
        )

        self.time_label = ttk.Label(
            timer_frame,
            text="25:00",
            font=("Helvetica", 48, "bold"),
            foreground="#7768E5",
            cursor="hand2",
        )
        self.time_label.pack(anchor="e")
        self.time_label.bind("<Button-1>", self.show_duration_dialog)

        # Button frame for Start and Pause
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side="right")

        # Start button
        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            style="Accent.TButton",
            command=self.toggle_timer,
        )
        self.start_button.pack(side="top", pady=(0, 5))

        # Pause button
        self.pause_button = ttk.Button(
            button_frame,
            text="Pause",
            style="Secondary.TButton",
            command=self.toggle_pause,
            state="disabled",
        )
        self.pause_button.pack(side="top", pady=(0, 5))

        # Restart button
        self.restart_button = ttk.Button(
            button_frame,
            text="Restart",
            style="Secondary.TButton",
            command=self.restart_timer,
            state="disabled",
        )
        self.restart_button.pack(side="top")

        self.update_timer()

    def restart_timer(self):
        """Restart the current time block."""
        if not self.timer_service.timer_active:
            return
            
        response = messagebox.askyesno(
            "Restart TimeBlock",
            "Are you sure you want to restart this time block from the beginning?"
        )
        
        if response:
            if self.timer_service.paused:
                self.toggle_pause()  # Unpause if paused
            self.timer_service.restart_timer()

    def reset_timer_ui(self):
        """Reset the timer UI to its initial state"""
        self.start_button.configure(text="Start")
        self.pause_button.configure(text="Pause", state="disabled")
        self.restart_button.configure(state="disabled")
        self.block_var.set("")
        self.current_block_queue = None
        self.current_block_index = 0

    def handle_session_completion(self, elapsed, was_stopped_manually=False):
        """Handle completion of a time block, showing dialog"""
        completion_dialog = CompletionDialog(self, self.current_block.name, elapsed)
        if was_stopped_manually:
            completion_dialog.notes_text.insert("1.0", "stopped manually")
        self.wait_window(completion_dialog.dialog)

        if completion_dialog.result:
            if completion_dialog.result.get("save", True):
                self.timer_service.save_session(
                    completion_dialog.result["total_elapsed"],
                    satisfaction_level=completion_dialog.result["satisfaction"],
                    notes=completion_dialog.result["notes"],
                )
            else:
                # Mark the timeblock as cancelled without saving satisfaction/notes
                self.timer_service.active_timeblock.state = TimeBlockState.CANCELLED_ON_COMPLETE
                self.timer_service.session.commit()

        if not was_stopped_manually and self.current_block_queue:
            self.current_block_index += 1
            if self.current_block_index < len(self.current_block_queue.blocks):
                base_duration = int(self.duration_var.get())
                self.start_next_block(base_duration)
                return

        self.reset_timer_ui()

    def toggle_pause(self):
        if self.timer_service.timer_active:
            if not self.timer_service.paused:
                if self.timer_service.pause_timer():
                    self.pause_button.configure(text="Resume")
            else:
                if self.timer_service.resume_timer():
                    self.pause_button.configure(text="Pause")

    def toggle_timer(self):
        if not self.timer_service.timer_active:
            try:
                base_duration = int(self.duration_var.get())
                if base_duration <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Duration must be a positive integer!")
                return

            # Select random block queue
            block_queue = self.block_service.pick_block_queue()
            if not block_queue or not block_queue.blocks:
                messagebox.showwarning("Warning", "No blocks available!")
                return

            self.current_block_queue = block_queue
            self.current_block_index = 0
            self.start_next_block(base_duration)
        else:
            # First confirm if user wants to stop
            stop_response = messagebox.askyesno(
                "Stop TimeBlock",
                "Are you sure you want to stop this timeblock?"
            )
            
            if not stop_response:
                return
                
            # If confirmed, stop the timer and handle saving
            elapsed = self.timer_service.stop_timer()
            if elapsed:
                save_response = messagebox.askyesno(
                    "Save TimeBlock",
                    f"Do you want to save this timeblock to history?\n\n"
                    f"Elapsed time: {elapsed:.1f} minutes"
                )

                if save_response:  # Yes - show completion dialog
                    self.handle_session_completion(elapsed, was_stopped_manually=True)
                else:  # No - just reset UI
                    self.reset_timer_ui()

    def start_next_block(self, base_duration):
        """Start the next block in the queue"""
        if not self.current_block_queue or self.current_block_index >= len(
            self.current_block_queue.blocks
        ):
            self.reset_timer_ui()
            return

        block = self.current_block_queue.blocks[self.current_block_index]

        # Show resistance dialog for the next block
        resistance_dialog = ResistanceDialog(self, block.name, self.current_block_queue.pick_reason)
        self.wait_window(resistance_dialog.dialog)

        if resistance_dialog.result is None:
            self.reset_timer_ui()
            return

        if resistance_dialog.result["delayed"]:
            # Create a delayed timeblock
            self.block_service.create_delayed_timeblock(
                block.id,
                delay_hours=resistance_dialog.result["delay_hours"]
            )
            self.reset_timer_ui()
            return

        # Check if this block was force-started through the UI
        was_force_started = hasattr(self.current_block_queue, 'was_force_started') and self.current_block_queue.was_force_started

        # For force-started blocks, use length_multiplier directly
        if was_force_started:
            adjusted_duration = base_duration * block.length_multiplier
        else:
            # For normal queues (including naturally occurring single-block queues),
            # calculate adjusted duration based on the block's proportion of the total queue
            block_proportion = block.length_multiplier / self.current_block_queue.total_multiplier
            adjusted_duration = base_duration * block_proportion

        self.current_block = block
        self.block_var.set(
            f"{block.name} ({self.current_block_index + 1}/{len(self.current_block_queue.blocks)})"
        )
        self.timer_service.start_timer(
            block, 
            adjusted_duration, 
            resistance_dialog.result["resistance"], 
            forced=was_force_started,
            pick_reason=self.current_block_queue.pick_reason
        )
        self.start_button.configure(text="Stop")
        self.pause_button.configure(state="normal")
        self.restart_button.configure(state="normal")

    def update_timer(self):
        if self.timer_service.timer_active:
            minutes, seconds, is_finished = self.timer_service.get_remaining_time()

            if is_finished and self.current_block:
                elapsed = self.timer_service.stop_timer()
                self.notification_service.alert_time_up(self.current_block.name)
                self.handle_session_completion(elapsed)
            else:
                self.time_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        else:
            try:
                minutes = int(self.duration_var.get())
                self.time_label.configure(text=f"{minutes:02d}:00")
            except ValueError:
                self.time_label.configure(text="00:00")

        self.after(1000, self.update_timer)

    def show_duration_dialog(self, event=None):
        if not self.timer_service.timer_active:
            try:
                current_duration = int(self.duration_var.get())
            except:
                current_duration = self.timer_service.get_default_duration()

            dialog = DurationDialog(self, current_duration)
            self.wait_window(dialog.dialog)

            if dialog.result:
                self.duration_var.set(str(dialog.result))
                # Save the new duration to settings
                self.timer_service.set_default_duration(dialog.result)
                self.update_timer()
