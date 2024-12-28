import tkinter as tk
from tkinter import ttk, messagebox
from .base_dialog import BaseDialog
import time


class CompletionDialog(BaseDialog):
    def __init__(self, parent, block_name, elapsed_minutes):
        self.block_name = block_name
        self.elapsed_minutes = elapsed_minutes
        self.overflow_start = time.time()
        self.after_id = None
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

        # Overflow timer frame
        overflow_frame = ttk.Frame(self.main_frame)
        overflow_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(overflow_frame, text="Overflow time:", style="TLabel").pack(side="left")
        self.overflow_label = ttk.Label(overflow_frame, text="0:00", style="TLabel")
        self.overflow_label.pack(side="left", padx=5)
        
        self.include_overflow = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            overflow_frame,
            text="Include overflow time",
            variable=self.include_overflow
        ).pack(side="right")

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

        # Start overflow timer update
        self._update_overflow_timer()

    def _update_overflow_timer(self):
        overflow_seconds = int(time.time() - self.overflow_start)
        minutes = overflow_seconds // 60
        seconds = overflow_seconds % 60
        self.overflow_label.configure(text=f"{minutes}:{seconds:02d}")
        self.after_id = self.dialog.after(1000, self._update_overflow_timer)

    def _save(self):
        if not self.satisfaction_var.get():
            messagebox.showwarning(
                "Missing Rating",
                "Please rate your satisfaction with the session before saving."
            )
            return

        # Calculate total elapsed time if overflow is included
        total_elapsed = self.elapsed_minutes
        if self.include_overflow.get():
            overflow_minutes = (time.time() - self.overflow_start) / 60
            total_elapsed += overflow_minutes

        self.result = {
            "save": True,
            "satisfaction": int(self.satisfaction_var.get()),
            "notes": self.notes_text.get("1.0", "end-1c"),
            "total_elapsed": total_elapsed
        }
        if self.after_id:
            self.dialog.after_cancel(self.after_id)
        self.destroy()

    def _cancel(self):
        response = messagebox.askyesno(
            "Cancel TimeBlock",
            "Are you sure you want to cancel this timeblock?\nIt will be marked as cancelled and not saved to history.",
            icon="warning"
        )
        if response:
            self.result = {"save": False}
            if self.after_id:
                self.dialog.after_cancel(self.after_id)
            self.destroy()
