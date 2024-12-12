import os
import subprocess
from tkinter import messagebox


class NotificationService:
    def __init__(self):
        self.has_notifications = os.system("which notify-send >/dev/null 2>&1") == 0

    def alert_time_up(self, block_name):
        self._send_notification(block_name)
        self._play_sound()

    def _send_notification(self, block_name):
        if self.has_notifications:
            try:
                subprocess.run(
                    [
                        "notify-send",
                        "Time Up!",
                        f'Block "{block_name}" timer has finished',
                        "-u",
                        "critical",
                    ]
                )
            except FileNotFoundError:
                messagebox.showinfo("Time's Up!", f"Time's up for {block_name}!")

    def _play_sound(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        audio_file = os.path.join(script_dir, "..", "ui", "youtube-hyoshigi.opus")

        try:
            subprocess.run(["paplay", audio_file])
        except FileNotFoundError:
            try:
                subprocess.run(["aplay", audio_file])
            except FileNotFoundError:
                pass
