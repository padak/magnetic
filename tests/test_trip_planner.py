"""Tests for trip planning service."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from magnetic.services.trip_planner import TripPlanner
from magnetic.agents.websurfer import WebSurferAgent
from magnetic.models.trip import Trip, TripStatus

@pytest.fixture
def mock_websurfer():
    """Create a mock WebSurfer agent."""
    agent = AsyncMock(spec=WebSurferAgent)
    agent.execute = AsyncMock()
    return agent

@pytest.fixture
def trip_planner(mock_websurfer):
    """Create a TripPlanner instance with mock WebSurfer."""
    return TripPlanner(mock_websurfer)

@pytest.fixture
def sample_trip():
    """Create a sample trip for testing."""
    return Trip(
        id=1,
        title="Test Trip",
        description="A test family trip",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=3),
        status=TripStatus.PLANNING,
        preferences={
            'adults': 2,
            'children': 2,
            'hotel_budget': 'MODERATE',
            'max_activity_price': 100,
            'activity_types': ['SIGHTSEEING', 'FAMILY_FUN'],
            'family_friendly': True,
            'accessible': False,
            'transportation_budget': 500,
            'food_budget': 300,
            'misc_budget': 200
        }
    )

@pytest.mark.asyncio
async def test_research_destination(trip_planner, mock_websurfer):
    """Test destination research functionality."""
    # Mock API responses
    mock_websurfer.execute.side_effect = [
        # Weather API response
        {
            'data': {
                'main': {'temp': 20},
                'weather': [{'description': 'sunny'}]
            }
        },
        # Location API response
        {
            'data': {
                'results': [{
                    'name': 'Test Location',
                    'formatted_address': '123 Test St'
                }]
            }
        },
        # Activities API response
        {
            'data': [
                {
                    'name': 'Test Activity',
                    'type': 'SIGHTSEEING',
                    'price': 50,
                    'family_friendly': True
                }
            ]
        }
    ]
    
    travel_dates = {
        'start': datetime.now(),
        'end': datetime.now() + timedelta(days=3)
    }
    
    result = await trip_planner.research_destination(
        'Test Location',
        travel_dates,
        {'family_friendly': True}
    )
    
    assert result['destination'] == 'Test Location'
    assert 'weather_forecast' in result
    assert 'location_details' in result
    assert 'available_activities' in result
    assert mock_websurfer.execute.call_count == 3

@pytest.mark.asyncio
async def test_create_itinerary(trip_planner, mock_websurfer, sample_trip):
    """Test itinerary creation."""
    research_results = {
        'destination': 'Test Location',
        'weather_forecast': {'main': {'temp': 20}},
        'location_details': {
            'results': [{
                'formatted_address': '123 Test St'
            }]
        },
        'available_activities': [
            {
                'name': 'Morning Activity',
                'type': 'SIGHTSEEING',
                'price': 50,
                'duration': 120,
                'family_friendly': True
            },
            {
                'name': 'Afternoon Activity',
                'type': 'FAMILY_FUN',
                'price': 75,
                'duration': 180,
                'family_friendly': True
            }
        ]
    }
    
    # Mock hotel search response
    mock_websurfer.execute.return_value = {
        'data': [{
            'name': 'Test Hotel',
            'address': '456 Hotel St',
            'price': 200
        }]
    }
    
    itinerary = await trip_planner.create_itinerary(sample_trip, research_results)
    
    assert len(itinerary) == 4  # 3 days + arrival day
    assert all(day.trip_id == sample_trip.id for day in itinerary)
    
    # Check activities
    for day in itinerary:
        assert len(day.activities) > 0
        for activity in day.activities:
            assert activity.name in ['Morning Activity', 'Afternoon Activity']
            assert activity.cost in [Decimal('50'), Decimal('75')]
    
    # Check accommodations
    for day in itinerary[:-1]:  # All days except last should have accommodation
        assert day.accommodation is not None
        assert day.accommodation.name == 'Test Hotel'
        assert day.accommodation.cost == Decimal('200')

def test_schedule_activities(trip_planner):
    """Test activity scheduling logic."""
    date = datetime.now()
    available_activities = [
        {
            'name': 'Expensive Activity',
            'type': 'SIGHTSEEING',
            'price': 200,
            'family_friendly': True
        },
        {
            'name': 'Family Activity',
            'type': 'FAMILY_FUN',
            'price': 50,
            'family_friendly': True
        },
        {
            'name': 'Adult Activity',
            'type': 'NIGHTLIFE',
            'price': 75,
            'family_friendly': False
        }
    ]
    
    preferences = {
        'max_activity_price': 100,
        'activity_types': ['SIGHTSEEING', 'FAMILY_FUN'],
        'family_friendly': True
    }
    
    activities = trip_planner._schedule_activities(date, available_activities, preferences)
    
    assert len(activities) == 1
    assert activities[0].name == 'Family Activity'
    assert activities[0].cost == Decimal('50')

def test_matches_preferences(trip_planner):
    """Test preference matching logic."""
    preferences = {
        'max_activity_price': 100,
        'activity_types': ['SIGHTSEEING', 'FAMILY_FUN'],
        'family_friendly': True,
        'accessible': True
    }
    
    # Should match
    activity1 = {
        'type': 'SIGHTSEEING',
        'price': 50,
        'family_friendly': True,
        'accessible': True
    }
    assert trip_planner._matches_preferences(activity1, preferences)
    
    # Should not match (too expensive)
    activity2 = {
        'type': 'SIGHTSEEING',
        'price': 150,
        'family_friendly': True,
        'accessible': True
    }
    assert not trip_planner._matches_preferences(activity2, preferences)
    
    # Should not match (wrong type)
    activity3 = {
        'type': 'NIGHTLIFE',
        'price': 50,
        'family_friendly': True,
        'accessible': True
    }
    assert not trip_planner._matches_preferences(activity3, preferences)
    
    # Should not match (not family-friendly)
    activity4 = {
        'type': 'SIGHTSEEING',
        'price': 50,
        'family_friendly': False,
        'accessible': True
    }
    assert not trip_planner._matches_preferences(activity4, preferences)

def test_calculate_budget(trip_planner, sample_trip):
    """Test budget calculation."""
    from magnetic.models.trip import Activity, Accommodation, ItineraryDay
    
    # Create sample itinerary
    itinerary = [
        ItineraryDay(
            trip_id=sample_trip.id,
            date=sample_trip.start_date + timedelta(days=i),
            activities=[
                Activity(
                    name=f"Activity {j}",
                    cost=Decimal('50'),
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=2)
                ) for j in range(2)
            ],
            accommodation=Accommodation(
                name=f"Hotel {i}",
                address="Test Address",
                cost=Decimal('200'),
                check_in=datetime.now(),
                check_out=datetime.now() + timedelta(days=1)
            ) if i < 3 else None  # No accommodation on last day
        ) for i in range(4)
    ]
    
    budget = trip_planner.calculate_budget(sample_trip, itinerary)
    
    assert budget.trip_id == sample_trip.id
    assert budget.currency == 'USD'
    assert budget.breakdown['activities'] == Decimal('400')  # 8 activities * $50
    assert budget.breakdown['accommodations'] == Decimal('600')  # 3 nights * $200
    assert budget.breakdown['transportation'] == Decimal('500')
    assert budget.breakdown['food'] == Decimal('300')
    assert budget.breakdown['miscellaneous'] == Decimal('200')
    assert budget.total == Decimal('2000')  # Sum of all categories 