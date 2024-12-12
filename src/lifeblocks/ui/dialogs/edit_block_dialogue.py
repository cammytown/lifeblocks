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
        self.dialog.grab_set()

        # Center dialog on parent
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200 // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - 150 // 2
        self.dialog.geometry(f"200x150+{x}+{y}")

        self.setup_ui()

        # Wait for dialog to close
        parent.wait_window(self.dialog)

    def setup_ui(self):
        # Name Entry
        ttk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(self.dialog)
        self.name_entry.insert(0, self.block.name)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Weight Entry
        ttk.Label(self.dialog, text="Weight:").grid(row=1, column=0, padx=5, pady=5)
        self.weight_entry = ttk.Entry(self.dialog)
        self.weight_entry.insert(0, str(self.block.weight))
        self.weight_entry.grid(row=1, column=1, padx=5, pady=5)

        # Max Interval Entry
        ttk.Label(self.dialog, text="Max Interval (hours):").grid(
            row=2, column=0, padx=5, pady=5
        )
        self.interval_entry = ttk.Entry(self.dialog)
        if self.block.max_interval_hours is not None:
            self.interval_entry.insert(0, str(self.block.max_interval_hours))
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5)

        # Parent Combobox
        ttk.Label(self.dialog, text="Parent:").grid(row=3, column=0, padx=5, pady=5)
        self.parent_combo = ttk.Combobox(self.dialog, state="readonly")

        # Get all possible parents (excluding self and children)
        all_blocks = self.block_service.get_all_blocks()
        invalid_parents = self._get_invalid_parents(all_blocks, self.block.id)
        valid_parents = ["None"] + [
            p.name for p in all_blocks if p.id not in invalid_parents
        ]

        self.parent_combo["values"] = valid_parents
        current_parent = "None" if not self.block.parent else self.block.parent.name
        self.parent_combo.set(current_parent)
        self.parent_combo.grid(row=3, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=self.save).pack(
            side=tk.LEFT, padx=5
        )
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

        parent_name = self.parent_combo.get()

        self.block_service.update_block(
            self.block.id,
            name=name,
            weight=weight,
            parent_name=parent_name,
            max_interval_hours=max_interval_hours,
        )

        self.result = True
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()
