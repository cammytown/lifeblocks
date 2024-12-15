from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from lifeblocks.models.base import Base


class TimeBlock(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    start_time = Column(DateTime)
    duration_minutes = Column(Float)
    pause_duration_minutes = Column(Float, default=0.0)
    resistance_level = Column(Integer)
    satisfaction_level = Column(Integer)
    notes = Column(String)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    # Relationships
    block = relationship("Block", back_populates="sessions")

    def __init__(
        self,
        block_id,
        start_time,
        duration_minutes,
        resistance_level=None,
        satisfaction_level=None,
        pause_duration_minutes=0.0,
        notes=None,
    ):
        self.block_id = block_id
        self.start_time = start_time
        self.duration_minutes = duration_minutes
        self.resistance_level = resistance_level
        self.satisfaction_level = satisfaction_level
        self.pause_duration_minutes = pause_duration_minutes
        self.notes = notes
        self.deleted = False
        self.deleted_at = None