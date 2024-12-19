from datetime import datetime
import time
from lifeblocks.models.block import Block
from lifeblocks.models.timeblock import TimeBlock, TimeBlockState


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
        self.active_timeblock = None
        
        # Check for any incomplete timeblocks and resume them
        self._restore_active_timer()

    def _restore_active_timer(self):
        """Restore timer state from any incomplete timeblock"""
        incomplete = self.session.query(TimeBlock).filter(
            TimeBlock.state.in_([TimeBlockState.ACTIVE, TimeBlockState.PAUSED]),
            TimeBlock.deleted.is_(False)
        ).first()
        
        if incomplete:
            self.timer_active = True
            self.session_start = incomplete.start_time
            self.session_duration = incomplete.duration_minutes
            self.current_block = incomplete.block
            self.resistance_level = incomplete.resistance_level
            self.total_pause_duration = incomplete.pause_duration_minutes * 60  # Convert to seconds
            
            # Calculate end_time based on start time, duration, and pauses
            elapsed_seconds = (datetime.now() - incomplete.start_time).total_seconds()
            remaining_seconds = (incomplete.duration_minutes * 60) - (elapsed_seconds - self.total_pause_duration)
            
            # If the timer has expired while we were away, mark it as such
            if remaining_seconds <= 0:
                incomplete.state = TimeBlockState.EXPIRED
                self.session.commit()
                return
            
            self.end_time = time.time() + remaining_seconds
            
            # Check if we were paused
            if incomplete.state == TimeBlockState.PAUSED:
                self.paused = True
                self.pause_start = time.time() - (datetime.now() - incomplete.pause_start).total_seconds()
            
            self.active_timeblock = incomplete

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
        
        # Create timeblock in ACTIVE state
        self.active_timeblock = TimeBlock(
            block_id=block.id,
            start_time=self.session_start,
            duration_minutes=minutes,
            resistance_level=resistance_level,
            state=TimeBlockState.ACTIVE
        )
        self.session.add(self.active_timeblock)
        self.session.commit()
        return True

    def pause_timer(self):
        if self.timer_active and not self.paused:
            self.paused = True
            self.pause_start = time.time()
            if self.active_timeblock:
                self.active_timeblock.state = TimeBlockState.PAUSED
                self.active_timeblock.pause_start = datetime.now()
                self.session.commit()
            return True
        return False

    def resume_timer(self):
        if self.timer_active and self.paused:
            pause_duration = time.time() - self.pause_start
            self.total_pause_duration += pause_duration
            self.end_time += pause_duration
            if self.active_timeblock:
                self.active_timeblock.state = TimeBlockState.ACTIVE
                self.active_timeblock.pause_duration_minutes = self.total_pause_duration / 60
                self.active_timeblock.pause_start = None
                self.session.commit()
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
        is_finished = remaining <= 0

        if is_finished and self.active_timeblock:
            self.active_timeblock.state = TimeBlockState.EXPIRED
            self.session.commit()

        return minutes, seconds, is_finished

    def stop_timer(self):
        if not self.timer_active:
            return 0

        self.timer_active = False
        current_time = self.pause_start if self.paused else time.time()
        total_elapsed_minutes = (current_time - self.session_start.timestamp()) / 60
        
        # Subtract pause duration to get actual working time
        active_elapsed_minutes = total_elapsed_minutes - (self.total_pause_duration / 60)
        
        if self.active_timeblock:
            self.active_timeblock.state = TimeBlockState.ABANDONED
            self.session.commit()
        
        return active_elapsed_minutes

    def save_session(self, elapsed_minutes, satisfaction_level=None, notes=None):
        if not self.session_start or not self.current_block:
            return False

        if self.active_timeblock:
            # Update existing timeblock
            self.active_timeblock.duration_minutes = elapsed_minutes
            self.active_timeblock.satisfaction_level = satisfaction_level
            self.active_timeblock.notes = notes
            self.active_timeblock.state = TimeBlockState.COMPLETED
            self.active_timeblock.pause_start = None
        else:
            # Create new timeblock (fallback)
            self.active_timeblock = TimeBlock(
                block_id=self.current_block.id,
                start_time=self.session_start,
                duration_minutes=elapsed_minutes,
                resistance_level=self.resistance_level,
                satisfaction_level=satisfaction_level,
                pause_duration_minutes=self.total_pause_duration / 60,
                notes=notes,
                state=TimeBlockState.COMPLETED
            )
            self.session.add(self.active_timeblock)

        self.session.commit()

        # Update block's last_picked time
        self.current_block.last_picked = self.session_start
        self.session.commit()

        return True
