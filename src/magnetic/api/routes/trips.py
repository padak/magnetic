"""Trip management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...models.trip import Trip, TripStatus
from ...services.trip_planner import TripPlanner
from ...agents.websurfer_m1 import WebSurferM1
from ...agents.filesurfer_m1 import FileSurferM1
from ...agents.orchestrator_m1 import OrchestratorM1
from ..schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trips", tags=["trips"])

async def get_trip_planner() -> TripPlanner:
    """Get TripPlanner instance with M1 agents."""
    # Initialize M1 agents
    websurfer = WebSurferM1()
    orchestrator = OrchestratorM1()
    await websurfer.initialize()
    await orchestrator.initialize()
    
    try:
        yield TripPlanner(websurfer, orchestrator)
    finally:
        await websurfer.cleanup()
        await orchestrator.cleanup()

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
    """Create a new trip with initial planning using M1 agents."""
    logger.info("Creating new trip with M1 agents")
    logger.info(f"Received trip data: {trip_data}")
    
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
        
        db.add(trip)
        db.commit()
        db.refresh(trip)
        
        # Create planning task for orchestrator
        planning_task = {
            'type': 'plan_trip',
            'data': {
                'destination': trip.destination,
                'dates': {
                    'start': trip.start_date.isoformat(),
                    'end': trip.end_date.isoformat()
                },
                'preferences': trip.preferences
            }
        }
        
        # Execute planning through orchestrator
        planning_result = await planner.orchestrator.execute(planning_task)
        
        # Generate documents
        await planner.generate_documents(trip, planning_result)
        
        # Update trip with results
        trip.status = TripStatus.PLANNED
        db.commit()
        db.refresh(trip)
        
        return trip
        
    except Exception as e:
        logger.error(f"Error in create_trip: {str(e)}")
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