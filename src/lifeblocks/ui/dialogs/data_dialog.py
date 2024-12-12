import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class DataDialog:
    def __init__(self, parent, data_service):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import/Export Data")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.data_service = data_service
        self.setup_ui()

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

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Export section
        export_frame = ttk.LabelFrame(main_frame, text="Export Data", padding="10")
        export_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            export_frame, text="Save your data to a file for backup or transfer."
        ).pack(pady=(0, 10))
        ttk.Button(
            export_frame,
            text="Export Data",
            command=self.export_data,
            style="Accent.TButton",
        ).pack()

        # Import section
        import_frame = ttk.LabelFrame(main_frame, text="Import Data", padding="10")
        import_frame.pack(fill="x")

        ttk.Label(
            import_frame, text="Warning: Importing data will replace your current data."
        ).pack(pady=(0, 10))
        ttk.Button(
            import_frame,
            text="Import Data",
            command=self.import_data,
            style="Secondary.TButton",
        ).pack()

        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(
            pady=(20, 0)
        )

    def export_data(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Data",
        )
        if filename:
            try:
                self.data_service.export_to_file(filename)
                messagebox.showinfo("Success", "Data exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def import_data(self):
        if not messagebox.askyesno(
            "Confirm Import",
            "Importing data will replace your current data. Are you sure?",
        ):
            return

        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Data",
        )
        if filename:
            try:
                messages = self.data_service.import_from_file(filename)
                messagebox.showinfo("Success", "\n".join(messages))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import data: {str(e)}")
