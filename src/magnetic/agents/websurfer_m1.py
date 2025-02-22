"""WebSurfer agent implementation using Magentic-One framework."""

from typing import Dict, List, Optional, Any
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

class WebSurferM1:
    """WebSurfer agent using Magentic-One framework."""
    
    def __init__(self) -> None:
        """Initialize the WebSurfer agent."""
        self.client = OpenAIChatCompletionClient(
            model="gpt-4-turbo-preview",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.code_executor = LocalCommandLineCodeExecutor()
        self.m1 = MagenticOne(
            client=self.client,
            code_executor=self.code_executor
        )
        self._browser = None
        
    async def initialize(self) -> None:
        """Initialize resources."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch()
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        # OpenAIChatCompletionClient doesn't have a close method
        
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
        return await self.m1.run_stream(task)
        
    async def search_location(self, query: str) -> Dict[str, Any]:
        """Search for location information."""
        task = {
            'type': 'location_search',
            'query': query,
            'required_info': ['coordinates', 'address', 'points_of_interest']
        }
        return await self.m1.run_stream(task)
        
    async def search_travel(self, travel_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for travel options."""
        task = {
            'type': travel_type,
            'params': params,
            'required_info': ['options', 'prices', 'availability']
        }
        return await self.m1.run_stream(task)
        
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
        return await self.m1.run_stream(task)
        
    async def research_destination(
        self,
        destination: str,
        dates: Dict[str, str],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research a travel destination."""
        task = {
            'type': 'destination_research',
            'destination': destination,
            'dates': dates,
            'preferences': preferences,
            'required_info': ['attractions', 'accommodations', 'transportation', 'weather', 'local_info']
        }
        return await self.m1.run_stream(task) 