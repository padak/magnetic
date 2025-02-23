"""Integration tests for Magentic-One agents."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, UTC
import tempfile
from pathlib import Path
import logging
import json

from magnetic.agents.websurfer_m1 import WebSurferM1
from magnetic.agents.filesurfer_m1 import FileSurferM1
from magnetic.agents.orchestrator_m1 import OrchestratorM1
from magnetic.services.trip_planner import TripPlanner
from magnetic.models.trip import Trip, TripStatus

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest_asyncio.fixture
async def m1_agents():
    """Create test agents with mocked M1."""
    
    class MockM1:
        def __init__(self):
            self.messages = []
        
        async def mock_run_stream(self):
            """Mock implementation of run_stream."""
            logger.debug("mock_run_stream called")
            logger.debug(f"Current messages: {json.dumps(self.messages, indent=2)}")
            
            if not self.messages:
                logger.warning("No messages found in mock_run_stream")
                yield "Error: No messages provided"
                return
                
            try:
                # Get the last user message
                last_message = next((m for m in reversed(self.messages) if m['role'] == 'user'), None)
                if not last_message:
                    logger.warning("No user message found")
                    yield "Error: No user message found"
                    return
                
                logger.debug(f"Processing message content: {last_message['content']}")
                
                # Try to parse task data if it exists
                if "Execute task:" in last_message['content']:
                    task_str = last_message['content'].split("Execute task:", 1)[1].strip()
                    try:
                        task_data = json.loads(task_str)
                        logger.debug(f"Parsed task data: {json.dumps(task_data, indent=2)}")
                        
                        # Handle different task types
                        if task_data['type'] == 'monitor_trip':
                            yield json.dumps({
                                "status": "success",
                                "weather": {"temperature": 72, "conditions": "Sunny"},
                                "alerts": []
                            })
                        else:
                            yield json.dumps({
                                "status": "success",
                                "task_type": task_data['type'],
                                "result": "Task completed successfully"
                            })
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse task data: {e}")
                        yield json.dumps({"error": "Invalid task format"})
                else:
                    logger.debug("Processing regular message")
                    yield json.dumps({"status": "success", "message": "Processed successfully"})
                    
            except Exception as e:
                logger.error(f"Error in mock_run_stream: {str(e)}")
                yield json.dumps({"error": str(e)})
        
        run_stream = mock_run_stream

    # Create mock M1 instance
    mock_m1 = MockM1()
    
    # Create agents with mock
    websurfer = WebSurferM1()
    websurfer.m1 = mock_m1
    
    orchestrator = OrchestratorM1()
    orchestrator.m1 = mock_m1
    
    filesurfer = FileSurferM1(mock_m1)
    
    # Create planner
    planner = TripPlanner(websurfer, orchestrator, filesurfer)
    
    # Return dictionary of components
    return {
        'planner': planner,
        'websurfer': websurfer,
        'orchestrator': orchestrator,
        'filesurfer': filesurfer
    }

@pytest.mark.asyncio
async def test_trip_planning_workflow(m1_agents):
    """Test complete trip planning workflow with all agents."""
    # Mock WebSurfer responses
    destination_research = {
        'attractions': ['Freedom Trail', 'Fenway Park'],
        'weather': {'temperature': 20, 'conditions': 'Clear'},
        'local_info': {
            'safety': ['Safe area'],
            'customs': ['Tipping culture'],
            'emergency_info': {
                'police': '911',
                'hospital': 'Mass General'
            }
        }
    }
    m1_agents['websurfer'].research_destination = AsyncMock(return_value=destination_research)
    
    # Create test trip
    trip = Trip(
        id=1,
        title="Boston Adventure",
        destination="Boston",
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=5),
        status="planning",
        preferences={
            'interests': ['history', 'sports'],
            'budget': 'medium'
        }
    )
    
    # Test destination research
    result = await m1_agents['planner'].research_destination(
        destination=trip.destination,
        dates={'start': trip.start_date, 'end': trip.end_date},
        preferences=trip.preferences
    )
    
    assert result == destination_research
    assert 'Freedom Trail' in result['attractions']
    assert result['weather']['temperature'] == 20

@pytest.mark.asyncio
async def test_real_time_monitoring(m1_agents):
    """Test real-time monitoring integration between agents."""
    # Mock weather updates
    weather_updates = [
        {'temperature': 20, 'conditions': 'Clear', 'timestamp': datetime.now().isoformat()},
        {'temperature': 22, 'conditions': 'Cloudy', 'timestamp': datetime.now().isoformat()}
    ]
    m1_agents['websurfer'].get_weather = AsyncMock(side_effect=weather_updates)
    
    # Create test trip
    trip = Trip(
        id=2,
        title="Boston Trip",
        destination="Boston",
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=3),
        status="in_progress"
    )
    
    # Start monitoring
    await m1_agents['planner'].monitor_trip(trip, ['weather'])
    
    # Verify monitoring setup
    task = m1_agents['orchestrator'].tasks.get('task_1')
    assert task is not None
    assert task['type'] == 'monitor_trip'
    assert task['status'] == 'completed'

@pytest.mark.asyncio
async def test_document_updates(m1_agents):
    """Test document updates based on trip changes."""
    # Mock initial research
    initial_research = {
        'attractions': ['Museum'],
        'weather': {'temperature': 20},
        'local_info': {'safety': ['Safe area']}
    }
    m1_agents['websurfer'].research_destination = AsyncMock(return_value=initial_research)
    
    # Create test trip
    trip = Trip(
        id=3,
        title="Boston Visit",
        destination="Boston",
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=4),
        status="planning",
        preferences={
            'interests': ['history', 'culture'],
            'budget': 'medium'
        }
    )
    
    # Generate initial documents
    docs = await m1_agents['planner'].generate_documents(trip, initial_research)
    assert len(docs) > 0
    
    # Update trip and regenerate documents
    updated_research = {
        'attractions': ['Museum', 'New Attraction'],
        'weather': {'temperature': 22},
        'local_info': {'safety': ['Safe area', 'Additional info']}
    }
    m1_agents['websurfer'].research_destination = AsyncMock(return_value=updated_research)
    
    updated_docs = await m1_agents['planner'].generate_documents(trip, updated_research)
    assert len(updated_docs) > 0

@pytest.mark.asyncio
async def test_error_handling_and_recovery(m1_agents):
    """Test error handling and recovery across agents."""
    # Mock WebSurfer to fail then succeed
    m1_agents['websurfer'].research_destination = AsyncMock(side_effect=[
        Exception("API Error"),
        {'attractions': ['Success']}
    ])
    
    # Create test trip
    trip = Trip(
        id=4,
        title="Error Test Trip",
        destination="Boston",
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=2),
        status="planning"
    )
    
    # First attempt should fail
    with pytest.raises(Exception) as exc_info:
        await m1_agents['planner'].research_destination(
            destination=trip.destination,
            dates={'start': trip.start_date, 'end': trip.end_date},
            preferences={}
        )
    assert "API Error" in str(exc_info.value)
    
    # Second attempt should succeed
    result = await m1_agents['planner'].research_destination(
        destination=trip.destination,
        dates={'start': trip.start_date, 'end': trip.end_date},
        preferences={}
    )
    assert result['attractions'] == ['Success'] 