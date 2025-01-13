import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from lifeblocks.models.timeblock import TimeBlockState
from .timeblock_dialog import TimeBlockDialog

class EditTimeBlockDialog(TimeBlockDialog):
    def __init__(self, parent, session, timeblock):
        self.timeblock = timeblock
        super().__init__(parent, session, "Edit Time Block")

    def setup_block_selection(self):
        self.block_combo.set(self.timeblock.block.name)
        self.block_combo.configure(state="disabled")  # Can't change block when editing

    def setup_datetime_fields(self):
        self.date_entry.insert(0, self.timeblock.start_time.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, self.timeblock.start_time.strftime("%H:%M"))

    def setup_duration(self):
        self.duration_entry.insert(0, str(self.timeblock.duration_minutes))

    def setup_resistance(self):
        self.resistance_var.set(str(self.timeblock.resistance_level or ""))

    def setup_satisfaction(self):
        self.satisfaction_var.set(str(self.timeblock.satisfaction_level or ""))

    def setup_notes(self):
        if self.timeblock.notes:
            self.notes_text.insert("1.0", self.timeblock.notes)

    def setup_state(self):
        self.state_var.set(self.timeblock.state.value)

    def get_action_button_text(self):
        return "Save"

    def save(self):
        values = self.validate_input()
        if values is None:
            return

        # Update the timeblock
        self.timeblock.start_time = values["start_time"]
        self.timeblock.duration_minutes = values["duration"]
        self.timeblock.resistance_level = values["resistance_level"]
        self.timeblock.satisfaction_level = values["satisfaction_level"]
        self.timeblock.notes = values["notes"]
        self.timeblock.state = values["state"]

        self.session.commit()
        self.result = True
        self.dialog.destroy() 