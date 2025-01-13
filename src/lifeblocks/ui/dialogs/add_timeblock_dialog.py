import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from lifeblocks.models.timeblock import TimeBlock, TimeBlockState, PickReason
from .timeblock_dialog import TimeBlockDialog

class AddTimeBlockDialog(TimeBlockDialog):
    def __init__(self, parent, session):
        super().__init__(parent, session, "Add Time Block")

    def setup_block_selection(self):
        if self.block_combo["values"]:
            self.block_combo.set(self.block_combo["values"][0])

    def setup_duration(self):
        self.duration_entry.insert(0, "25")  # Default to 25 minutes

    def setup_state(self):
        self.state_var.set(TimeBlockState.COMPLETED.value)  # Default to completed for manual entries

    def get_action_button_text(self):
        return "Add"

    def save(self):
        values = self.validate_input()
        if values is None:
            return

        # Create new timeblock
        timeblock = TimeBlock(
            block_id=values["block"].id,
            start_time=values["start_time"],
            duration_minutes=values["duration"],
            resistance_level=values["resistance_level"],
            satisfaction_level=values["satisfaction_level"],
            notes=values["notes"],
            state=values["state"],
            forced=True,  # Mark as forced since it's manually added
            pick_reason=PickReason.FORCED
        )

        # Update the block's last_picked time if this is the most recent timeblock
        if values["start_time"] > (values["block"].last_picked or datetime.min):
            values["block"].last_picked = values["start_time"]

        self.session.add(timeblock)
        self.session.commit()
        self.result = True
        self.dialog.destroy() 