"""Tests for WebSurfer agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from magnetic.agents.websurfer import WebSurferAgent

@pytest.fixture
async def websurfer():
    """Create a WebSurfer agent for testing."""
    agent = WebSurferAgent()
    yield agent
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
    with patch('magnetic.agents.websurfer.async_playwright') as mock_playwright:
        # Mock browser and page
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Test Content")
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_page.__aenter__ = AsyncMock(return_value=mock_page)
        mock_page.__aexit__ = AsyncMock()
        
        mock_browser = AsyncMock()
        mock_browser.new_page = MagicMock(return_value=mock_page)
        mock_playwright.return_value.start = AsyncMock()
        mock_playwright.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        await websurfer.initialize()
        
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
        assert result['data']['title'] == "Test Content"
        assert result['data']['description'] == "Test Content"

@pytest.mark.asyncio
async def test_weather_api_task(websurfer):
    """Test weather API functionality."""
    with patch('httpx.AsyncClient') as mock_client:
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            'main': {'temp': 20},
            'weather': [{'description': 'sunny'}]
        })
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        
        await websurfer.initialize()
        
        task = {
            'type': 'weather_info',
            'location': 'San Francisco'
        }
        
        result = await websurfer.execute(task)
        
        assert result['location'] == 'San Francisco'
        assert 'timestamp' in result
        assert 'data' in result
        assert result['data']['main']['temp'] == 20

@pytest.mark.asyncio
async def test_location_api_task(websurfer):
    """Test location API functionality."""
    with patch('httpx.AsyncClient') as mock_client:
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            'results': [{
                'name': 'Test Location',
                'formatted_address': '123 Test St'
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
    with patch('httpx.AsyncClient') as mock_client:
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
                'departureDate': '2024-05-01'
            }
        }
        
        result = await websurfer.execute(task)
        
        assert result['search_type'] == 'flights'
        assert 'timestamp' in result
        assert 'data' in result
        assert result['data']['data'][0]['type'] == 'flight-offer'

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