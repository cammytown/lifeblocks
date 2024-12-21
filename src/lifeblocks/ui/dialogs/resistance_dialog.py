import tkinter as tk
from tkinter import ttk
from .base_dialog import BaseDialog


class ResistanceDialog(BaseDialog):
    def __init__(self, parent, block_name):
        self.block_name = block_name
        super().__init__(parent, "Rate Resistance", y_offset=100)

    def setup_ui(self):
        # Block name
        ttk.Label(self.main_frame, text=f"Before starting work on:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(self.main_frame, text=self.block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 20)
        )

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
        ttk.Button(
            btn_frame, text="Start", style="Accent.TButton", command=self._submit
        ).pack(side="right", padx=5)

    def _submit(self):
        if self.resistance_var.get():
            self.result = int(self.resistance_var.get())
            self.destroy()
