"""Trip planning service using M1 agents."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..agents.websurfer_m1 import WebSurferM1
from ..agents.filesurfer_m1 import FileSurferM1
from ..agents.orchestrator_m1 import OrchestratorM1
from ..models.trip import Trip

logger = logging.getLogger(__name__)

class TripPlanner:
    """Service for planning trips using M1 agents."""
    
    def __init__(
        self,
        websurfer: WebSurferM1,
        orchestrator: OrchestratorM1,
        filesurfer: Optional[FileSurferM1] = None
    ):
        """Initialize the trip planner.
        
        Args:
            websurfer: WebSurferM1 agent for web interactions
            orchestrator: OrchestratorM1 agent for task coordination
            filesurfer: Optional FileSurferM1 agent for document management
        """
        self.websurfer = websurfer
        self.orchestrator = orchestrator
        self.filesurfer = filesurfer
        
    async def research_destination(
        self,
        destination: str,
        dates: Dict[str, datetime],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research a destination using WebSurferM1.
        
        Args:
            destination: Name of the destination
            dates: Dictionary with start and end dates
            preferences: User preferences
            
        Returns:
            Dictionary containing research results
        """
        return await self.websurfer.research_destination(
            destination=destination,
            dates=dates,
            preferences=preferences
        )
        
    async def generate_documents(
        self,
        trip: Trip,
        planning_result: Dict[str, Any]
    ) -> List[str]:
        """Generate trip documents using FileSurferM1.
        
        Args:
            trip: Trip model instance
            planning_result: Results from trip planning
            
        Returns:
            List of generated document paths
        """
        if not self.filesurfer:
            logger.warning("FileSurferM1 not available, skipping document generation")
            return []
            
        documents = []
        
        # Generate travel guide
        guide_path = await self.filesurfer.create_travel_guide(
            destination=trip.destination,
            interests=trip.preferences.get('interests', [])
        )
        documents.append(guide_path)
        
        # Generate emergency info
        emergency_path = await self.filesurfer.create_emergency_info({
            'destination': trip.destination,
            'dates': {
                'start': trip.start_date.isoformat(),
                'end': trip.end_date.isoformat()
            },
            'emergency_info': planning_result.get('emergency_info', {})
        })
        documents.append(emergency_path)
        
        return documents
        
    async def update_trip(
        self,
        trip: Trip,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update trip details using OrchestratorM1.
        
        Args:
            trip: Trip model instance
            updates: Dictionary of updates
            
        Returns:
            Updated trip information
        """
        update_task = {
            'type': 'update_trip',
            'data': {
                'trip_id': trip.id,
                'updates': updates,
                'current_state': {
                    'destination': trip.destination,
                    'dates': {
                        'start': trip.start_date.isoformat(),
                        'end': trip.end_date.isoformat()
                    },
                    'preferences': trip.preferences
                }
            }
        }
        
        return await self.orchestrator.execute(update_task)
        
    async def monitor_trip(
        self,
        trip: Trip,
        monitor_types: List[str]
    ) -> None:
        """Set up trip monitoring using OrchestratorM1.
        
        Args:
            trip: Trip model instance
            monitor_types: List of aspects to monitor (e.g., ['weather', 'flights'])
        """
        monitor_task = {
            'type': 'monitor_trip',
            'data': {
                'trip_id': trip.id,
                'destination': trip.destination,
                'monitor_types': monitor_types,
                'dates': {
                    'start': trip.start_date.isoformat(),
                    'end': trip.end_date.isoformat()
                }
            }
        }
        
        await self.orchestrator.execute(monitor_task) 