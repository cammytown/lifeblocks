import tkinter as tk
from tkinter import ttk
from .theme_manager import ThemeManager
from .block_frame import BlockFrame
from .history_frame import HistoryFrame
from .timer_frame import TimerFrame
from .dialogs.data_dialog import DataDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.hotkeys_dialog import HotkeysDialog
from lifeblocks.services.block_service import BlockService
from lifeblocks.services.timer_service import TimerService
from lifeblocks.services.notification_service import NotificationService
from lifeblocks.services.settings_service import SettingsService
from lifeblocks.services.data_service import DataService


class MainWindow:
    def __init__(self, session):
        self.root = tk.Tk()
        self.root.title("LifeBlocks")
        self.root.minsize(800, 800)

        # Initialize services
        self.settings_service = SettingsService(session)
        self.block_service = BlockService(session, self.settings_service)
        self.timer_service = TimerService(session, self.settings_service)
        self.notification_service = NotificationService(self.settings_service)
        self.data_service = DataService(session)

        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)

        # Setup main container with padding
        self.main_container = ttk.Frame(self.root, padding="20")
        self.main_container.grid(row=0, column=0, sticky="nsew")

        # Configure root window grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Top right buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.place(relx=1.0, x=-20, y=20, anchor="ne")

        # Settings button
        settings_button = ttk.Button(
            buttons_frame,
            text="⚙️",
            width=2,
            command=self.show_settings_dialog,
            style="Small.TButton",
        )
        settings_button.pack(side=tk.LEFT, padx=(0, 5))

        # Import/Export button
        data_button = ttk.Button(
            buttons_frame,
            text="💾",
            width=2,
            command=self.show_data_dialog,
            style="Small.TButton",
        )
        data_button.pack(side=tk.LEFT, padx=(0, 5))

        # Hotkeys button
        hotkeys_button = ttk.Button(
            buttons_frame,
            text="⌨️",
            width=2,
            command=self.show_hotkeys_dialog,
            style="Small.TButton",
        )
        hotkeys_button.pack(side=tk.LEFT, padx=(0, 5))

        # Theme toggle button
        theme_button = ttk.Button(
            buttons_frame,
            text="🌙",
            width=2,
            command=self.theme_manager.toggle_theme,
            style="Small.TButton",
        )
        theme_button.pack(side=tk.LEFT)

        # Configure grid weights for vertical expansion
        self.main_container.grid_rowconfigure(1, weight=6)  # Blocks section (60%)
        self.main_container.grid_rowconfigure(2, weight=4)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create frames
        self.history_frame = HistoryFrame(self.main_container, session)
        self.timer_frame = TimerFrame(
            self.main_container,
            self.timer_service,
            self.block_service,
            self.notification_service,
            self.history_frame,
        )
        self.block_frame = BlockFrame(self.main_container, self.block_service, self.timer_frame)

        # Timer at the top
        self.timer_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # Blocks section (60% of space)
        self.block_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))

        # History section (40% of space)
        self.history_frame.grid(row=2, column=0, sticky="nsew")

        # Set up hotkey bindings
        self.setup_hotkeys()

        # Apply initial theme
        self.theme_manager.apply_theme()

    def show_settings_dialog(self):
        SettingsDialog(self.root, self.settings_service)

    def show_data_dialog(self):
        DataDialog(self.root, self.data_service)

    def show_hotkeys_dialog(self):
        HotkeysDialog(self.root, self.settings_service)

    def setup_hotkeys(self):
        def handle_hotkey(event):
            # Convert event state and keysym to our hotkey format
            parts = []
            if event.state & 0x4:  # Control
                parts.append('Control')
            if event.state & 0x8:  # Alt
                parts.append('Alt')
            if event.state & 0x1:  # Shift
                parts.append('Shift')
            if event.keysym not in ('Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R'):
                parts.append(event.keysym)
            hotkey = '-'.join(parts)

            # Check if it matches any of our hotkeys
            start_hotkey = self.settings_service.get_setting("hotkey_start", "Control-s")
            pause_hotkey = self.settings_service.get_setting("hotkey_pause", "Pause")

            if hotkey == start_hotkey:
                self.timer_frame.toggle_timer()
                return "break"
            elif hotkey == pause_hotkey:
                self.timer_frame.toggle_pause()
                return "break"

        # Bind to root window to catch all events
        self.root.bind('<Key>', handle_hotkey)

    def run(self):
        # Initialize default categories if needed
        self.block_service.initialize_default_categories()
        self.root.mainloop()
