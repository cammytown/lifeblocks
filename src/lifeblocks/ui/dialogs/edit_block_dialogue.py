import tkinter as tk
from tkinter import ttk, messagebox


class EditBlockDialog:
    def __init__(self, parent, block_service, block_id):
        self.result = False
        self.block_service = block_service
        self.block = next(
            (p for p in block_service.get_all_blocks() if p.id == block_id), None
        )

        if not self.block:
            messagebox.showerror("Error", "Block not found!")
            return

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Block")
        self.dialog.transient(parent)

        # Center dialog on parent
        x = parent.winfo_rootx() + parent.winfo_width() // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2

        # Set up the UI first
        self.setup_ui()

        # Now center the dialog after UI is set up and size is known
        self.dialog.update_idletasks()  # Ensure dialog has calculated its size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        x = x - dialog_width // 2
        y = y - dialog_height // 2
        self.dialog.geometry(f"+{x}+{y}")  # Only set position, not size

        # Bind return key to save
        self.name_entry.bind("<Return>", lambda event: self.save())

        # After UI is set up, set the grab and wait
        self.dialog.grab_set()
        parent.wait_window(self.dialog)

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Name Entry
        ttk.Label(main_frame, text="Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.insert(0, self.block.name)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Weight Entry
        ttk.Label(main_frame, text="Weight:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.weight_entry = ttk.Entry(main_frame, width=10)
        self.weight_entry.insert(0, str(self.block.weight))
        self.weight_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Max Interval Entry
        ttk.Label(main_frame, text="Max Interval (hours):").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.interval_entry = ttk.Entry(main_frame, width=10)
        if self.block.max_interval_hours is not None:
            self.interval_entry.insert(0, str(self.block.max_interval_hours))
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Length Multiplier Entry
        ttk.Label(main_frame, text="Length Multiplier:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        self.length_multiplier_entry = ttk.Entry(main_frame, width=10)
        self.length_multiplier_entry.insert(0, str(self.block.length_multiplier))
        self.length_multiplier_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Min Duration Entry
        ttk.Label(main_frame, text="Min Duration (minutes):").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        self.min_duration_entry = ttk.Entry(main_frame, width=10)
        if self.block.min_duration_minutes is not None:
            self.min_duration_entry.insert(0, str(self.block.min_duration_minutes))
        self.min_duration_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Parent Combobox
        ttk.Label(main_frame, text="Parent:").grid(
            row=5, column=0, padx=5, pady=5, sticky="e"
        )
        self.parent_combo = ttk.Combobox(main_frame, state="readonly", width=28)

        # Get all possible parents (excluding self and children)
        all_blocks = self.block_service.get_all_blocks()
        invalid_parents = self._get_invalid_parents(all_blocks, self.block.id)
        valid_parents = ["None"] + [
            p.name for p in all_blocks if p.id not in invalid_parents
        ]

        self.parent_combo["values"] = valid_parents
        current_parent = "None"
        if self.block.parent_id is not None:
            parent_block = next(
                (p for p in all_blocks if p.id == self.block.parent_id), None
            )
            if parent_block:
                current_parent = parent_block.name
        self.parent_combo.set(current_parent)
        self.parent_combo.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Configure grid column weights
        main_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame, text="Save", command=self.save, style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(
            side=tk.LEFT, padx=5
        )

    def _get_invalid_parents(self, blocks, block_id):
        """Get IDs of self and all child blocks (invalid as parents)"""
        invalid_ids = {block_id}

        def add_children(parent_id):
            for block in blocks:
                if block.parent_id == parent_id:
                    invalid_ids.add(block.id)
                    add_children(block.id)

        add_children(block_id)
        return invalid_ids

    def save(self):
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

        # Parse length multiplier
        try:
            length_multiplier = float(self.length_multiplier_entry.get())
            if length_multiplier <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "Length multiplier must be a positive number!"
            )
            return

        # Parse min duration
        min_duration_minutes = None
        min_duration_text = self.min_duration_entry.get().strip()
        if min_duration_text:
            try:
                min_duration_minutes = float(min_duration_text)
                if min_duration_minutes < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", "Minimum duration must be a positive number or empty!"
                )
                return

        parent_name = self.parent_combo.get()

        self.block_service.update_block(
            self.block.id,
            name=name,
            weight=weight,
            parent_name=parent_name,
            max_interval_hours=max_interval_hours,
            length_multiplier=length_multiplier,
            min_duration_minutes=min_duration_minutes,
        )

        self.result = True
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()
