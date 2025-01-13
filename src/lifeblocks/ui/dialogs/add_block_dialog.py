import tkinter as tk
from tkinter import ttk, messagebox
from .block_dialog import BlockDialog


class AddBlockDialog(BlockDialog):
    def __init__(self, parent, block_service, selected_block_name=None):
        self.selected_block_name = selected_block_name
        super().__init__(parent, block_service, "Add Block")

        # Set default weight
        self.weight_entry.insert(0, "1")

        # Set up parent combo
        self.parent_combo["values"] = ["None"] + [
            p.name for p in self.block_service.get_all_blocks()
        ]
        self.parent_combo.set(
            self.selected_block_name if self.selected_block_name else "None"
        )

        parent.wait_window(self.dialog)

    def get_action_button_text(self):
        return "Add"

    def save(self):
        values = self.validate_input()
        if values is None:
            return

        self.block_service.add_block(
            values["name"],
            values["weight"],
            values["parent_name"],
            max_interval_hours=values["max_interval_hours"],
            length_multiplier=values["length_multiplier"],
            min_duration_minutes=values["min_duration_minutes"],
        )
        self.result = True
        self.dialog.destroy()
