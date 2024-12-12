from datetime import datetime
import time
from lifeblocks.models.block import Block


class TimerService:
    def __init__(self, session, settings_service):
        self.session = session
        self.settings_service = settings_service
        self.timer_active = False
        self.session_start = None
        self.session_duration = 0
        self.end_time = 0.0
        self.current_block = None
        self.resistance_level = None
        self.paused = False
        self.pause_start = 0.0
        self.total_pause_duration = 0

    def get_default_duration(self):
        return int(self.settings_service.get_setting("default_duration", "60"))

    def set_default_duration(self, duration):
        self.settings_service.set_setting("default_duration", str(duration))

    def start_timer(self, block, minutes, resistance_level):
        self.timer_active = True
        self.session_start = datetime.now()
        self.session_duration = minutes
        self.end_time = time.time() + (minutes * 60)
        self.current_block = block
        self.resistance_level = resistance_level
        self.paused = False
        self.pause_start = 0.0
        self.total_pause_duration = 0.0
        return True

    def pause_timer(self):
        if self.timer_active and not self.paused:
            self.paused = True
            self.pause_start = time.time()
            return True
        return False

    def resume_timer(self):
        if self.timer_active and self.paused:
            pause_duration = time.time() - self.pause_start
            self.total_pause_duration += pause_duration
            self.end_time += pause_duration
            self.paused = False
            self.pause_start = 0.0
            return True
        return False

    def get_remaining_time(self):
        if not self.timer_active:
            return 0, 0, False

        if self.paused:
            remaining = max(0, self.end_time - self.pause_start)
        else:
            remaining = max(0, self.end_time - time.time())

        minutes = int(remaining // 60)
        seconds = int(remaining % 60)

        return minutes, seconds, remaining <= 0

    def stop_timer(self):
        if not self.timer_active:
            return 0

        self.timer_active = False
        current_time = self.pause_start if self.paused else time.time()
        elapsed_minutes = (current_time - self.session_start.timestamp()) / 60

        return elapsed_minutes

    def save_session(self, elapsed_minutes, satisfaction_level=None, notes=None):
        if not self.session_start or not self.current_block:
            return False

        from models.timeblock import TimeBlock

        timeblock = TimeBlock(
            block_id=self.current_block.id,
            start_time=self.session_start,
            duration_minutes=elapsed_minutes,
            resistance_level=self.resistance_level,
            satisfaction_level=satisfaction_level,
            pause_duration_minutes=self.total_pause_duration / 60,
            notes=notes,
        )

        self.session.add(timeblock)
        self.session.commit()

        # Update block's last_picked time
        self.current_block.last_picked = self.session_start
        self.session.commit()

        return True
