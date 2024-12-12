import tkinter as tk
from tkinter import ttk, messagebox


class AddBlockDialog:
    def __init__(self, parent, block_service, selected_block_name=None):
        self.result = False
        self.block_service = block_service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Block")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - 100
        self.dialog.geometry(f"+{x}+{y}")  # Only set position, not size

        self.selected_block_name = selected_block_name
        self.setup_ui()

        # After UI is set up, prevent resizing smaller than needed
        self.dialog.update_idletasks()  # Ensure dialog has calculated its size
        self.dialog.minsize(self.dialog.winfo_width(), self.dialog.winfo_height())
        parent.wait_window(self.dialog)

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="30")
        main_frame.pack(fill="both", expand=True)

        # Name Entry
        ttk.Label(main_frame, text="Name:").pack(anchor="w", pady=(0, 5))
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.pack(fill="x", pady=(0, 20))

        # Weight Entry
        ttk.Label(main_frame, text="Weight:").pack(anchor="w", pady=(0, 5))
        self.weight_entry = ttk.Entry(main_frame, width=10)
        self.weight_entry.insert(0, "1")
        self.weight_entry.pack(anchor="w", pady=(0, 20))

        # Max Interval Entry
        ttk.Label(main_frame, text="Max Interval (hours):").pack(
            anchor="w", pady=(0, 5)
        )
        self.interval_entry = ttk.Entry(main_frame, width=10)
        self.interval_entry.pack(anchor="w", pady=(0, 20))

        # Parent Selection
        ttk.Label(main_frame, text="Parent:").pack(anchor="w", pady=(0, 5))
        self.parent_combo = ttk.Combobox(main_frame, state="readonly")
        self.parent_combo["values"] = ["None"] + [
            p.name for p in self.block_service.get_all_blocks()
        ]
        self.parent_combo.set(
            self.selected_block_name if self.selected_block_name else "None"
        )
        self.parent_combo.pack(fill="x", pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(
            side="right", padx=5
        )
        ttk.Button(
            button_frame, text="Add", style="Accent.TButton", command=self.add_block
        ).pack(side="right", padx=5)

    def add_block(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Block name cannot be empty!")
            return

        try:
            weight = int(self.weight_entry.get())
            if weight < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Weight must be a positive integer!")
            return

        # Parse max interval
        max_interval_hours = None
        interval_text = self.interval_entry.get().strip()
        if interval_text:
            try:
                max_interval_hours = float(interval_text)
                if max_interval_hours < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", "Max interval must be a positive number or empty!"
                )
                return

        parent_name = self.parent_combo.get()
        self.block_service.add_block(
            name, weight, parent_name, max_interval_hours=max_interval_hours
        )
        self.result = True
        self.dialog.destroy()
