"""WebSurfer agent implementation for web scraping and API interactions."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import httpx
from playwright.async_api import async_playwright, Browser, Page
from amadeus import Client, ResponseError

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
        self._amadeus_client: Optional[Client] = None
        self.logger = get_logger(__name__)
        self.endpoints = {
            'amadeus': 'https://test.api.amadeus.com'
        }

    async def initialize(self) -> None:
        """Initialize browser and HTTP client."""
        await super().initialize()
        
        # Initialize state
        self.state.update({
            'browser_ready': False,
            'http_client_ready': False,
            'amadeus_ready': False,
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
            
            # Initialize Amadeus client
            self._amadeus_client = Client(
                client_id=self.config.api_keys["amadeus_key"],
                client_secret=self.config.api_keys["amadeus_secret"],
                hostname='test'  # Use test environment
            )
            self.state['amadeus_ready'] = True
            
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
        """Handle weather API requests using Open-Meteo.
        
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
        
        # First get coordinates using Google Maps API
        location_response = await self._handle_location_api({
            'type': 'location_info',
            'location': location
        })
        
        if not location_response.get('data', {}).get('results'):
            raise ValueError(f"Could not find location: {location}")
        
        # Extract coordinates
        location_data = location_response['data']['results'][0]
        coords = location_data['geometry']['location']
        
        # Get weather data from Open-Meteo
        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': coords['lat'],
            'longitude': coords['lng'],
            'current': ['temperature_2m', 'relative_humidity_2m', 'weather_code', 'wind_speed_10m'],
            'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'weather_code'],
            'temperature_unit': 'celsius',
            'wind_speed_unit': 'kmh',
            'timezone': 'auto'
        }
        
        response = await self._http_client.get(weather_url, params=params)
        response.raise_for_status()
        
        return {
            'location': location,
            'coordinates': coords,
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
        """Handle travel-related API requests using Amadeus SDK."""
        if not self._amadeus_client:
            raise RuntimeError("Amadeus client not initialized")

        search_type = task.get('search_type')
        if not search_type:
            raise ValueError("No search_type specified in travel API task")

        try:
            if search_type == 'hotels':
                # First search for hotels in the city
                city_code = task['parameters'].get('cityCode')
                if not city_code:
                    raise ValueError("No cityCode provided for hotel search")

                # Search hotels in city
                hotels_response = self._amadeus_client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code,
                    radius=task['parameters'].get('radius', 5),
                    radiusUnit=task['parameters'].get('radiusUnit', 'KM'),
                    amenities=task['parameters'].get('amenities', []),
                    ratings=task['parameters'].get('ratings', []),
                    hotelSource='ALL'
                )

                hotels = hotels_response.data
                if not hotels:
                    return {
                        'status': 'success',
                        'search_type': 'hotels',
                        'data': {'hotels': [], 'message': 'No hotels found in the specified city'}
                    }

                # Get hotel IDs (limit to first 10 to avoid too many requests)
                hotel_ids = [hotel['hotelId'] for hotel in hotels[:10]]

                # Search for offers for these hotels
                offers_response = self._amadeus_client.shopping.hotel_offers_search.get(
                    hotelIds=','.join(hotel_ids),
                    adults=str(task['parameters'].get('adults', 2)),
                    checkInDate=task['parameters']['checkInDate'],
                    checkOutDate=task['parameters']['checkOutDate'],
                    roomQuantity=str(task['parameters'].get('roomQuantity', 1)),
                    paymentPolicy=task['parameters'].get('paymentPolicy', 'NONE'),
                    bestRateOnly=True
                )

                return {
                    'status': 'success',
                    'search_type': 'hotels',
                    'data': {
                        'hotels': hotels,  # Original hotel list with details
                        'offers': offers_response.data,  # Available offers
                        'total_hotels_found': len(hotels),
                        'hotels_with_offers': len(offers_response.data),
                    }
                }

            elif search_type == 'flights':
                # Validate flight search parameters
                params = task.get('parameters', {})
                required_params = ['originLocationCode', 'destinationLocationCode', 'departureDate']
                if not all(param in params for param in required_params):
                    raise ValueError(f"Missing required flight parameters. Required: {required_params}")

                # Search for flights using the SDK
                flight_response = self._amadeus_client.shopping.flight_offers_search.get(
                    originLocationCode=params['originLocationCode'],
                    destinationLocationCode=params['destinationLocationCode'],
                    departureDate=params['departureDate'],
                    adults=params.get('adults', 1),
                    max=params.get('max', 10)
                )

                return {
                    'status': 'success',
                    'search_type': 'flights',
                    'data': flight_response.data
                }

            else:
                raise ValueError(f"Unknown search_type: {search_type}")

        except ResponseError as error:
            return {
                'status': 'error',
                'search_type': search_type,
                'error': {
                    'code': error.response.status_code,
                    'message': error.response.body
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'search_type': search_type,
                'error': {
                    'message': str(e)
                }
            } 