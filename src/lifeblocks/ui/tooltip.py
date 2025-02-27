import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Create a tooltip for a given widget with theme awareness and screen boundary detection."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)

    def schedule(self, event=None):
        self.id = self.widget.after(500, self.show)

    def show(self, event=None):
        # Get widget position
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        
        # Create tooltip window
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        
        # Determine if we're in dark mode by checking background color
        style = ttk.Style()
        bg_color = style.lookup("TFrame", "background")
        is_dark_mode = self._is_dark_color(bg_color)
        
        # Create a frame with appropriate styling based on theme
        if is_dark_mode:
            frame = ttk.Frame(tw, style="Card.TFrame", padding=2)
            label = ttk.Label(frame, text=self.text, background="#241E2E", foreground="#E8E6F0")
        else:
            frame = ttk.Frame(tw, style="Card.TFrame", padding=2)
            label = ttk.Label(frame, text=self.text, background="#FFFFFF", foreground="#2D2438")
        
        frame.pack(fill="both", expand=True)
        label.pack(padx=6, pady=4)
        
        # Update window size before positioning
        tw.update_idletasks()
        
        # Adjust position to ensure tooltip stays on screen
        tooltip_width = tw.winfo_width()
        tooltip_height = tw.winfo_height()
        screen_width = tw.winfo_screenwidth()
        screen_height = tw.winfo_screenheight()
        
        # Horizontal positioning
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10
        elif x - tooltip_width//2 < 0:
            x = 10
        else:
            x = x - tooltip_width//2  # Center horizontally
        
        # Vertical positioning - prefer below widget, but go above if no space below
        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() - tooltip_height - 5
        
        tw.wm_geometry(f"+{x}+{y}")

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
            
    def _is_dark_color(self, color_str):
        """Determine if a color is dark based on its string representation."""
        # Default to light mode if color isn't in hex format
        if not color_str or not color_str.startswith('#'):
            return False
            
        # Convert hex to RGB values
        r = int(color_str[1:3], 16)
        g = int(color_str[3:5], 16)
        b = int(color_str[5:7], 16)
        
        # Calculate perceived brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        
        # If brightness < 128, it's a dark color
        return brightness < 128 