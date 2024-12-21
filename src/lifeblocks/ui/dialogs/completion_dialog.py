import tkinter as tk
from tkinter import ttk, messagebox
from .base_dialog import BaseDialog


class CompletionDialog(BaseDialog):
    def __init__(self, parent, block_name, elapsed_minutes):
        self.block_name = block_name
        self.elapsed_minutes = elapsed_minutes
        super().__init__(parent, "Session Complete", y_offset=100)

    def setup_ui(self):
        # Block info
        ttk.Label(self.main_frame, text=f"Completed work on:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(self.main_frame, text=self.block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 5)
        )
        ttk.Label(
            self.main_frame, text=f"Duration: {self.elapsed_minutes:.1f} minutes", style="TLabel"
        ).pack(pady=(0, 20))

        # Satisfaction rating
        ttk.Label(self.main_frame, text="Rate your satisfaction:", style="TLabel").pack(
            pady=(0, 10)
        )

        self.satisfaction_var = tk.StringVar()
        satisfaction_frame = ttk.Frame(self.main_frame)
        satisfaction_frame.pack(fill="x", pady=(0, 20))

        for i in range(1, 6):
            ttk.Radiobutton(
                satisfaction_frame,
                text=str(i),
                value=str(i),
                variable=self.satisfaction_var,
            ).pack(side="left", padx=10)

        # Notes
        ttk.Label(self.main_frame, text="Session notes:", style="TLabel").pack(
            anchor="w", pady=(0, 5)
        )
        self.notes_text = tk.Text(self.main_frame, height=4, width=40)
        self.notes_text.pack(fill="x", pady=(0, 20))

        # Buttons
        btn_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self._cancel
        ).pack(side="right", padx=5)

        ttk.Button(
            btn_frame, text="Save", style="Accent.TButton", command=self._save
        ).pack(side="right", padx=5)

    def _save(self):
        if not self.satisfaction_var.get():
            return

        self.result = {
            "save": True,
            "satisfaction": int(self.satisfaction_var.get()),
            "notes": self.notes_text.get("1.0", "end-1c"),
        }
        self.destroy()

    def _cancel(self):
        response = messagebox.askyesno(
            "Cancel TimeBlock",
            "Are you sure you want to cancel this timeblock?\nIt will be marked as cancelled and not saved to history.",
            icon="warning"
        )
        if response:
            self.result = {"save": False}
            self.destroy()
