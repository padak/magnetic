"""Tests for WebSurfer agent."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from magnetic.agents.websurfer import WebSurferAgent

class AsyncContextManagerMock(AsyncMock):
    """Mock class that supports async context manager protocol."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aenter_return = kwargs.get('return_value')

    async def __aenter__(self):
        return self.aenter_return

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

@pytest_asyncio.fixture
async def websurfer():
    """Create a WebSurfer agent for testing."""
    agent = WebSurferAgent()
    try:
        yield agent
    finally:
        await agent.cleanup()

@pytest.mark.asyncio
async def test_websurfer_initialization(websurfer):
    """Test WebSurfer agent initialization."""
    with patch('magnetic.agents.websurfer.async_playwright') as mock_playwright:
        # Mock browser setup
        mock_browser = AsyncMock()
        mock_playwright.return_value.start = AsyncMock()
        mock_playwright.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        await websurfer.initialize()
        
        assert websurfer.state['browser_ready'] is True
        assert websurfer.state['http_client_ready'] is True
        assert websurfer._browser is not None
        assert websurfer._http_client is not None

@pytest.mark.asyncio
async def test_web_scrape_task(websurfer):
    """Test web scraping functionality."""
    with patch('magnetic.agents.websurfer.async_playwright') as mock_playwright, \
         patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        # Mock browser and page
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Test Content")
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_page.goto = AsyncMock()

        # Create a new page mock that supports async context manager
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page

        # Set up the playwright mock
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)

        # Initialize the agent
        await websurfer.initialize()
        
        # Set the browser directly since we're testing the web scraping
        websurfer._browser = mock_browser

        task = {
            'type': 'web_scrape',
            'url': 'https://example.com',
            'selectors': {
                'title': 'h1',
                'description': '.description'
            }
        }

        result = await websurfer.execute(task)
        assert result['url'] == 'https://example.com'
        assert 'timestamp' in result
        assert 'data' in result
        assert result['data']['title'] == 'Test Content'
        assert result['data']['description'] == 'Test Content'

@pytest.mark.asyncio
async def test_weather_api_task(websurfer):
    """Test weather API functionality."""
    with patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        # Mock location API response
        location_response = AsyncMock()
        location_response.raise_for_status = AsyncMock()
        location_response.json = MagicMock(return_value={
            'results': [{
                'geometry': {
                    'location': {'lat': 37.7749, 'lng': -122.4194}
                }
            }]
        })
        
        # Mock weather API response
        weather_response = AsyncMock()
        weather_response.raise_for_status = AsyncMock()
        weather_response.json = MagicMock(return_value={
            'current': {'temperature_2m': 20},
            'daily': {'temperature_2m_max': [22], 'temperature_2m_min': [18]}
        })
        
        mock_client.return_value.get = AsyncMock(side_effect=[location_response, weather_response])
        
        await websurfer.initialize()
        
        task = {
            'type': 'weather_info',
            'location': 'San Francisco'
        }
        
        result = await websurfer.execute(task)
        
        assert result['location'] == 'San Francisco'
        assert 'timestamp' in result
        assert 'data' in result
        assert result['data']['current']['temperature_2m'] == 20

@pytest.mark.asyncio
async def test_location_api_task(websurfer):
    """Test location API functionality."""
    with patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            'results': [{
                'name': 'Test Location',
                'formatted_address': '123 Test St',
                'geometry': {
                    'location': {'lat': 37.7749, 'lng': -122.4194}
                }
            }]
        })
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        
        await websurfer.initialize()
        
        task = {
            'type': 'location_info',
            'location': 'Test Location'
        }
        
        result = await websurfer.execute(task)
        
        assert result['location'] == 'Test Location'
        assert 'timestamp' in result
        assert 'data' in result
        assert result['data']['results'][0]['name'] == 'Test Location'

