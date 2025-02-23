"""WebSurfer agent implementation using Magentic-One framework."""

from typing import Dict, List, Optional, Any
import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import logging
import json
import time
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import hashlib

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if not already added
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class Cache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _get_key(self, data: Any) -> str:
        """Generate a cache key from data."""
        if isinstance(data, (str, bytes)):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def get(self, key_data: Any) -> Optional[Any]:
        """Get value from cache if not expired."""
        key = self._get_key(key_data)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp <= self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key_data: Any, value: Any) -> None:
        """Set value in cache with current timestamp."""
        key = self._get_key(key_data)
        self.cache[key] = (value, time.time())

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 1):  # Reduced to 1 call per minute
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.min_interval = 60.0 / calls_per_minute  # Minimum time between calls
        
    async def acquire(self):
        """Acquire permission to make an API call."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if self.calls:
            # Ensure minimum interval between calls
            time_since_last_call = now - self.calls[-1]
            if time_since_last_call < self.min_interval:
                wait_time = self.min_interval - time_since_last_call
                logger.info(f"Rate limit: Waiting {wait_time:.2f} seconds between calls...")
                await asyncio.sleep(wait_time)
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until we can make another call
            wait_time = 60 - (now - self.calls[0])
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
        
        self.calls.append(time.time())  # Use current time after waiting

class WebSurferM1:
    """WebSurfer agent using Magentic-One framework."""
    
    def __init__(self) -> None:
        """Initialize the WebSurfer agent."""
        self.client = OpenAIChatCompletionClient(
            model="gpt-3.5-turbo-0125",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.code_executor = LocalCommandLineCodeExecutor()
        self.m1 = MagenticOne(
            client=self.client,
            code_executor=self.code_executor
        )
        self._browser = None
        self.rate_limiter = RateLimiter(calls_per_minute=1)  # More conservative rate limit
        self.cache = Cache(ttl_seconds=3600)  # Cache results for 1 hour
        
        # Initialize state
        self.state = {
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
        }
        
        logger.info("WebSurferM1 initialized")
        
    async def initialize(self) -> None:
        """Initialize resources."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch()
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Starting WebSurferM1 cleanup...")
        
        try:
            if self._browser:
                logger.debug("Closing browser...")
                try:
                    await self._browser.close()
                except Exception as e:
                    logger.error(f"Error closing browser: {e}")
                finally:
                    self._browser = None
            
            # Clean up any active tasks or operations
            tasks = []
            for task in asyncio.all_tasks():
                if task.get_name().startswith('websurfer_'):
                    tasks.append(task)
            
            if tasks:
                logger.debug(f"Cancelling {len(tasks)} active tasks...")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Reset state
            self.state = {
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
            }
            
            logger.info("WebSurferM1 cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during WebSurferM1 cleanup: {e}")
            raise
        
    async def web_scrape(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Scrape content from a webpage."""
        page = await self._browser.new_page()
        try:
            await page.goto(url)
            data = {}
            for key, selector in selectors.items():
                element = await page.query_selector(selector)
                if element:
                    data[key] = await element.text_content()
                else:
                    data[key] = None
            return {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
        finally:
            await page.close()
            
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location."""
        task = {
            'type': 'weather',
            'location': location,
            'required_info': ['current', 'forecast']
        }
        return await self.m1.run_stream(task=task)
        
    async def search_location(self, query: str) -> Dict[str, Any]:
        """Search for location information."""
        task = {
            'type': 'location_search',
            'query': query,
            'required_info': ['coordinates', 'address', 'points_of_interest']
        }
        return await self.m1.run_stream(task=task)
        
    async def search_travel(self, travel_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for travel options."""
        task = {
            'type': travel_type,
            'params': params,
            'required_info': ['options', 'prices', 'availability']
        }
        return await self.m1.run_stream(task=task)
        
    async def plan_route(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Plan a route between locations."""
        task = {
            'type': 'route_planning',
            'origin': origin,
            'destination': destination,
            'waypoints': waypoints or [],
            'preferences': preferences or {},
            'required_info': ['route', 'alternatives']
        }
        return await self.m1.run_stream(task=task)
        
    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=120),  # More conservative retry settings
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((Exception))
    )
    async def research_destination(
        self,
        destination: str,
        dates: Dict[str, datetime],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research a destination using M1 with rate limiting and retries."""
        logger.info(f"Researching destination: {destination}")
        logger.debug(f"Dates: {dates}, Preferences: {preferences}")
        
        # Check cache first
        cache_key = {
            'destination': destination,
            'dates': {k: v.isoformat() for k, v in dates.items()},
            'preferences': preferences
        }
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {destination}")
            self.state['cache_hits'] += 1
            return cached_result
        
        try:
            # Wait for rate limiter
            await self.rate_limiter.acquire()
            
            # Format task for M1
            task = {
                'type': 'destination_research',
                'destination': destination,
                'dates': {
                    'start_date': dates['start_date'].isoformat(),
                    'end_date': dates['end_date'].isoformat()
                },
                'preferences': preferences,
                'required_info': [
                    'attractions',
                    'weather',
                    'local_info',
                    'accommodations',
                    'transportation',
                    'activities',
                    'safety',
                    'budget'
                ]
            }
            
            # Process the async generator from run_stream
            result_chunks = []
            try:
                async for chunk in self.m1.run_stream(task=json.dumps(task)):
                    if isinstance(chunk, str):
                        result_chunks.append(chunk)
                    elif isinstance(chunk, dict):
                        result_chunks.append(json.dumps(chunk))
            except Exception as e:
                if "insufficient_quota" in str(e):
                    logger.warning("OpenAI quota exceeded, retrying after delay...")
                    raise  # This will trigger the retry decorator
                raise
            
            # Combine chunks and parse JSON
            result_str = ''.join(result_chunks)
            try:
                result = json.loads(result_str)
                logger.info(f"Research completed for {destination}")
                # Cache the successful result
                self.cache.set(cache_key, result)
                return result
            except json.JSONDecodeError as e:
                error_msg = f"Error parsing research results: {str(e)}"
                logger.error(error_msg)
                return {
                    'error': error_msg,
                    'raw_response': result_str
                }
            
        except Exception as e:
            error_msg = f"Error researching destination {destination}: {str(e)}"
            logger.error(error_msg)
            self.state['errors'].append(error_msg)
            raise

    async def generate_guide(self, destination: str, interests: List[str]) -> Dict[str, Any]:
        """Generate a travel guide for a destination."""
        try:
            # Use Magentic-One to generate guide content
            result = await self.m1.run_stream(task={
                'type': 'generate_guide',
                'destination': destination,
                'interests': interests
            })
            return result
        except Exception as e:
            return {
                'error': str(e)
            } 