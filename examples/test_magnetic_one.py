#!/usr/bin/env python
"""Example script demonstrating Magnetic-One agent capabilities."""

import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_agentchat.ui import Console

# Load environment variables
load_dotenv()

# Check if OpenAI API key is set and has correct format
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not api_key.startswith("sk-"):
    raise ValueError("OPENAI_API_KEY should start with 'sk-'")

async def main():
    try:
        # Initialize OpenAI client with GPT-4 Turbo
        client = OpenAIChatCompletionClient(
            model="gpt-4-turbo-preview",
            api_key=api_key
        )

        # Create a MagenticOne instance
        m1 = MagenticOne(client=client)

        # Define the travel planning task
        task = """
Plan a family trip to Boston for summer 2024. Consider:
1. Activities suitable for both adults and children (museums, parks, historical sites)
2. Accommodation options in safe, family-friendly areas (preferably near public transport)
3. Transportation recommendations (including from airport)
4. Budget considerations and cost estimates for a 5-day trip
5. Suggested itinerary with daily activities
"""

        # Run the task with streaming output
        print("\nStarting Travel Planning Task...")
        await Console(m1.run_stream(task=task))
        print("\nTravel Planning Task Completed!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        # Cleanup
        await asyncio.sleep(1)  # Allow time for connections to close properly
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main()) 