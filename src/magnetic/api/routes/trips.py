"""Trip management API routes."""

from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager
import os

from ...database import get_db
from ...models.trip import Trip, TripStatus
from ...services.trip_planner import TripPlanner
from ...agents.websurfer_m1 import WebSurferM1
from ...agents.filesurfer_m1 import FileSurferM1
from ...agents.orchestrator_m1 import OrchestratorM1
from ...config.llm_config import LLMConfig
from ..schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
    TripDocument,
    TripMonitoring,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trips", tags=["trips"])

async def get_trip_planner() -> TripPlanner:
    """Get TripPlanner instance with M1 agents."""
    # Get agent configuration from LLMConfig
    agent_config = LLMConfig.get_agent_config()
    
    # Initialize M1 agents with configuration
    websurfer = WebSurferM1(config=agent_config)
    orchestrator = OrchestratorM1(config=agent_config)
    filesurfer = FileSurferM1(config=agent_config)
    
    await websurfer.initialize()
    await orchestrator.initialize()
    
    planner = TripPlanner(websurfer, orchestrator, filesurfer)
    return planner

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
        
        # Research destination
        research_result = await planner.research_destination(
            trip.destination,
            {
                'start_date': trip.start_date,
                'end_date': trip.end_date
            },
            trip.preferences
        )
        
        # Generate documents
        await planner.generate_documents(trip, research_result)
        
        # Update trip status
        trip.status = TripStatus.PLANNED
        db.commit()
        db.refresh(trip)
        
        # Clean up resources
        await planner.websurfer.cleanup()
        await planner.orchestrator.cleanup()
        
        return trip
        
    except Exception as e:
        logger.error(f"Error in create_trip: {str(e)}")
        db.rollback()
        
        # Clean up resources on error
        try:
            await planner.websurfer.cleanup()
            await planner.orchestrator.cleanup()
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        
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
                    'start_date': trip.start_date,
                    'end_date': trip.end_date
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

@router.get(
    "/{trip_id}/documents",
    response_model=List[TripDocument],
    responses={404: {"model": ErrorResponse}},
    summary="Get trip documents"
)
async def get_trip_documents(
    trip_id: int,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> List[TripDocument]:
    """Get documents associated with a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        # Get documents from FileSurfer
        documents = await planner.filesurfer.list_documents(trip_id)
        return documents
    except Exception as e:
        logger.error(f"Error getting trip documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving documents: {str(e)}"
        )

@router.get(
    "/{trip_id}/monitoring",
    response_model=TripMonitoring,
    responses={404: {"model": ErrorResponse}},
    summary="Get trip monitoring updates"
)
async def get_trip_monitoring(
    trip_id: int,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> TripMonitoring:
    """Get real-time monitoring updates for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        # Get monitoring updates from Orchestrator
        task_id = f"monitor_{trip_id}"
        task_info = planner.orchestrator.get_task_status(task_id)
        
        if not task_info or task_info['status'] == 'failed':
            raise HTTPException(
                status_code=404,
                detail="No monitoring data available"
            )
        
        return task_info.get('updates', {})
    except Exception as e:
        logger.error(f"Error getting monitoring updates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving monitoring data: {str(e)}"
        )

@router.post(
    "/{trip_id}/monitoring",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Start trip monitoring"
)
async def start_monitoring(
    trip_id: int,
    monitor_types: List[str] = Query(['weather', 'travel']),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> None:
    """Start monitoring a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        # Start monitoring in background
        background_tasks.add_task(
            planner.monitor_trip,
            trip,
            monitor_types
        )
    except Exception as e:
        logger.error(f"Error starting trip monitoring: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting monitoring: {str(e)}"
        )

@router.delete(
    "/{trip_id}/monitoring",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Stop trip monitoring"
)
async def stop_monitoring(
    trip_id: int,
    db: Session = Depends(get_db),
    planner: TripPlanner = Depends(get_trip_planner)
) -> None:
    """Stop monitoring a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    try:
        # Stop monitoring task
        task_id = f"monitor_{trip_id}"
        await planner.orchestrator.cleanup_task(task_id)
    except Exception as e:
        logger.error(f"Error stopping trip monitoring: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping monitoring: {str(e)}"
        ) 