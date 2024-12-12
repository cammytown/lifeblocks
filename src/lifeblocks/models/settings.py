from sqlalchemy import Column, Integer, String
from lifeblocks.models.base import Base
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, key: str, value: str) -> None:
        super().__init__()
        self.key = key
        self.value = value
