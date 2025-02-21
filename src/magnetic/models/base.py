"""Base model configuration."""

from datetime import datetime
from typing import Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import Mapped

Base = declarative_base()

class BaseModel(Base):
    """Base model class with common fields."""
    
    __abstract__ = True

    id: Mapped[int] = Column(Integer, primary_key=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>" 