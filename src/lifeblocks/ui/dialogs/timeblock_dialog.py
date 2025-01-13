import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from lifeblocks.models.timeblock import TimeBlockState
from lifeblocks.models.block import Block
from .base_dialog import BaseDialog

class TimeBlockDialog(BaseDialog):
    def __init__(self, parent, session, title):
        self.session = session
        super().__init__(parent, title)
        
        # Wait for the dialog to close
        parent.wait_window(self.dialog)

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Block Selection
        ttk.Label(main_frame, text="Block:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.block_var = tk.StringVar()
        blocks = self.session.query(Block).order_by(Block.name).all()
        self.block_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.block_var,
            values=[block.name for block in blocks],
            width=30,
            state="readonly"
        )
        self.block_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.setup_block_selection()

        # Start Time
        ttk.Label(main_frame, text="Start Time:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.start_time_frame = ttk.Frame(main_frame)
        self.start_time_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Date entry
        self.date_entry = ttk.Entry(self.start_time_frame, width=10)
        self.date_entry.pack(side="left", padx=(0, 5))
        
        # Time entry
        self.time_entry = ttk.Entry(self.start_time_frame, width=8)
        self.time_entry.pack(side="left")
        
        self.setup_datetime_fields()

        # Duration Entry
        ttk.Label(main_frame, text="Duration (minutes):").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.duration_entry = ttk.Entry(main_frame, width=10)
        self.duration_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.setup_duration()

        # Resistance Level
        ttk.Label(main_frame, text="Resistance Level:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        self.resistance_var = tk.StringVar()
        resistance_values = [""] + [str(i) for i in range(1, 6)]  # Empty or 1-5
        self.resistance_combo = ttk.Combobox(
            main_frame, textvariable=self.resistance_var, values=resistance_values, width=8, state="readonly"
        )
        self.resistance_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.setup_resistance()

        # Satisfaction Level
        ttk.Label(main_frame, text="Satisfaction Level:").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        self.satisfaction_var = tk.StringVar()
        satisfaction_values = [""] + [str(i) for i in range(1, 6)]  # Empty or 1-5
        self.satisfaction_combo = ttk.Combobox(
            main_frame, textvariable=self.satisfaction_var, values=satisfaction_values, width=8, state="readonly"
        )
        self.satisfaction_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.setup_satisfaction()

        # Notes
        ttk.Label(main_frame, text="Notes:").grid(
            row=5, column=0, padx=5, pady=5, sticky="ne"
        )
        self.notes_text = tk.Text(main_frame, width=30, height=4)
        self.notes_text.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.setup_notes()

        # State
        ttk.Label(main_frame, text="State:").grid(
            row=6, column=0, padx=5, pady=5, sticky="e"
        )
        self.state_var = tk.StringVar(value=TimeBlockState.COMPLETED.value)
        state_values = [state.value for state in TimeBlockState]
        self.state_combo = ttk.Combobox(
            main_frame, textvariable=self.state_var, values=state_values, width=15, state="readonly"
        )
        self.state_combo.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        self.setup_state()

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text=self.get_action_button_text(),
            style="Primary.TButton",
            command=self.save
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.dialog.destroy
        ).pack(side="left", padx=5)

    def setup_block_selection(self):
        """Override in subclasses to set initial block selection"""
        pass

    def setup_datetime_fields(self):
        """Override in subclasses to set initial datetime values"""
        now = datetime.now()
        self.date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, now.strftime("%H:%M"))

    def setup_duration(self):
        """Override in subclasses to set initial duration"""
        pass

    def setup_resistance(self):
        """Override in subclasses to set initial resistance"""
        pass

    def setup_satisfaction(self):
        """Override in subclasses to set initial satisfaction"""
        pass

    def setup_notes(self):
        """Override in subclasses to set initial notes"""
        pass

    def setup_state(self):
        """Override in subclasses to set initial state"""
        pass

    def get_action_button_text(self):
        """Override in subclasses to set the action button text"""
        return "Save"

    def validate_input(self):
        """Validate all input fields and return a dict of values if valid"""
        try:
            # Validate block
            block_name = self.block_var.get()
            if not block_name:
                raise ValueError("Please select a block")
            block = self.session.query(Block).filter_by(name=block_name).first()
            if not block:
                raise ValueError("Selected block not found")

            # Validate datetime
            try:
                date_str = self.date_entry.get()
                time_str = self.time_entry.get()
                start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("Invalid date/time format. Use YYYY-MM-DD HH:MM")

            # Validate duration
            try:
                duration = float(self.duration_entry.get())
                if duration <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("Duration must be a positive number")

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

            return {
                "block": block,
                "start_time": start_time,
                "duration": duration,
                "resistance_level": resistance_level,
                "satisfaction_level": satisfaction_level,
                "notes": notes,
                "state": state
            }

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return None

    def save(self):
        """Override in subclasses to implement save functionality"""
        pass 