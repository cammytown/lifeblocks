import tkinter as tk
from tkinter import ttk, messagebox


class BlockDialog:
    def __init__(self, parent, block_service, title):
        self.result = False
        self.block_service = block_service
        self.parent = parent

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)

        # Center dialog
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - 100
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui()

        # After UI is set up, prevent resizing smaller than needed
        self.dialog.update_idletasks()
        self.dialog.minsize(self.dialog.winfo_width(), self.dialog.winfo_height())

        # Bind return key to save
        self.name_entry.bind("<Return>", lambda event: self.save())

        # Wait for the window to be visible before grabbing
        self.dialog.wait_visibility()
        self.dialog.grab_set()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Name Entry
        ttk.Label(main_frame, text="Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Weight Entry
        ttk.Label(main_frame, text="Weight:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.weight_entry = ttk.Entry(main_frame, width=10)
        self.weight_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Max Interval Entry
        ttk.Label(main_frame, text="Max Interval (hours):").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.interval_entry = ttk.Entry(main_frame, width=10)
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Length Multiplier Entry
        ttk.Label(main_frame, text="Length Multiplier:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        self.length_multiplier_entry = ttk.Entry(main_frame, width=10)
        self.length_multiplier_entry.insert(0, "1.0")
        self.length_multiplier_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Min Duration Entry
        ttk.Label(main_frame, text="Min Duration (minutes):").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        self.min_duration_entry = ttk.Entry(main_frame, width=10)
        self.min_duration_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Parent Selection
        ttk.Label(main_frame, text="Parent:").grid(
            row=5, column=0, padx=5, pady=5, sticky="e"
        )
        self.parent_combo = ttk.Combobox(main_frame, state="readonly", width=28)
        self.parent_combo.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Configure grid column weights
        main_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text=self.get_action_button_text(),
            style="Accent.TButton",
            command=self.save,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(
            side=tk.LEFT, padx=5
        )

    def get_action_button_text(self):
        return "Save"

    def validate_input(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Block name cannot be empty!")
            return None

        try:
            weight = int(self.weight_entry.get())
            if weight < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Weight must be a positive integer!")
            return None

        # Parse max interval
        max_interval_hours = None
        interval_text = self.interval_entry.get().strip()
        if interval_text:
            try:
                max_interval_hours = float(interval_text)
                if max_interval_hours < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", "Max interval must be a positive number or empty!"
                )
                return None

        # Parse length multiplier
        try:
            length_multiplier = float(self.length_multiplier_entry.get())
            if length_multiplier <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "Length multiplier must be a positive number!"
            )
            return None

        # Parse min duration
        min_duration_minutes = None
        min_duration_text = self.min_duration_entry.get().strip()
        if min_duration_text:
            try:
                min_duration_minutes = float(min_duration_text)
                if min_duration_minutes < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", "Minimum duration must be a positive number or empty!"
                )
                return None

        return {
            "name": name,
            "weight": weight,
            "max_interval_hours": max_interval_hours,
            "parent_name": self.parent_combo.get(),
            "length_multiplier": length_multiplier,
            "min_duration_minutes": min_duration_minutes,
        }

    def save(self):
        pass

    def cancel(self):
        self.dialog.destroy()
