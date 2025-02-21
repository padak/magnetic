"""API schema definitions using Pydantic models."""

from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

class TripPreferences(BaseModel):
    """Trip preferences model."""
    adults: int = Field(default=2, ge=1)
    children: int = Field(default=0, ge=0)
    hotel_budget: str = Field(default="MODERATE")
    max_activity_price: float = Field(default=100.0, ge=0)
    activity_types: List[str] = Field(default_factory=lambda: ["SIGHTSEEING", "FAMILY_FUN"])
    family_friendly: bool = Field(default=True)
    accessible: bool = Field(default=False)
    transportation_budget: float = Field(default=500.0, ge=0)
    food_budget: float = Field(default=300.0, ge=0)
    misc_budget: float = Field(default=200.0, ge=0)
    currency: str = Field(default="USD")

class TripCreate(BaseModel):
    """Trip creation request model."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    destination: str = Field(..., min_length=1, max_length=255)
    start_date: datetime
    end_date: datetime
    preferences: TripPreferences = Field(default_factory=TripPreferences)

class ActivityResponse(BaseModel):
    """Activity response model."""
    name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    cost: Decimal
    booking_info: Dict = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True

class AccommodationResponse(BaseModel):
    """Accommodation response model."""
    name: str
    address: str
    check_in: datetime
    check_out: datetime
    cost: Decimal
    booking_info: Dict = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True

class ItineraryDayResponse(BaseModel):
    """Itinerary day response model."""
    date: datetime
    notes: Optional[str]
    activities: List[ActivityResponse]
    accommodation: Optional[AccommodationResponse]

    class Config:
        """Pydantic config."""
        from_attributes = True

class BudgetResponse(BaseModel):
    """Budget response model."""
    total: Decimal
    spent: Decimal
    currency: str
    breakdown: Dict[str, Decimal]

    class Config:
        """Pydantic config."""
        from_attributes = True

class TripResponse(BaseModel):
    """Trip response model."""
    id: int
    title: str
    description: Optional[str]
    destination: str
    start_date: datetime
    end_date: datetime
    status: str
    preferences: TripPreferences
    itinerary_days: List[ItineraryDayResponse]
    budget: Optional[BudgetResponse]

    class Config:
        """Pydantic config."""
        from_attributes = True

class TripListResponse(BaseModel):
    """Trip list response model."""
    trips: List[TripResponse]
    total: int
    page: int
    page_size: int

class TripUpdate(BaseModel):
    """Trip update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    preferences: Optional[TripPreferences]

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    code: Optional[str] 