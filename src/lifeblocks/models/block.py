from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from lifeblocks.models.base import Base


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    weight = Column(Integer, default=1)
    last_picked = Column(DateTime)
    parent_id = Column(Integer, ForeignKey("blocks.id"))
    max_interval_hours = Column(Integer, nullable=True)

    # Relationships
    children = relationship("Block", backref="parent", remote_side=[id])
    sessions = relationship("TimeBlock", back_populates="block")

    def __init__(self, name, weight=1, parent_id=None, max_interval_hours=None):
        self.name = name
        self.weight = weight
        self.parent_id = parent_id
        self.max_interval_hours = max_interval_hours
