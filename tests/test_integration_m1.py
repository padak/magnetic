"""Integration tests for Magentic-One agents."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from magnetic.agents.websurfer_m1 import WebSurferM1
from magnetic.agents.filesurfer_m1 import FileSurferM1
from magnetic.agents.orchestrator_m1 import OrchestratorM1

@pytest_asyncio.fixture
async def agents():
    """Create instances of all agents for testing."""
    with patch('autogen_ext.models.openai.OpenAIChatCompletionClient') as mock_client_class:
        # Configure mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Create M1 instance
        from autogen_ext.teams.magentic_one import MagenticOne
        m1 = MagenticOne(client=mock_client)
        
        # Create agent instances
        orchestrator = OrchestratorM1()
        websurfer = WebSurferM1()
        filesurfer = FileSurferM1(m1=m1)
        
        # Initialize agents
        await orchestrator.initialize()
        await websurfer.initialize()
        
        try:
            yield {
                'orchestrator': orchestrator,
                'websurfer': websurfer,
                'filesurfer': filesurfer
            }
        finally:
            await orchestrator.cleanup()
            await websurfer.cleanup()

@pytest.mark.asyncio
async def test_trip_planning_workflow(agents):
    """Test complete trip planning workflow with all agents."""
    # Mock WebSurfer responses
    destination_research = {
        'attractions': ['Freedom Trail', 'Fenway Park'],
        'weather': {'temperature': 20, 'conditions': 'Clear'},
        'local_info': {'safety': ['Safe area'], 'customs': ['Tipping culture']}
    }
    agents['websurfer'].research_destination = AsyncMock(return_value=destination_research)
    
    # Mock route planning
    route_info = {
        'route': {'distance': '400 miles', 'duration': '6 hours'},
        'stops': ['Stop 1', 'Stop 2']
    }
    agents['websurfer'].plan_route = AsyncMock(return_value=route_info)
    
    # Create trip planning task
    trip_task = {
        'type': 'plan_trip',
        'data': {
            'destination': 'Boston',
            'dates': {
                'start': datetime.now() + timedelta(days=30),
                'end': datetime.now() + timedelta(days=35)
            },
            'preferences': {
                'interests': ['history', 'sports'],
                'budget': 'medium'
            }
        }
    }
    
    # Execute trip planning through orchestrator
    result = await agents['orchestrator'].execute(trip_task)
    assert result['status'] == 'success'
    
    # Verify document generation
    guide_path = await agents['filesurfer'].create_travel_guide(
        destination='Boston',
        interests=['history', 'sports']
    )
    assert guide_path.endswith('.md')
    
    emergency_path = await agents['filesurfer'].create_emergency_info({
        'destination': 'Boston',
        'embassy_info': {'phone': '123-456-7890'}
    })
    assert emergency_path.endswith('.md')

@pytest.mark.asyncio
async def test_real_time_updates(agents):
    """Test real-time updates and monitoring between agents."""
    # Mock WebSurfer weather updates
    weather_updates = [
        {'temperature': 20, 'conditions': 'Clear'},
        {'temperature': 22, 'conditions': 'Cloudy'}
    ]
    agents['websurfer'].get_weather = AsyncMock(side_effect=weather_updates)
    
    # Create monitoring task
    monitor_task = {
        'type': 'monitor_weather',
        'data': {
            'location': 'Boston',
            'interval': 1  # 1 second for testing
        }
    }
    
    # Start monitoring through orchestrator
    monitor_result = await agents['orchestrator'].execute(monitor_task)
    assert monitor_result['status'] == 'success'
    
    # Verify weather updates were processed
    assert len(agents['orchestrator'].get_task_status('task_1')['updates']) == 2

@pytest.mark.asyncio
async def test_error_handling_and_recovery(agents):
    """Test error handling and recovery across agents."""
    # Mock WebSurfer to fail then succeed
    agents['websurfer'].research_destination = AsyncMock(side_effect=[
        Exception("API Error"),
        {'attractions': ['Success']}
    ])
    
    task = {
        'type': 'destination_research',
        'data': {
            'destination': 'Boston',
            'retry_on_failure': True
        }
    }
    
    result = await agents['orchestrator'].execute(task)
    assert result['status'] == 'success'
    
    # Verify error was handled and task recovered
    task_info = agents['orchestrator'].get_task_status('task_1')
    assert task_info['status'] == 'completed'
    assert len(task_info['error_history']) == 1
    assert task_info['metrics'].retries == 1

@pytest.mark.asyncio
async def test_parallel_agent_operations(agents):
    """Test parallel operations across multiple agents."""
    # Create multiple tasks
    tasks = [
        {
            'type': 'weather_info',
            'data': {'location': 'Boston'}
        },
        {
            'type': 'route_planning',
            'data': {
                'origin': 'Boston',
                'destination': 'New York'
            }
        },
        {
            'type': 'create_guide',
            'data': {
                'destination': 'Boston',
                'interests': ['history']
            }
        }
    ]
    
    # Execute tasks in parallel
    results = await agents['orchestrator'].execute_parallel(tasks)
    
    # Verify all tasks completed
    assert len(results) == 3
    assert all(r['status'] == 'success' for r in results)
    
    # Verify task metrics
    metrics = agents['orchestrator'].get_metrics()
    assert metrics['tasks_completed'] == 3
    assert metrics['tasks_failed'] == 0 