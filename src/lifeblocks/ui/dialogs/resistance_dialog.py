import tkinter as tk
from tkinter import ttk


class ResistanceDialog:
    def __init__(self, parent, block_name):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Rate Resistance")
        self.dialog.transient(parent)
        self.dialog.resizable(False, False)

        main_frame = ttk.Frame(self.dialog, padding="20", style="Card.TFrame")
        main_frame.pack(fill="both", expand=True)

        # Block name
        ttk.Label(main_frame, text=f"Before starting work on:", style="TLabel").pack(
            pady=(0, 5)
        )
        ttk.Label(main_frame, text=block_name, font=("Helvetica", 12, "bold")).pack(
            pady=(0, 20)
        )

        # Resistance level description
        ttk.Label(main_frame, text="Rate your resistance level:", style="TLabel").pack(
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
                main_frame, text=level, value=level[0], variable=self.resistance_var
            ).pack(anchor="w", pady=2)

        # Buttons
        btn_frame = ttk.Frame(main_frame, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.dialog.destroy
        ).pack(side="right", padx=5)
        ttk.Button(
            btn_frame, text="Start", style="Accent.TButton", command=self._submit
        ).pack(side="right", padx=5)

        # Wait for the window to be visible and sized
        self.dialog.update_idletasks()
        self.dialog.wait_visibility()

        # Get the size that fits the content
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        # Calculate position
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 3  # Position slightly above center

        # Set the final position and size
        self.dialog.geometry(f"+{x}+{y}")
        
        # Finally, set the grab
        self.dialog.grab_set()

    def _submit(self):
        if self.resistance_var.get():
            self.result = int(self.resistance_var.get())
            self.dialog.destroy()
