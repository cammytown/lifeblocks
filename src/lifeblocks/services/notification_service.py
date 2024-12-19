import os
import subprocess
from tkinter import messagebox


class NotificationService:
    def __init__(self, settings_service=None):
        self.has_notifications = os.system("which notify-send >/dev/null 2>&1") == 0
        self.settings_service = settings_service

    def alert_time_up(self, block_name):
        self._send_notification(block_name)
        if self.settings_service and self.settings_service.get_setting("play_sound", "true") == "true":
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

    def _play_sound(self, show_errors=False):
        if not self.settings_service:
            if show_errors:
                messagebox.showerror("Error", "Settings service not initialized")
            return

        # Get sound file path from settings
        sound_file = self.settings_service.get_setting("sound_file", "youtube-hyogishi.opus")
        print(f"Attempting to play sound file: {sound_file}")
        
        # If it's a relative path, look in the default locations
        if not os.path.isabs(sound_file):
            # First try the workspace root
            workspace_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
            sound_path = os.path.join(workspace_path, sound_file)
            print(f"Checking workspace path: {sound_path}")
            
            # If not found, try the ui directory
            if not os.path.exists(sound_path):
                sound_path = os.path.join(workspace_path, "src", "lifeblocks", "ui", sound_file)
                print(f"Checking ui directory path: {sound_path}")
        else:
            sound_path = sound_file
            print(f"Using absolute path: {sound_path}")

        if not os.path.exists(sound_path):
            error_msg = f"Sound file not found: {sound_file}\nTried paths:\n- {sound_path}"
            print(error_msg)
            if show_errors:
                messagebox.showerror("Error", error_msg)
            return

        success = False
        error_msg = ""

        # Try paplay first (PulseAudio)
        try:
            print("Attempting to play with paplay...")
            result = subprocess.run(["paplay", sound_path], check=True, capture_output=True, text=True)
            print(f"paplay output: {result.stdout}")
            if result.stderr:
                print(f"paplay stderr: {result.stderr}")
            success = True
        except FileNotFoundError:
            print("paplay not found")
            error_msg = "paplay not found, "
        except subprocess.CalledProcessError as e:
            print(f"paplay error: {str(e)}")
            if e.stdout:
                print(f"paplay stdout: {e.stdout}")
            if e.stderr:
                print(f"paplay stderr: {e.stderr}")
            error_msg = f"paplay error: {str(e)}, "

        # If paplay failed, try aplay (ALSA)
        if not success:
            try:
                print("Attempting to play with aplay...")
                result = subprocess.run(["aplay", sound_path], check=True, capture_output=True, text=True)
                print(f"aplay output: {result.stdout}")
                if result.stderr:
                    print(f"aplay stderr: {result.stderr}")
                success = True
            except FileNotFoundError:
                print("aplay not found")
                error_msg += "aplay not found"
            except subprocess.CalledProcessError as e:
                print(f"aplay error: {str(e)}")
                if e.stdout:
                    print(f"aplay stdout: {e.stdout}")
                if e.stderr:
                    print(f"aplay stderr: {e.stderr}")
                error_msg += f"aplay error: {str(e)}"

        if not success:
            error_msg = f"Failed to play sound: {error_msg}\nSound file: {sound_path}"
            print(error_msg)
            if show_errors:
                messagebox.showerror("Error", error_msg)

    def test_sound(self):
        """Test sound playback with error reporting enabled"""
        print("\nTesting sound playback...")
        self._play_sound(show_errors=True)
