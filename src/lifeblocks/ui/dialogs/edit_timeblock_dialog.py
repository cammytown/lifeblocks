import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from lifeblocks.models.timeblock import TimeBlockState
from .base_dialog import BaseDialog

class EditTimeBlockDialog(BaseDialog):
    def __init__(self, parent, session, timeblock):
        self.session = session
        self.timeblock = timeblock
        super().__init__(parent, "Edit Time Block")
        
        # Wait for the dialog to close
        parent.wait_window(self.dialog)

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Duration Entry
        ttk.Label(main_frame, text="Duration (minutes):").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.duration_entry = ttk.Entry(main_frame, width=10)
        self.duration_entry.insert(0, str(self.timeblock.duration_minutes))
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Resistance Level
        ttk.Label(main_frame, text="Resistance Level:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.resistance_var = tk.StringVar(value=str(self.timeblock.resistance_level or ""))
        resistance_values = [""] + [str(i) for i in range(1, 6)]  # Empty or 1-5
        self.resistance_combo = ttk.Combobox(
            main_frame, textvariable=self.resistance_var, values=resistance_values, width=8, state="readonly"
        )
        self.resistance_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Satisfaction Level
        ttk.Label(main_frame, text="Satisfaction Level:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.satisfaction_var = tk.StringVar(value=str(self.timeblock.satisfaction_level or ""))
        satisfaction_values = [""] + [str(i) for i in range(1, 6)]  # Empty or 1-5
        self.satisfaction_combo = ttk.Combobox(
            main_frame, textvariable=self.satisfaction_var, values=satisfaction_values, width=8, state="readonly"
        )
        self.satisfaction_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Notes
        ttk.Label(main_frame, text="Notes:").grid(
            row=3, column=0, padx=5, pady=5, sticky="ne"
        )
        self.notes_text = tk.Text(main_frame, width=30, height=4)
        if self.timeblock.notes:
            self.notes_text.insert("1.0", self.timeblock.notes)
        self.notes_text.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # State
        ttk.Label(main_frame, text="State:").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        self.state_var = tk.StringVar(value=self.timeblock.state.value)
        state_values = [state.value for state in TimeBlockState]
        self.state_combo = ttk.Combobox(
            main_frame, textvariable=self.state_var, values=state_values, width=15, state="readonly"
        )
        self.state_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="Save",
            style="Primary.TButton",
            command=self.save
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.dialog.destroy
        ).pack(side="left", padx=5)

    def save(self):
        try:
            duration = float(self.duration_entry.get())
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Duration must be a positive number!")
            return

        # Get resistance level (can be None)
        resistance = self.resistance_var.get()
        resistance_level = int(resistance) if resistance else None

        # Get satisfaction level (can be None)
        satisfaction = self.satisfaction_var.get()
        satisfaction_level = int(satisfaction) if satisfaction else None

        # Get notes
        notes = self.notes_text.get("1.0", "end-1c").strip()
        if not notes:
            notes = None

        # Get state
        state = TimeBlockState(self.state_var.get())

        # Update the timeblock
        self.timeblock.duration_minutes = duration
        self.timeblock.resistance_level = resistance_level
        self.timeblock.satisfaction_level = satisfaction_level
        self.timeblock.notes = notes
        self.timeblock.state = state

        self.session.commit()
        self.result = True
        self.dialog.destroy() 