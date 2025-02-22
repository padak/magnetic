"""WebSurfer agent implementation for web scraping and API interactions."""

import asyncio
from datetime import datetime, timezone
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
        """Initialize WebSurfer agent."""
        super().__init__(name, config)
        self._browser: Optional[Browser] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._amadeus_client: Optional[Client] = None
        self.logger = get_logger(__name__)
        self.endpoints = {
            'amadeus': 'https://test.api.amadeus.com',
            'maps': 'https://maps.googleapis.com/maps/api',
            'weather': 'https://api.open-meteo.com/v1'
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
            'errors': [],
            'route_optimizations': 0,
            'weather_alerts': [],
            'tracked_flights': set(),
            'hotel_recommendations': []
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
        """Execute a web surfing task."""
        await super().execute(task)
        
        task_type = task.get('type', '')
        self.state['last_request_time'] = datetime.now(timezone.utc).isoformat()
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
            elif task_type == 'route_planning':
                return await self._handle_route_planning(task)
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
            
        page = await self._browser.new_page()
        try:
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': results
            }
        finally:
            await page.close()

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
            'timestamp': datetime.now(timezone.utc).isoformat(),
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
            'timestamp': datetime.now(timezone.utc).isoformat(),
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

    async def _handle_route_planning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route planning and optimization tasks.
        
        Args:
            task: Task specification with route details
            
        Returns:
            Dict containing optimized route data
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")

        # Validate required parameters
        origin = task.get('origin')
        destination = task.get('destination')
        waypoints = task.get('waypoints', [])
        optimize = task.get('optimize', True)
        mode = task.get('mode', 'driving')
        departure_time = task.get('departure_time', 'now')
        
        if not origin or not destination:
            raise ValueError("Origin and destination are required for route planning")

        # Get Google Maps API key
        api_key = self.config.api_keys.get('maps')
        if not api_key:
            raise ValueError("Maps API key not configured")

        # Prepare waypoints string if any
        waypoints_str = ''
        if waypoints:
            if optimize:
                waypoints_str = f"optimize:true|{('|').join(waypoints)}"
            else:
                waypoints_str = f"{('|').join(waypoints)}"

        # Build request parameters
        params = {
            'origin': origin,
            'destination': destination,
            'mode': mode,
            'departure_time': departure_time,
            'alternatives': 'true',
            'key': api_key
        }
        
        if waypoints_str:
            params['waypoints'] = waypoints_str

        # Make request to Directions API
        url = f"{self.endpoints['maps']}/directions/json"
        response = await self._http_client.get(url, params=params)
        response.raise_for_status()
        routes_data = response.json()

        if routes_data.get('status') != 'OK':
            raise ValueError(f"Route planning failed: {routes_data.get('status')}")

        # Process and analyze routes
        routes = routes_data['routes']
        analyzed_routes = []
        
        for route in routes:
            # Calculate total distance and duration
            total_distance = sum(leg['distance']['value'] for leg in route['legs'])
            total_duration = sum(leg['duration']['value'] for leg in route['legs'])
            
            # Get traffic duration if available
            traffic_duration = None
            if 'duration_in_traffic' in route['legs'][0]:
                traffic_duration = sum(leg['duration_in_traffic']['value'] for leg in route['legs'])

            # Extract key points along the route
            key_points = []
            for leg in route['legs']:
                key_points.extend([
                    step['start_location'] for step in leg['steps']
                ])
                key_points.append(leg['steps'][-1]['end_location'])

            # Check for toll roads and highways
            has_tolls = any('toll road' in warning for warning in route.get('warnings', []))
            has_highways = any(
                any('highway' in step.get('html_instructions', '').lower() 
                    for step in leg['steps'])
                for leg in route['legs']
            )

            analyzed_routes.append({
                'overview_polyline': route['overview_polyline']['points'],
                'bounds': route['bounds'],
                'total_distance': total_distance,
                'total_duration': total_duration,
                'traffic_duration': traffic_duration,
                'key_points': key_points,
                'has_tolls': has_tolls,
                'has_highways': has_highways,
                'steps': [leg['steps'] for leg in route['legs']],
                'warnings': route.get('warnings', [])
            })

        # Sort routes by duration (considering traffic if available)
        analyzed_routes.sort(key=lambda x: x['traffic_duration'] if x['traffic_duration'] else x['total_duration'])

        # Update agent state
        self.state['route_optimizations'] += 1

        return {
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'origin': origin,
            'destination': destination,
            'waypoints': waypoints,
            'mode': mode,
            'routes': analyzed_routes,
            'optimized': optimize,
            'total_routes_found': len(analyzed_routes)
        } 