import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


class SettingsDialog:
    def __init__(self, parent, settings_service):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.settings_service = settings_service
        self.setup_ui()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Block Queue Settings
        queue_frame = ttk.LabelFrame(main_frame, text="Block Queue Settings", padding="10")
        queue_frame.pack(fill="x", pady=(0, 10))

        # Selection Mode
        selection_frame = ttk.Frame(queue_frame)
        selection_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            selection_frame,
            text="Block Selection Mode:",
            font=('TkDefaultFont', 10, 'bold')
        ).pack(anchor="w")

        self.leaf_based_var = tk.BooleanVar(
            value=self.settings_service.get_setting("use_leaf_based_selection", "true") == "true"
        )
        
        modes_frame = ttk.Frame(queue_frame)
        modes_frame.pack(fill="x", pady=(0, 10))
                
        ttk.Radiobutton(
            modes_frame,
            text="Leaf-based Selection",
            variable=self.leaf_based_var,
            value=True,
            command=self.save_selection_mode
        ).pack(anchor="w", pady=(5, 0))
        
        ttk.Label(
            modes_frame,
            text="Compare all end-tasks directly, with weights multiplied through their parent chain",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        ).pack(anchor="w", padx=(20, 0))
        
        # Radio buttons for selection modes
        ttk.Radiobutton(
            modes_frame,
            text="Hierarchical Selection",
            variable=self.leaf_based_var,
            value=False,
            command=self.save_selection_mode
        ).pack(anchor="w")
        
        ttk.Label(
            modes_frame,
            text="Select blocks level by level through the hierarchy",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        ).pack(anchor="w", padx=(20, 0))

        # Separator
        ttk.Separator(queue_frame, orient="horizontal").pack(fill="x", pady=(0, 10))

        # Fill Queue Option
        self.fill_queue_var = tk.BooleanVar(value=self.settings_service.get_setting("fill_fractional_queues", "true") == "true")
        ttk.Checkbutton(
            queue_frame,
            text="Fill fractional block queues to make a full block",
            variable=self.fill_queue_var,
            command=self.save_fill_queue_setting
        ).pack(pady=(0, 10))

        # Time Weight Setting
        time_weight_frame = ttk.Frame(queue_frame)
        time_weight_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(
            time_weight_frame,
            text="Double a block's selection weight after (hours):",
            wraplength=300
        ).pack(side="left")
        
        # Load existing setting or default to 48 hours
        self.time_weight_var = tk.StringVar(
            value=self.settings_service.get_setting("hours_until_double_weight", "48")
        )
        time_weight_entry = ttk.Entry(time_weight_frame, textvariable=self.time_weight_var, width=10)
        time_weight_entry.pack(side="left", padx=(5, 0))
        time_weight_entry.bind('<FocusOut>', lambda e: self.save_time_weight_setting())
        time_weight_entry.bind('<Return>', lambda e: self.save_time_weight_setting())

        # Add a tooltip/help text
        ttk.Label(
            queue_frame,
            text="Weight increases linearly with time - lower values make blocks get picked more quickly",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        ).pack(fill="x", pady=(0, 10))

        # Sound Settings
        sound_frame = ttk.LabelFrame(main_frame, text="Sound Settings", padding="10")
        sound_frame.pack(fill="x", pady=(0, 10))

        # Play Sound Option
        self.play_sound_var = tk.BooleanVar(value=self.settings_service.get_setting("play_sound", "true") == "true")
        ttk.Checkbutton(
            sound_frame,
            text="Play sound when block timer finishes",
            variable=self.play_sound_var,
            command=self.save_sound_settings
        ).pack(pady=(0, 10))

        # Sound File Path
        ttk.Label(sound_frame, text="Sound file:").pack(anchor="w")
        sound_path_frame = ttk.Frame(sound_frame)
        sound_path_frame.pack(fill="x", pady=(5, 0))

        self.sound_file_var = tk.StringVar(value=self.settings_service.get_setting("sound_file", "youtube-hyoshigi.opus"))
        self.sound_file_entry = ttk.Entry(sound_path_frame, textvariable=self.sound_file_var)
        self.sound_file_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(
            sound_path_frame,
            text="Browse",
            command=self.browse_sound_file
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            sound_path_frame,
            text="Test",
            command=self.test_sound
        ).pack(side="right", padx=(5, 0))

        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(
            pady=(20, 0)
        )

    def save_fill_queue_setting(self):
        self.settings_service.set_setting("fill_fractional_queues", str(self.fill_queue_var.get()).lower())

    def save_sound_settings(self):
        self.settings_service.set_setting("play_sound", str(self.play_sound_var.get()).lower())
        self.settings_service.set_setting("sound_file", self.sound_file_var.get())

    def browse_sound_file(self):
        filename = filedialog.askopenfilename(
            title="Select Sound File",
            filetypes=[
                ("Opus Files", ".opus"),
                ("Wave Files", ".wav"),
                ("MP3 Files", ".mp3"),
                ("Ogg Files", ".ogg"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.sound_file_var.set(filename)
            self.save_sound_settings()

    def test_sound(self):
        from lifeblocks.services.notification_service import NotificationService
        notification_service = NotificationService(self.settings_service)
        notification_service.test_sound()

    def save_time_weight_setting(self):
        try:
            hours = float(self.time_weight_var.get())
            if hours <= 0:
                hours = 48  # Reset to default if invalid
            
            self.time_weight_var.set(str(int(hours)))
            self.settings_service.set_setting("hours_until_double_weight", str(int(hours)))
        except ValueError:
            # Reset to default if invalid input
            self.time_weight_var.set("48")
            self.settings_service.set_setting("hours_until_double_weight", "48") 

    def save_selection_mode(self):
        self.settings_service.set_setting("use_leaf_based_selection", str(self.leaf_based_var.get()).lower())