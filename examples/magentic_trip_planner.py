#!/usr/bin/env python
"""Example implementation of a trip planner using Magentic-One."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.ui import Console

# Load environment variables
load_dotenv()

class TripPlanner:
    """Trip planner using Magentic-One framework."""
    
    def __init__(self):
        """Initialize the trip planner with OpenAI client and MagenticOne instance."""
        self.client = OpenAIChatCompletionClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo-preview"
        )
        self.code_executor = LocalCommandLineCodeExecutor()
        self.m1 = MagenticOne(
            client=self.client,
            code_executor=self.code_executor
        )
    
    def _validate_dates(self, dates: Dict[str, datetime]) -> None:
        """Validate trip dates.
        
        Args:
            dates: Dictionary containing start_date and end_date
            
        Raises:
            ValueError: If dates are invalid
        """
        if not all(key in dates for key in ['start_date', 'end_date']):
            raise ValueError("Both start_date and end_date must be provided")
            
        if dates['end_date'] <= dates['start_date']:
            raise ValueError("End date must be after start date")
            
        if dates['start_date'] < datetime.now():
            raise ValueError("Start date cannot be in the past")
    
    def _format_preferences(self, preferences: Dict[str, str]) -> str:
        """Format preferences into a readable string.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            Formatted string of preferences
        """
        if not preferences:
            return "No specific preferences provided"
            
        formatted = []
        for key, value in preferences.items():
            formatted_key = key.replace('_', ' ').title()
            formatted.append(f"{formatted_key}: {value}")
        return "\n".join(formatted)
    
    async def plan_trip(
        self,
        destination: str,
        dates: Dict[str, datetime],
        preferences: Dict[str, str]
    ) -> Dict[str, Any]:
        """Plan a trip based on given parameters.
        
        Args:
            destination: Trip destination
            dates: Dictionary containing start_date and end_date
            preferences: Dictionary of user preferences
            
        Returns:
            Dictionary containing trip plan details
            
        Raises:
            ValueError: If input parameters are invalid
            Exception: If trip planning fails
        """
        # Validate dates
        self._validate_dates(dates)
        
        # Format preferences
        formatted_preferences = self._format_preferences(preferences)
        
        try:
            # Use Magentic-One to generate trip plan
            result = await self.m1.run_stream({
                'task': 'plan_trip',
                'destination': destination,
                'start_date': dates['start_date'].isoformat(),
                'end_date': dates['end_date'].isoformat(),
                'preferences': formatted_preferences
            })
            
            return result
        except Exception as e:
            raise Exception(f"Failed to plan trip: {str(e)}")

async def main():
    """Example usage of TripPlanner."""
    try:
        # Create planner instance
        planner = TripPlanner()
        
        # Example trip details
        destination = "Boston"
        dates = {
            'start_date': datetime.now() + timedelta(days=30),
            'end_date': datetime.now() + timedelta(days=35)
        }
        preferences = {
            'budget_range': "$2000-$3000",
            'accommodation_type': "Hotel",
            'travel_style': "Family-friendly",
            'interests': "History, Food, Culture"
        }
        
        # Generate trip plan
        plan = await planner.plan_trip(destination, dates, preferences)
        print("Trip Plan Generated:")
        print(plan)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Cleanup
        await planner.m1.client.close()

if __name__ == "__main__":
    asyncio.run(main()) 