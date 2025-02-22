"""Tests for Magentic-One trip planner implementation."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from examples.magentic_trip_planner import TripPlanner

@pytest_asyncio.fixture
async def planner():
    """Create a TripPlanner instance for testing."""
    with patch('autogen_ext.models.openai.OpenAIChatCompletionClient') as mock_client:
        # Mock the client
        mock_client.return_value = AsyncMock()
        
        # Create planner
        planner = TripPlanner()
        yield planner

@pytest.mark.asyncio
async def test_plan_trip_basic(planner):
    """Test basic trip planning functionality."""
    # Setup test data
    destination = "Boston"
    dates = {
        'start_date': datetime.now() + timedelta(days=30),
        'end_date': datetime.now() + timedelta(days=35)
    }
    preferences = {
        'budget_range': "$2000-$3000",
        'accommodation_type': "Hotel"
    }
    
    # Mock the Magentic-One run_stream method
    planner.m1.run_stream = AsyncMock(return_value={
        'itinerary': ['Day 1: Arrival and check-in'],
        'accommodation': ['Hotel recommendations'],
        'transportation': ['Transport options'],
        'budget': {'total': 2500}
    })
    
    # Execute trip planning
    result = await planner.plan_trip(destination, dates, preferences)
    
    # Verify the result
    assert result is not None
    assert 'itinerary' in result
    assert 'accommodation' in result
    assert 'transportation' in result
    assert 'budget' in result

@pytest.mark.asyncio
async def test_plan_trip_error_handling(planner):
    """Test error handling in trip planning."""
    # Setup test data
    destination = "Boston"
    dates = {
        'start_date': datetime.now() + timedelta(days=30),
        'end_date': datetime.now() + timedelta(days=35)
    }
    preferences = {}
    
    # Mock the Magentic-One run_stream method to raise an exception
    planner.m1.run_stream = AsyncMock(side_effect=Exception("API Error"))
    
    # Verify error handling
    with pytest.raises(Exception) as exc_info:
        await planner.plan_trip(destination, dates, preferences)
    assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_preference_formatting(planner):
    """Test preference formatting."""
    preferences = {
        'budget_range': "$2000-$3000",
        'accommodation_type': "Hotel",
        'travel_style': "Family-friendly"
    }
    
    formatted = planner._format_preferences(preferences)
    
    # Verify formatting
    assert "Budget Range: $2000-$3000" in formatted
    assert "Accommodation Type: Hotel" in formatted
    assert "Travel Style: Family-friendly" in formatted

@pytest.mark.asyncio
async def test_date_handling(planner):
    """Test date handling in trip planning."""
    # Setup test data with invalid dates
    destination = "Boston"
    dates = {
        'start_date': datetime.now() + timedelta(days=30),
        'end_date': datetime.now() + timedelta(days=25)  # End before start
    }
    preferences = {}
    
    # Mock the Magentic-One run_stream method
    planner.m1.run_stream = AsyncMock(return_value={})
    
    # Verify date handling
    with pytest.raises(Exception):
        await planner.plan_trip(destination, dates, preferences) 