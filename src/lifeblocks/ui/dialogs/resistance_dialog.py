import tkinter as tk
from tkinter import ttk
from .base_dialog import BaseDialog
from lifeblocks.models.timeblock import PickReason


class DelayDialog(BaseDialog):
    def __init__(self, parent, block_name):
        self.block_name = block_name
        self.result = None
        super().__init__(parent, "Delay Block", y_offset=100)

    def setup_ui(self):
        # Block name
        ttk.Label(self.main_frame, text=f"Delay block:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(self.main_frame, text=self.block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 20)
        )

        # Delay duration input
        delay_frame = ttk.Frame(self.main_frame)
        delay_frame.pack(pady=(0, 20))
        ttk.Label(delay_frame, text="Delay for:").pack(side="left", padx=(0, 5))
        
        self.delay_var = tk.StringVar(value="4")
        delay_spinbox = ttk.Spinbox(
            delay_frame,
            from_=1,
            to=24,
            width=3,
            textvariable=self.delay_var
        )
        delay_spinbox.pack(side="left", padx=(0, 5))
        ttk.Label(delay_frame, text="hours").pack(side="left")

        # Buttons
        btn_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.destroy,
        ).pack(side="right", padx=5)

        ttk.Button(
            btn_frame,
            text="Delay",
            style="Accent.TButton",
            command=self._submit,
        ).pack(side="right", padx=5)

    def _submit(self):
        try:
            delay_hours = int(self.delay_var.get())
            if 1 <= delay_hours <= 24:
                self.result = delay_hours
                self.destroy()
        except ValueError:
            pass


class ResistanceDialog(BaseDialog):
    def __init__(self, parent, block_name, pick_reason=PickReason.NORMAL):
        self.block_name = block_name
        self.pick_reason = pick_reason
        super().__init__(parent, "Rate Resistance", y_offset=100)

    def setup_ui(self):
        # Block name
        ttk.Label(self.main_frame, text=f"Before starting work on:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(self.main_frame, text=self.block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 20)
        )

        # Show overdue notice if applicable
        if self.pick_reason == PickReason.OVERDUE:
            notice_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
            notice_frame.pack(fill="x", pady=(0, 20), padx=10)
            ttk.Label(
                notice_frame,
                text="⚠️ This block is overdue",
                font=("Helvetica", 10, "italic"),
                foreground="#E67E22"  # Orange color for emphasis
            ).pack(pady=10)

        # Resistance level description
        ttk.Label(self.main_frame, text="Rate your resistance level:", style="TLabel").pack(
            pady=(0, 10)
        )

        levels = [
            "1 - Eager to begin",
            "2 - Ready to engage",
            "3 - Ambivalent",
            "4 - Strong resistance",
            "5 - Severe aversion",
        ]

        self.resistance_var = tk.StringVar()
        for level in levels:
            ttk.Radiobutton(
                self.main_frame, text=level, value=level[0], variable=self.resistance_var
            ).pack(anchor="w", pady=2)

        # Buttons
        btn_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.destroy,
        ).pack(side="right", padx=5)

        # Add Delay button for overdue blocks
        if self.pick_reason == PickReason.OVERDUE:
            ttk.Button(
                btn_frame,
                text="Delay",
                style="Secondary.TButton",
                command=self._delay,
            ).pack(side="right", padx=5)

        ttk.Button(
            btn_frame, text="Start", style="Accent.TButton", command=self._submit
        ).pack(side="right", padx=5)

    def _delay(self):
        delay_dialog = DelayDialog(self.dialog.winfo_toplevel(), self.block_name)
        self.dialog.wait_window(delay_dialog.dialog)
        
        if delay_dialog.result:
            self.result = {"delayed": True, "delay_hours": delay_dialog.result}
            self.destroy()

    def _submit(self):
        if self.resistance_var.get():
            # Set a normal result with resistance level
            self.result = {"delayed": False, "resistance": int(self.resistance_var.get())}
            self.destroy()
