import tkinter as tk
from tkinter import ttk

class BaseDialog:
    def __init__(self, parent, title, y_offset=0):
        self.result = None
        self.parent = parent
        self.y_offset = y_offset

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)

        # Create main frame with padding
        self.main_frame = ttk.Frame(self.dialog, padding="20", style="Card.TFrame")
        self.main_frame.pack(fill="both", expand=True)

        # Let child classes set up their UI
        self.setup_ui()

        # After UI is set up, prevent resizing smaller than needed
        self.dialog.update_idletasks()
        self.dialog.minsize(self.dialog.winfo_width(), self.dialog.winfo_height())

        # Center the dialog
        self._center_dialog()

        # Wait for the window to be visible before grabbing
        self.dialog.wait_visibility()
        self.dialog.grab_set()

    def _center_dialog(self):
        """Center the dialog relative to its parent window."""
        x = self.parent.winfo_rootx() + self.parent.winfo_width() // 2 - self.dialog.winfo_width() // 2
        y = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - self.dialog.winfo_height() // 2 + self.y_offset
        self.dialog.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Override this method in child classes to set up the dialog's UI."""
        pass

    def destroy(self):
        """Destroy the dialog."""
        self.dialog.destroy() 