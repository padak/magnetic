"""Trip management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...models.trip import Trip, TripStatus
from ...services.trip_planner import TripPlanner
from ...agents.websurfer import WebSurferAgent
from ..schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["trips"])

async def get_trip_planner() -> TripPlanner:
    """Get TripPlanner instance."""
    websurfer = WebSurferAgent()
    await websurfer.initialize()
    try:
        yield TripPlanner(websurfer)
    finally:
        await websurfer.cleanup()

@router.post(
    "/",
    response_model=TripResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Create a new trip"
)
async def create_trip(
    trip_data: TripCreate,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> TripResponse:
    """Create a new trip with initial planning."""
    logger.info("Entering create_trip endpoint")
    logger.info(f"Received trip data: {trip_data}")
    logger.info(f"Database session object: {db}")
    logger.info(f"Session type: {type(db)}")
    
    try:
        # Create trip instance
        trip = Trip(
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            status=TripStatus.PLANNING,
            preferences=trip_data.preferences.dict()
        )
        logger.info(f"Created trip instance: {trip}")
        
        logger.info("Attempting to add trip to session")
        db.add(trip)
        logger.info("Successfully added trip to session")
        
        logger.info("Attempting to commit")
        db.commit()
        logger.info("Successfully committed")
        
        db.refresh(trip)
        logger.info(f"Refreshed trip instance: {trip}")
        
        # Research destination
        research_results = await planner.research_destination(
            trip_data.destination,
            {
                'start': trip_data.start_date,
                'end': trip_data.end_date
            },
            trip_data.preferences.dict()
        )
        
        # Create itinerary
        itinerary = await planner.create_itinerary(trip, research_results)
        for day in itinerary:
            db.add(day)
        
        # Calculate budget
        budget = planner.calculate_budget(trip, itinerary)
        db.add(budget)
        
        db.commit()
        db.refresh(trip)
        
        return trip
        
    except Exception as e:
        logger.error(f"Error in create_trip: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating trip: {str(e)}"
        )

@router.get(
    "/",
    response_model=TripListResponse,
    summary="List all trips"
)
async def list_trips(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> TripListResponse:
    """List all trips with pagination."""
    query = db.query(Trip)
    
    if status:
        query = query.filter(Trip.status == status)
    
    total = query.count()
    trips = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return TripListResponse(
        trips=trips,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get(
    "/{trip_id}",
    response_model=TripResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get trip details"
)
async def get_trip(
    trip_id: int,
    db: Session = Depends(get_db)
) -> TripResponse:
    """Get detailed information about a specific trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    return trip

@router.patch(
    "/{trip_id}",
    response_model=TripResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Update trip details"
)
async def update_trip(
    trip_id: int,
    trip_update: TripUpdate,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> TripResponse:
    """Update trip details and optionally recalculate itinerary."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        # Update basic details
        if trip_update.title:
            trip.title = trip_update.title
        if trip_update.description is not None:
            trip.description = trip_update.description
        
        # Update preferences and recalculate if needed
        if trip_update.preferences:
            trip.preferences.update(trip_update.preferences.dict())
            
            # Recalculate itinerary with new preferences
            research_results = await planner.research_destination(
                trip.destination,
                {
                    'start': trip.start_date,
                    'end': trip.end_date
                },
                trip.preferences
            )
            
            # Clear existing itinerary
            for day in trip.itinerary_days:
                db.delete(day)
            if trip.budget:
                db.delete(trip.budget)
            
            # Create new itinerary
            itinerary = await planner.create_itinerary(trip, research_results)
            for day in itinerary:
                db.add(day)
            
            # Recalculate budget
            budget = planner.calculate_budget(trip, itinerary)
            db.add(budget)
        
        db.commit()
        db.refresh(trip)
        return trip
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error updating trip: {str(e)}"
        )

@router.delete(
    "/{trip_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a trip"
)
async def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db)
) -> None:
    """Delete a trip and all associated data."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        db.delete(trip)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error deleting trip: {str(e)}"
        ) 