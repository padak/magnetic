"""WebSurfer agent implementation for web scraping and API interactions."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import httpx
from playwright.async_api import async_playwright, Browser, Page

from .base import BaseAgent
from ..config.settings import config
from ..utils.logging import get_logger

class WebSurferAgent(BaseAgent):
    """Agent responsible for web scraping and API interactions."""

    def __init__(self, name: str = "WebSurfer", config: Optional[Dict[str, Any]] = None):
        """Initialize WebSurfer agent.
        
        Args:
            name: Agent name
            config: Optional configuration override
        """
        super().__init__(name, config)
        self._browser: Optional[Browser] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self.logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize browser and HTTP client."""
        await super().initialize()
        
        # Initialize state
        self.state.update({
            'browser_ready': False,
            'http_client_ready': False,
            'last_request_time': None,
            'requests_made': 0,
            'cache_hits': 0,
            'errors': []
        })
        
        try:
            # Initialize Playwright browser
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            self.state['browser_ready'] = True
            
            # Initialize HTTP client for API calls
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            self.state['http_client_ready'] = True
            
            self.logger.info("WebSurfer agent initialized successfully")
            
        except Exception as e:
            self.state['errors'].append(str(e))
            self.logger.error(f"Error initializing WebSurfer agent: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            
        await super().cleanup()

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a web surfing task.
        
        Args:
            task: Task specification containing type and parameters
            
        Returns:
            Dict containing task results
        """
        await super().execute(task)
        
        task_type = task.get('type', '')
        self.state['last_request_time'] = datetime.utcnow().isoformat()
        self.state['requests_made'] += 1
        
        try:
            if task_type == 'web_scrape':
                return await self._handle_web_scrape(task)
            elif task_type == 'weather_info':
                return await self._handle_weather_api(task)
            elif task_type == 'location_info':
                return await self._handle_location_api(task)
            elif task_type == 'travel_search':
                return await self._handle_travel_api(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            error_msg = f"Error executing task {task_type}: {str(e)}"
            self.state['errors'].append(error_msg)
            self.logger.error(error_msg)
            raise

    async def _handle_web_scrape(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web scraping tasks.
        
        Args:
            task: Task specification with URL and selectors
            
        Returns:
            Dict containing scraped data
        """
        if not self._browser:
            raise RuntimeError("Browser not initialized")
            
        url = task.get('url')
        selectors = task.get('selectors', {})
        
        if not url:
            raise ValueError("URL is required for web scraping")
            
        async with self._browser.new_page() as page:
            await page.goto(url, wait_until='networkidle')
            
            results = {}
            for key, selector in selectors.items():
                try:
                    element = await page.query_selector(selector)
                    if element:
                        results[key] = await element.text_content()
                except Exception as e:
                    self.logger.warning(f"Error extracting {key}: {e}")
                    results[key] = None
                    
            return {
                'url': url,
                'timestamp': datetime.utcnow().isoformat(),
                'data': results
            }

    async def _handle_weather_api(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather API requests.
        
        Args:
            task: Task specification with location
            
        Returns:
            Dict containing weather data
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")
            
        location = task.get('location')
        if not location:
            raise ValueError("Location is required for weather info")
            
        api_key = self.config.api_keys.get('weather')
        if not api_key:
            raise ValueError("Weather API key not configured")
            
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = await self._http_client.get(url, params=params)
        response.raise_for_status()
        
        return {
            'location': location,
            'timestamp': datetime.utcnow().isoformat(),
            'data': response.json()
        }

    async def _handle_location_api(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle location-based API requests.
        
        Args:
            task: Task specification with location details
            
        Returns:
            Dict containing location data
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")
            
        location = task.get('location')
        if not location:
            raise ValueError("Location is required")
            
        api_key = self.config.api_keys.get('maps')
        if not api_key:
            raise ValueError("Maps API key not configured")
            
        # Use Google Places API for location info
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': location,
            'key': api_key
        }
        
        response = await self._http_client.get(url, params=params)
        response.raise_for_status()
        
        return {
            'location': location,
            'timestamp': datetime.utcnow().isoformat(),
            'data': response.json()
        }

    async def _handle_travel_api(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle travel-related API requests.
        
        Args:
            task: Task specification with travel parameters
            
        Returns:
            Dict containing travel data
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")
            
        api_key = self.config.api_keys.get('amadeus')
        if not api_key:
            raise ValueError("Travel API key not configured")
            
        # Example using Amadeus API
        search_type = task.get('search_type')
        params = task.get('parameters', {})
        
        # Map search types to endpoints
        endpoints = {
            'flights': '/v1/shopping/flight-offers',
            'hotels': '/v2/shopping/hotel-offers',
            'activities': '/v1/shopping/activities'
        }
        
        if search_type not in endpoints:
            raise ValueError(f"Invalid search type: {search_type}")
            
        base_url = "https://test.api.amadeus.com"  # Use test endpoint for development
        endpoint = endpoints[search_type]
        
        # First, get access token
        auth_response = await self._http_client.post(
            f"{base_url}/v1/security/oauth2/token",
            data={
                'grant_type': 'client_credentials',
                'client_id': api_key,
                'client_secret': self.config.api_keys.get('amadeus_secret', '')
            }
        )
        auth_response.raise_for_status()
        access_token = auth_response.json()['access_token']
        
        # Make API request
        headers = {'Authorization': f'Bearer {access_token}'}
        response = await self._http_client.get(
            f"{base_url}{endpoint}",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        
        return {
            'search_type': search_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': response.json()
        } 