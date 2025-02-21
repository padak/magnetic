"""Trip planning models."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, Enum
from sqlalchemy.orm import relationship, Mapped
import enum

from .base import BaseModel

class TripStatus(enum.Enum):
    """Trip status enumeration."""
    DRAFT = "draft"
    PLANNING = "planning"
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Trip(BaseModel):
    """Trip model representing a planned journey."""
    
    __tablename__ = "trips"

    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[Optional[str]] = Column(String(1000))
    destination: Mapped[str] = Column(String(255), nullable=False)
    start_date: Mapped[datetime] = Column(DateTime, nullable=False)
    end_date: Mapped[datetime] = Column(DateTime, nullable=False)
    status: Mapped[TripStatus] = Column(Enum(TripStatus), default=TripStatus.DRAFT, nullable=False)
    preferences: Mapped[dict] = Column(JSON, default=dict)
    
    # Relationships
    itinerary_days: Mapped[List["ItineraryDay"]] = relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan")
    budget: Mapped["Budget"] = relationship("Budget", back_populates="trip", uselist=False, cascade="all, delete-orphan")

class ItineraryDay(BaseModel):
    """Model representing a single day in a trip itinerary."""
    
    __tablename__ = "itinerary_days"

    trip_id: Mapped[int] = Column(ForeignKey("trips.id"), nullable=False)
    date: Mapped[datetime] = Column(DateTime, nullable=False)
    notes: Mapped[Optional[str]] = Column(String(1000))
    
    # Relationships
    trip: Mapped[Trip] = relationship("Trip", back_populates="itinerary_days")
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="day", cascade="all, delete-orphan")
    accommodation: Mapped[Optional["Accommodation"]] = relationship("Accommodation", back_populates="day", uselist=False, cascade="all, delete-orphan")

class Activity(BaseModel):
    """Model representing an activity in the itinerary."""
    
    __tablename__ = "activities"

    day_id: Mapped[int] = Column(ForeignKey("itinerary_days.id"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[Optional[str]] = Column(String(1000))
    start_time: Mapped[datetime] = Column(DateTime, nullable=False)
    end_time: Mapped[datetime] = Column(DateTime, nullable=False)
    location: Mapped[Optional[str]] = Column(String(255))
    cost: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    booking_info: Mapped[dict] = Column(JSON, default=dict)
    
    # Relationships
    day: Mapped[ItineraryDay] = relationship("ItineraryDay", back_populates="activities")

class Accommodation(BaseModel):
    """Model representing accommodation for a day."""
    
    __tablename__ = "accommodations"

    day_id: Mapped[int] = Column(ForeignKey("itinerary_days.id"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    address: Mapped[str] = Column(String(255), nullable=False)
    check_in: Mapped[datetime] = Column(DateTime, nullable=False)
    check_out: Mapped[datetime] = Column(DateTime, nullable=False)
    cost: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    booking_info: Mapped[dict] = Column(JSON, default=dict)
    
    # Relationships
    day: Mapped[ItineraryDay] = relationship("ItineraryDay", back_populates="accommodation")

class Budget(BaseModel):
    """Model representing a trip's budget."""
    
    __tablename__ = "budgets"

    trip_id: Mapped[int] = Column(ForeignKey("trips.id"), nullable=False)
    total: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    spent: Mapped[Decimal] = Column(Numeric(10, 2), default=0)
    currency: Mapped[str] = Column(String(3), nullable=False, default="USD")
    breakdown: Mapped[dict] = Column(JSON, default=dict)
    
    # Relationships
    trip: Mapped[Trip] = relationship("Trip", back_populates="budget") 