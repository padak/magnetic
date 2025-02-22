"""Tests for Magentic-One WebSurfer implementation."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from magnetic.agents.websurfer_m1 import WebSurferM1

@pytest_asyncio.fixture
async def websurfer():
    """Create a WebSurfer instance for testing."""
    with patch('magnetic.agents.websurfer_m1.OpenAIChatCompletionClient') as mock_client_class:
        # Configure mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Create WebSurfer instance
        agent = WebSurferM1()
        await agent.initialize()
        try:
            yield agent
        finally:
            await agent.cleanup()

@pytest.mark.asyncio
async def test_web_scrape(websurfer):
    """Test web scraping functionality."""
    # Mock page and element
    mock_page = AsyncMock()
    mock_element = AsyncMock()
    mock_element.text_content = AsyncMock(return_value="Test Content")
    mock_page.query_selector = AsyncMock(return_value=mock_element)
    mock_page.goto = AsyncMock()
    
    # Mock browser new_page method
    websurfer._browser.new_page = AsyncMock(return_value=mock_page)
    
    result = await websurfer.web_scrape(
        url="https://example.com",
        selectors={
            'title': 'h1',
            'description': '.description'
        }
    )
    
    assert result['url'] == 'https://example.com'
    assert 'timestamp' in result
    assert result['data']['title'] == 'Test Content'
    assert result['data']['description'] == 'Test Content'

@pytest.mark.asyncio
async def test_get_weather(websurfer):
    """Test weather information retrieval."""
    # Mock Magentic-One response
    expected_result = {
        'current': {
            'temperature': 20,
            'conditions': 'Clear'
        },
        'forecast': [
            {'day': 1, 'temp': 22},
            {'day': 2, 'temp': 21}
        ]
    }
    mock_run_stream = AsyncMock(return_value=expected_result)
    websurfer.m1.run_stream = mock_run_stream
    
    result = await websurfer.get_weather("San Francisco")
    
    assert result == expected_result
    assert mock_run_stream.called
    task = mock_run_stream.call_args.args[0]
    assert task['type'] == 'weather'
    assert task['location'] == "San Francisco"
    assert 'current' in task['required_info']
    assert 'forecast' in task['required_info']

@pytest.mark.asyncio
async def test_search_location(websurfer):
    """Test location search functionality."""
    expected_result = {
        'coordinates': {'lat': 37.7749, 'lng': -122.4194},
        'address': '123 Test St, San Francisco, CA',
        'points_of_interest': ['Golden Gate Bridge', 'Fisherman\'s Wharf']
    }
    mock_run_stream = AsyncMock(return_value=expected_result)
    websurfer.m1.run_stream = mock_run_stream
    
    result = await websurfer.search_location("San Francisco landmarks")
    
    assert result == expected_result
    assert mock_run_stream.called
    task = mock_run_stream.call_args.args[0]
    assert task['type'] == 'location_search'
    assert task['query'] == "San Francisco landmarks"
    assert 'coordinates' in task['required_info']
    assert 'points_of_interest' in task['required_info']

@pytest.mark.asyncio
async def test_search_travel(websurfer):
    """Test travel search functionality."""
    params = {
        'origin': 'SFO',
        'destination': 'LAX',
        'date': '2025-03-01'
    }
    expected_result = {
        'flights': [
            {'airline': 'Test Air', 'price': 200},
            {'airline': 'Mock Air', 'price': 250}
        ]
    }
    mock_run_stream = AsyncMock(return_value=expected_result)
    websurfer.m1.run_stream = mock_run_stream
    
    result = await websurfer.search_travel("flights", params)
    
    assert result == expected_result
    assert mock_run_stream.called
    task = mock_run_stream.call_args.args[0]
    assert task['type'] == "flights"
    assert task['params'] == params
    assert 'options' in task['required_info']
    assert 'prices' in task['required_info']

@pytest.mark.asyncio
async def test_plan_route(websurfer):
    """Test route planning functionality."""
    expected_result = {
        'route': {
            'distance': '400 miles',
            'duration': '6 hours',
            'waypoints': ['Stop 1', 'Stop 2']
        },
        'alternatives': [
            {'distance': '450 miles', 'duration': '6.5 hours'}
        ]
    }
    mock_run_stream = AsyncMock(return_value=expected_result)
    websurfer.m1.run_stream = mock_run_stream
    
    result = await websurfer.plan_route(
        origin="San Francisco",
        destination="Los Angeles",
        waypoints=["Santa Barbara"],
        preferences={"avoid_tolls": True}
    )
    
    assert result == expected_result
    assert mock_run_stream.called
    task = mock_run_stream.call_args.args[0]
    assert task['type'] == 'route_planning'
    assert task['origin'] == "San Francisco"
    assert task['destination'] == "Los Angeles"
    assert "Santa Barbara" in task['waypoints']
    assert task['preferences'] == {"avoid_tolls": True}
    assert 'route' in task['required_info']
    assert 'alternatives' in task['required_info']

@pytest.mark.asyncio
async def test_research_destination(websurfer):
    """Test destination research functionality."""
    dates = {
        'arrival': '2025-03-01',
        'departure': '2025-03-05'
    }
    preferences = {
        'budget': 'medium',
        'interests': ['history', 'food']
    }
    expected_result = {
        'attractions': ['Museum', 'Restaurant'],
        'accommodations': ['Hotel 1', 'Hotel 2'],
        'transportation': ['Subway', 'Bus'],
        'weather': {'temperature': 20, 'conditions': 'Sunny'},
        'local_info': {'customs': ['Tip 15-20%'], 'safety': ['Safe area']}
    }
    mock_run_stream = AsyncMock(return_value=expected_result)
    websurfer.m1.run_stream = mock_run_stream
    
    result = await websurfer.research_destination(
        destination="Boston",
        dates=dates,
        preferences=preferences
    )
    
    assert result == expected_result
    assert mock_run_stream.called
    task = mock_run_stream.call_args.args[0]
    assert task['type'] == 'destination_research'
    assert task['destination'] == "Boston"
    assert task['dates'] == dates
    assert task['preferences'] == preferences
    assert 'attractions' in task['required_info']
    assert 'local_info' in task['required_info']

@pytest.mark.asyncio
async def test_cleanup(websurfer):
    """Test cleanup of resources."""
    await websurfer.cleanup()
    assert websurfer._browser is None 