import tkinter as tk
from tkinter import ttk, messagebox
from .block_dialog import BlockDialog


class EditBlockDialog(BlockDialog):
    def __init__(self, parent, block_service, block_id):
        self.block_id = block_id
        self.block = next(
            (p for p in block_service.get_all_blocks() if p.id == block_id), None
        )

        if not self.block:
            messagebox.showerror("Error", "Block not found!")
            return

        super().__init__(parent, block_service, "Edit Block")

        # Set existing values
        self.name_entry.insert(0, self.block.name)
        self.weight_entry.insert(0, str(self.block.weight))
        if self.block.max_interval_hours is not None:
            self.interval_entry.insert(0, str(self.block.max_interval_hours))
        self.length_multiplier_entry.delete(0, tk.END)  # Clear default value
        self.length_multiplier_entry.insert(0, str(self.block.length_multiplier))
        if self.block.min_duration_minutes is not None:
            self.min_duration_entry.insert(0, str(self.block.min_duration_minutes))

        # Set up parent combo with valid parents
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

        parent.wait_window(self.dialog)

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

    def get_action_button_text(self):
        return "Save"

    def save(self):
        values = self.validate_input()
        if values is None:
            return

        self.block_service.update_block(
            self.block.id,
            name=values["name"],
            weight=values["weight"],
            parent_name=values["parent_name"],
            max_interval_hours=values["max_interval_hours"],
            length_multiplier=values["length_multiplier"],
            min_duration_minutes=values["min_duration_minutes"],
        )

        self.result = True
        self.dialog.destroy()
