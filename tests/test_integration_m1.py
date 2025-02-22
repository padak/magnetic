"""Integration tests for Magentic-One agents."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import tempfile
from pathlib import Path

from magnetic.agents.websurfer_m1 import WebSurferM1
from magnetic.agents.filesurfer_m1 import FileSurferM1
from magnetic.agents.orchestrator_m1 import OrchestratorM1
from magnetic.services.trip_planner import TripPlanner
from magnetic.models.trip import Trip, TripStatus

@pytest_asyncio.fixture
async def m1_agents():
    """Create instances of all M1 agents for testing."""
    with patch('autogen_ext.models.openai.OpenAIChatCompletionClient') as mock_client_class:
        # Configure mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Create M1 instance
        from autogen_ext.teams.magentic_one import MagenticOne
        m1 = MagenticOne(client=mock_client)
        
        # Create temporary directories for FileSurfer
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            output_dir = Path(temp_dir) / "output"
            templates_dir.mkdir()
            output_dir.mkdir()
            
            # Create agent instances
            orchestrator = OrchestratorM1()
            websurfer = WebSurferM1()
            filesurfer = FileSurferM1(m1=m1, templates_dir=str(templates_dir), output_dir=str(output_dir))
            
            # Initialize agents
            await orchestrator.initialize()
            await websurfer.initialize()
            
            try:
                yield {
                    'orchestrator': orchestrator,
                    'websurfer': websurfer,
                    'filesurfer': filesurfer,
                    'planner': TripPlanner(websurfer, orchestrator, filesurfer)
                }
            finally:
                await orchestrator.cleanup()
                await websurfer.cleanup()

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
        description="Family trip to Boston",
        destination="Boston",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=35),
        status=TripStatus.PLANNING,
        preferences={
            'interests': ['history', 'sports'],
            'budget': 'medium'
        }
    )
    
    # Test destination research
    research_result = await m1_agents['planner'].research_destination(
        trip.destination,
        {'start': trip.start_date, 'end': trip.end_date},
        trip.preferences
    )
    assert 'attractions' in research_result
    assert 'weather' in research_result
    
    # Test document generation
    documents = await m1_agents['planner'].generate_documents(trip, research_result)
    assert len(documents) == 2  # Guide and emergency info
    assert any('guide' in doc.lower() for doc in documents)
    assert any('emergency' in doc.lower() for doc in documents)
    
    # Test trip monitoring setup
    await m1_agents['planner'].monitor_trip(trip, ['weather', 'travel'])
    
    # Verify orchestrator task execution
    task_info = m1_agents['orchestrator'].get_task_status('task_1')
    assert task_info['status'] == 'completed'

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
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=5),
        status=TripStatus.IN_PROGRESS,
        preferences={}
    )
    
    # Start monitoring
    await m1_agents['planner'].monitor_trip(trip, ['weather'])
    
    # Verify monitoring task execution
    task_info = m1_agents['orchestrator'].get_task_status('task_1')
    assert task_info['status'] == 'completed'
    assert len(task_info.get('updates', [])) > 0

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
        title="Boston Trip",
        destination="Boston",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=35),
        status=TripStatus.PLANNED,
        preferences={'interests': ['history']}
    )
    
    # Generate initial documents
    initial_docs = await m1_agents['planner'].generate_documents(trip, initial_research)
    assert len(initial_docs) > 0
    
    # Update trip preferences
    updated_preferences = {
        'interests': ['history', 'food'],
        'budget': 'high'
    }
    update_result = await m1_agents['planner'].update_trip(trip, {'preferences': updated_preferences})
    assert update_result['status'] == 'success'
    
    # Verify updated documents
    updated_docs = await m1_agents['planner'].generate_documents(trip, update_result)
    assert len(updated_docs) > 0
    assert updated_docs != initial_docs

@pytest.mark.asyncio
async def test_error_handling_and_recovery(m1_agents):
    """Test error handling and recovery across agents."""
    # Mock WebSurfer to fail then succeed
    m1_agents['websurfer'].research_destination = AsyncMock(side_effect=[
        Exception("API Error"),
        {'attractions': ['Success']}
    ])
    
    trip = Trip(
        id=4,
        title="Test Trip",
        destination="Boston",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=5),
        status=TripStatus.PLANNING,
        preferences={}
    )
    
    # Test research with retry
    result = await m1_agents['planner'].research_destination(
        trip.destination,
        {'start': trip.start_date, 'end': trip.end_date},
        trip.preferences
    )
    
    assert 'attractions' in result
    
    # Verify error handling in orchestrator
    task_info = m1_agents['orchestrator'].get_task_status('task_1')
    assert task_info['status'] == 'completed'
    assert len(task_info.get('error_history', [])) == 1 