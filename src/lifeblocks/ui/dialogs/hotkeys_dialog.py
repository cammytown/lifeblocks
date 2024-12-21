import tkinter as tk
from tkinter import ttk, messagebox

class HotkeysDialog:
    def __init__(self, parent, settings_service):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Hotkeys")
        self.dialog.transient(parent)
        self.settings_service = settings_service
        self.setup_ui()
        
        # Center the dialog
        self.dialog.geometry("400x300")
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Make dialog modal
        self.dialog.grab_set()
        self.dialog.focus_set()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Hotkeys list
        hotkeys_frame = ttk.LabelFrame(main_frame, text="Keyboard Shortcuts", padding="10")
        hotkeys_frame.pack(fill="x", pady=(0, 10))

        # Start/Stop shortcut
        start_frame = ttk.Frame(hotkeys_frame)
        start_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(start_frame, text="Start/Stop Timer:").pack(side="left")
        self.start_var = tk.StringVar(value=self.settings_service.get_setting("hotkey_start", "Control-s"))
        start_entry = ttk.Entry(start_frame, textvariable=self.start_var, width=15)
        start_entry.pack(side="right")
        start_entry.bind('<KeyPress>', lambda e: self.capture_hotkey(e, self.start_var))

        # Pause/Resume shortcut
        pause_frame = ttk.Frame(hotkeys_frame)
        pause_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(pause_frame, text="Pause/Resume Timer:").pack(side="left")
        self.pause_var = tk.StringVar(value=self.settings_service.get_setting("hotkey_pause", "Pause"))
        pause_entry = ttk.Entry(pause_frame, textvariable=self.pause_var, width=15)
        pause_entry.pack(side="right")
        pause_entry.bind('<KeyPress>', lambda e: self.capture_hotkey(e, self.pause_var))

        # Help text
        ttk.Label(
            hotkeys_frame,
            text="Click in the entry field and press the desired key combination.\nFormat: Control/Alt/Shift + key (e.g. Control-s)",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        ).pack(fill="x", pady=(10, 0))

        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=(20, 0))

    def capture_hotkey(self, event, var):
        if event.keysym in ('Tab', 'Return', 'Escape'):
            return

        # Build the key combination string
        parts = []
        if event.state & 0x4:  # Control
            parts.append('Control')
        if event.state & 0x8:  # Alt
            parts.append('Alt')
        if event.state & 0x1:  # Shift
            parts.append('Shift')
        
        # Add the key itself
        key = event.keysym
        if key not in ('Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R'):
            parts.append(key)

        # Combine parts with hyphens
        hotkey = '-'.join(parts)
        
        # Update the variable and save to settings
        if var == self.start_var:
            self.settings_service.set_setting("hotkey_start", hotkey)
        elif var == self.pause_var:
            self.settings_service.set_setting("hotkey_pause", hotkey)
        
        var.set(hotkey)
        return "break"  # Prevent default handling 