@pytest.mark.asyncio
async def test_travel_api_task(websurfer):
    """Test travel API functionality."""
    with patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        # Mock auth response
        mock_auth_response = AsyncMock()
        mock_auth_response.raise_for_status = AsyncMock()
        mock_auth_response.json = MagicMock(return_value={'access_token': 'test_token'})
        
        # Mock API response
        mock_api_response = AsyncMock()
        mock_api_response.raise_for_status = AsyncMock()
        mock_api_response.json = MagicMock(return_value={
            'data': [{'type': 'flight-offer', 'id': '1'}]
        })
        
        mock_client.return_value.post = AsyncMock(return_value=mock_auth_response)
        mock_client.return_value.get = AsyncMock(return_value=mock_api_response)
        
        await websurfer.initialize()
        
        task = {
            'type': 'travel_search',
            'search_type': 'flights',
            'parameters': {
                'originLocationCode': 'SFO',
                'destinationLocationCode': 'LAX',
                'departureDate': '2025-05-01'  # Future date to avoid validation error
            }
        }
        
        result = await websurfer.execute(task)
        
        assert result['status'] == 'success'
        assert result['search_type'] == 'flights'
        assert 'data' in result

@pytest.mark.asyncio
async def test_invalid_task_type(websurfer):
    """Test handling of invalid task type."""
    await websurfer.initialize()
    
    task = {
        'type': 'invalid_type',
        'data': {}
    }
    
    with pytest.raises(ValueError) as exc_info:
        await websurfer.execute(task)
    assert "Unknown task type: invalid_type" in str(exc_info.value)

@pytest.mark.asyncio
async def test_cleanup(websurfer):
    """Test cleanup of resources."""
    await websurfer.initialize()
    assert websurfer._browser is not None
    assert websurfer._http_client is not None
    
    await websurfer.cleanup()
    assert websurfer._browser is None
    assert websurfer._http_client is None
    assert websurfer.state == {}

@pytest.mark.asyncio
async def test_route_planning(websurfer):
    """Test route planning functionality."""
    with patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        # Mock API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            'status': 'OK',
            'routes': [{
                'overview_polyline': {'points': 'test_polyline'},
                'bounds': {'northeast': {'lat': 1, 'lng': 1}, 'southwest': {'lat': 0, 'lng': 0}},
                'legs': [{
                    'distance': {'value': 1000},
                    'duration': {'value': 3600},
                    'duration_in_traffic': {'value': 4000},
                    'steps': [
                        {
                            'html_instructions': 'Take highway 101',
                            'start_location': {'lat': 0, 'lng': 0},
                            'end_location': {'lat': 1, 'lng': 1}
                        }
                    ]
                }],
                'warnings': ['This route has toll roads']
            }]
        })
        
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        
        await websurfer.initialize()
        
        task = {
            'type': 'route_planning',
            'origin': 'San Francisco, CA',
            'destination': 'Los Angeles, CA',
            'waypoints': ['Santa Barbara, CA'],
            'optimize': True,
            'mode': 'driving'
        }
        
        result = await websurfer.execute(task)
        
        assert result['status'] == 'success'
        assert result['origin'] == 'San Francisco, CA'
        assert result['destination'] == 'Los Angeles, CA'
        assert len(result['routes']) == 1
        
        route = result['routes'][0]
        assert route['overview_polyline'] == 'test_polyline'
        assert route['total_distance'] == 1000
        assert route['total_duration'] == 3600
        assert route['traffic_duration'] == 4000
        assert route['has_highways'] is True
        assert route['has_tolls'] is True
        assert len(route['key_points']) == 2
        
        # Check state update
        assert websurfer.state['route_optimizations'] == 1

@pytest.mark.asyncio
async def test_route_planning_missing_params(websurfer):
    """Test route planning with missing parameters."""
    await websurfer.initialize()
    
    task = {
        'type': 'route_planning',
        'origin': 'San Francisco, CA'
        # Missing destination
    }
    
    with pytest.raises(ValueError) as exc_info:
        await websurfer.execute(task)
    assert "Origin and destination are required" in str(exc_info.value)

@pytest.mark.asyncio
async def test_route_planning_api_error(websurfer):
    """Test route planning API error handling."""
    with patch('httpx.AsyncClient', return_value=AsyncMock()) as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            'status': 'ZERO_RESULTS'
        })
        
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        
        await websurfer.initialize()
        
        task = {
            'type': 'route_planning',
            'origin': 'Invalid Location',
            'destination': 'Another Invalid Location'
        }
        
        with pytest.raises(ValueError) as exc_info:
            await websurfer.execute(task)
        assert "Route planning failed: ZERO_RESULTS" in str(exc_info.value) 