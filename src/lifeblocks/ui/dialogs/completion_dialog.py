import tkinter as tk
from tkinter import ttk, messagebox


class CompletionDialog:
    def __init__(self, parent, block_name, elapsed_minutes):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Session Complete")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="20", style="Card.TFrame")
        main_frame.pack(fill="both", expand=True)

        # Block info
        ttk.Label(main_frame, text=f"Completed work on:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(main_frame, text=block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 5)
        )
        ttk.Label(
            main_frame, text=f"Duration: {elapsed_minutes:.1f} minutes", style="TLabel"
        ).pack(pady=(0, 20))

        # Satisfaction rating
        ttk.Label(main_frame, text="Rate your satisfaction:", style="TLabel").pack(
            pady=(0, 10)
        )

        self.satisfaction_var = tk.StringVar()
        satisfaction_frame = ttk.Frame(main_frame)
        satisfaction_frame.pack(fill="x", pady=(0, 20))

        for i in range(1, 6):
            ttk.Radiobutton(
                satisfaction_frame,
                text=str(i),
                value=str(i),
                variable=self.satisfaction_var,
            ).pack(side="left", padx=10)

        # Notes
        ttk.Label(main_frame, text="Session notes:", style="TLabel").pack(
            anchor="w", pady=(0, 5)
        )
        self.notes_text = tk.Text(main_frame, height=4, width=40)
        self.notes_text.pack(fill="x", pady=(0, 20))

        # Buttons
        btn_frame = ttk.Frame(main_frame, style="Card.TFrame")
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

        # Center dialog
        self.dialog.update_idletasks()
        x = (
            parent.winfo_rootx()
            + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        )
        y = (
            parent.winfo_rooty()
            + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        )
        self.dialog.geometry(f"+{x}+{y}")

    def _save(self):
        if not self.satisfaction_var.get():
            return

        self.result = {
            "save": True,
            "satisfaction": int(self.satisfaction_var.get()),
            "notes": self.notes_text.get("1.0", "end-1c"),
        }
        self.dialog.destroy()

    def _cancel(self):
        response = messagebox.askyesno(
            "Cancel TimeBlock",
            "Are you sure you want to cancel this timeblock?\nIt will be marked as cancelled and not saved to history.",
            icon="warning"
        )
        if response:
            self.result = {"save": False}
            self.dialog.destroy()
