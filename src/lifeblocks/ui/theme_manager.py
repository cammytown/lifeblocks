from tkinter import ttk


class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.is_night_mode = True

    def toggle_theme(self):
        self.is_night_mode = not self.is_night_mode
        self.apply_theme()
        return self.is_night_mode

    def apply_theme(self):
        if self.is_night_mode:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        self._apply_common_styles()
        self.root.update_idletasks()

    def _apply_dark_theme(self):
        self.root.configure(bg="#1A1625")
        style = ttk.Style()

        # Base styles
        style.configure(".", background="#1A1625", foreground="#E8E6F0")
        style.configure("TLabel", background="#1A1625", foreground="#E8E6F0")
        style.configure("TButton", background="#2D2438", foreground="#E8E6F0")
        style.configure("Secondary.TButton", background="#342B42", foreground="#E8E6F0")
        style.configure("TEntry", fieldbackground="#2D2438", foreground="#E8E6F0")
        style.configure("TFrame", background="#1A1625")
        style.configure("Card.TFrame", background="#241E2E")
        style.configure("TLabelframe", background="#1A1625")
        style.configure("TLabelframe.Label", background="#1A1625", foreground="#E8E6F0")
        style.configure("TCheckbutton", background="#1A1625", foreground="#E8E6F0")
        style.configure("TCombobox", fieldbackground="#2D2438", foreground="#E8E6F0")
        style.configure("TRadiobutton", background="#1A1625", foreground="#E8E6F0")

        # Checkbutton state mapping
        style.map(
            "TCheckbutton",
            background=[("active", "#1A1625")],
            foreground=[("active", "#E8E6F0")],
            indicatorcolor=[
                ("selected", "#7768E5"),
                ("!selected", "#2D2438"),
                ("disabled", "#342B42"),
            ],
        )

        # Configure Treeview with grid lines and proper spacing
        self._configure_treeview(
            bg="#2D2438",
            fg="#E8E6F0",
            selectbg="#443856",
            selectfg="#FFFFFF",
            headerbg="#342B42",
            headerfg="#E8E6F0",
            headeractivebg="#443856",
            gridcolor="#342B42",
        )

        # Dialog styling
        style.configure("Toplevel", background="#1A1625")
        self.root.option_add("*Toplevel.background", "#1A1625")
        self.root.option_add("*Dialog.background", "#1A1625")
        self.root.option_add("*Entry.background", "#2D2438")
        self.root.option_add("*Entry.foreground", "#E8E6F0")

        self.root.option_add("*TCombobox*Listbox.background", "#2D2438")
        self.root.option_add("*TCombobox*Listbox.foreground", "#E8E6F0")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#443856")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#2D2438")],
            selectbackground=[("readonly", "#443856")],
            selectforeground=[("readonly", "#FFFFFF")],
        )

        style.map(
            "TRadiobutton",
            background=[("active", "#1A1625")],
            foreground=[("active", "#E8E6F0")],
        )

        # Button hover states
        style.map(
            "TButton",
            background=[
                ("active", "#443856"),  # Normal hover purple
                ("disabled", "#1A1822")  # Very dark purple for disabled
            ],
            foreground=[
                ("active", "#FFFFFF"),  # White text on hover
                ("disabled", "#444444")  # Dark gray for disabled text
            ],
        )

        # Secondary button hover states
        style.map(
            "Secondary.TButton",
            background=[
                ("active", "#443856"),  # Normal hover purple
                ("disabled", "#1A1822")  # Very dark purple for disabled
            ],
            foreground=[
                ("active", "#FFFFFF"),  # White text on hover
                ("disabled", "#444444")  # Dark gray for disabled text
            ],
        )

    def _apply_light_theme(self):
        self.root.configure(bg="#F5F3F7")
        style = ttk.Style()

        # Base styles
        style.configure(".", background="#F5F3F7", foreground="#2D2438")
        style.configure("TLabel", background="#F5F3F7", foreground="#2D2438")
        style.configure("TButton", background="#E8E6F0", foreground="#2D2438")
        style.configure("Secondary.TButton", background="#F0EDF4", foreground="#2D2438")
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#2D2438")
        style.configure("TFrame", background="#F5F3F7")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("TLabelframe", background="#F5F3F7")
        style.configure("TLabelframe.Label", background="#F5F3F7", foreground="#2D2438")
        style.configure("TCheckbutton", background="#F5F3F7", foreground="#2D2438")
        style.configure("TCombobox", fieldbackground="#FFFFFF", foreground="#2D2438")
        style.configure("TRadiobutton", background="#F5F3F7", foreground="#2D2438")

        # Checkbutton state mapping
        style.map(
            "TCheckbutton",
            background=[("active", "#F5F3F7")],
            foreground=[("active", "#2D2438")],
            indicatorcolor=[
                ("selected", "#7768E5"),
                ("!selected", "#FFFFFF"),
                ("disabled", "#F0EDF4"),
            ],
        )

        # Configure Treeview with grid lines and proper spacing
        self._configure_treeview(
            bg="#FFFFFF",
            fg="#2D2438",
            selectbg="#E8E6F0",
            selectfg="#2D2438",
            headerbg="#E8E6F0",
            headerfg="#2D2438",
            headeractivebg="#D8D4E3",
            gridcolor="#F0EDF4",
        )

        # Dialog styling
        style.configure("Toplevel", background="#F5F3F7")
        self.root.option_add("*Toplevel.background", "#F5F3F7")
        self.root.option_add("*Dialog.background", "#F5F3F7")
        self.root.option_add("*Entry.background", "#FFFFFF")
        self.root.option_add("*Entry.foreground", "#2D2438")

        self.root.option_add("*TCombobox*Listbox.background", "#E8E6F0")
        self.root.option_add("*TCombobox*Listbox.foreground", "#2D2438")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#E8E6F0")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#2D2438")

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            selectbackground=[("readonly", "#E8E6F0")],
            selectforeground=[("readonly", "#000000")],
        )

        style.map(
            "TRadiobutton",
            background=[("active", "#F5F3F7")],
            foreground=[("active", "#2D2438")],
        )

        # Button hover states
        style.map(
            "TButton",
            background=[
                ("active", "#D8D4E3"),  # Normal light hover
                ("disabled", "#CCCCCC")  # Light gray for disabled
            ],
            foreground=[
                ("active", "#2D2438"),  # Normal text on hover
                ("disabled", "#888888")  # Medium gray for disabled text
            ],
        )

        # Secondary button hover states
        style.map(
            "Secondary.TButton",
            background=[
                ("active", "#E8E6F0"),  # Normal light hover
                ("disabled", "#CCCCCC")  # Light gray for disabled
            ],
            foreground=[
                ("active", "#2D2438"),  # Normal text on hover
                ("disabled", "#888888")  # Medium gray for disabled text
            ],
        )

    def _configure_treeview(
        self, bg, fg, selectbg, selectfg, headerbg, headerfg, headeractivebg, gridcolor
    ):
        style = ttk.Style()

        # Main Treeview settings
        style.configure(
            "Treeview",
            background=bg,
            foreground=fg,
            fieldbackground=bg,
            selectbackground=selectbg,
            selectforeground=selectfg,
            rowheight=40,
            padding=(10, 5),
        )

        # Header settings
        style.configure(
            "Treeview.Heading",
            background=headerbg,
            foreground=headerfg,
            relief="flat",
            padding=(20, 10),
        )

        # Active states
        style.map("Treeview.Heading", background=[("active", headeractivebg)])

        # Configure grid lines
        style.configure("Treeview", show="tree headings gridlines", gridcolor=gridcolor)

    def _apply_common_styles(self):
        style = ttk.Style()

        # Remove the duplicate button style mappings from here since they're now handled
        # in the individual theme methods
