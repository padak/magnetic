"""Tests for trip management API endpoints."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from magnetic.api.main import app
from magnetic.models.trip import Trip, TripStatus
from magnetic.services.trip_planner import TripPlanner

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_db(mocker):
    """Mock database session."""
    session = MagicMock(spec=Session)
    mocker.patch("magnetic.database.get_db", return_value=session)
    return session

@pytest.fixture
def mock_trip_planner(mocker):
    """Mock TripPlanner."""
    planner = AsyncMock(spec=TripPlanner)
    mocker.patch("magnetic.api.routes.trips.get_trip_planner", return_value=planner)
    return planner

def test_create_trip(client, mock_db, mock_trip_planner):
    """Test trip creation endpoint."""
    # Mock research results
    mock_trip_planner.research_destination.return_value = {
        'destination': 'Test Location',
        'weather_forecast': {'main': {'temp': 20}},
        'location_details': {
            'results': [{
                'formatted_address': '123 Test St'
            }]
        },
        'available_activities': []
    }
    
    # Mock itinerary creation
    mock_trip_planner.create_itinerary.return_value = []
    
    # Mock budget calculation
    mock_trip_planner.calculate_budget.return_value = MagicMock(
        total=Decimal('1000'),
        spent=Decimal('0'),
        currency='USD',
        breakdown={
            'activities': Decimal('0'),
            'accommodations': Decimal('0')
        }
    )
    
    # Test data
    data = {
        'title': 'Test Trip',
        'description': 'A test trip',
        'destination': 'Test Location',
        'start_date': datetime.now().isoformat(),
        'end_date': (datetime.now() + timedelta(days=3)).isoformat(),
        'preferences': {
            'adults': 2,
            'children': 1,
            'hotel_budget': 'MODERATE',
            'max_activity_price': 100.0
        }
    }
    
    response = client.post("/trips/", json=data)
    assert response.status_code == 200
    assert response.json()['title'] == 'Test Trip'
    assert response.json()['status'] == 'PLANNING'

def test_list_trips(client, mock_db):
    """Test trip listing endpoint."""
    # Mock database query
    mock_db.query.return_value.count.return_value = 1
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
        MagicMock(
            id=1,
            title='Test Trip',
            description='A test trip',
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3),
            status=TripStatus.PLANNING,
            preferences={},
            itinerary_days=[],
            budget=None
        )
    ]
    
    response = client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 1
    assert len(data['trips']) == 1
    assert data['trips'][0]['title'] == 'Test Trip'

def test_get_trip(client, mock_db):
    """Test get trip endpoint."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        id=1,
        title='Test Trip',
        description='A test trip',
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=3),
        status=TripStatus.PLANNING,
        preferences={},
        itinerary_days=[],
        budget=None
    )
    
    response = client.get("/trips/1")
    assert response.status_code == 200
    assert response.json()['id'] == 1
    assert response.json()['title'] == 'Test Trip'

def test_get_trip_not_found(client, mock_db):
    """Test get trip endpoint with non-existent trip."""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    response = client.get("/trips/999")
    assert response.status_code == 404
    assert response.json()['detail'] == 'Trip 999 not found'

def test_update_trip(client, mock_db, mock_trip_planner):
    """Test trip update endpoint."""
    # Mock existing trip
    mock_trip = MagicMock(
        id=1,
        title='Test Trip',
        description='A test trip',
        destination='Test Location',
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=3),
        status=TripStatus.PLANNING,
        preferences={},
        itinerary_days=[],
        budget=None
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_trip
    
    # Mock research and planning
    mock_trip_planner.research_destination.return_value = {
        'destination': 'Test Location',
        'weather_forecast': {},
        'location_details': {'results': [{}]},
        'available_activities': []
    }
    mock_trip_planner.create_itinerary.return_value = []
    
    # Test data
    data = {
        'title': 'Updated Trip',
        'preferences': {
            'adults': 3,
            'children': 2
        }
    }
    
    response = client.patch("/trips/1", json=data)
    assert response.status_code == 200
    assert response.json()['title'] == 'Updated Trip'

def test_delete_trip(client, mock_db):
    """Test trip deletion endpoint."""
    # Mock existing trip
    mock_trip = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_trip
    
    response = client.delete("/trips/1")
    assert response.status_code == 204
    mock_db.delete.assert_called_once_with(mock_trip)
    mock_db.commit.assert_called_once()

def test_delete_trip_not_found(client, mock_db):
    """Test delete trip endpoint with non-existent trip."""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    response = client.delete("/trips/999")
    assert response.status_code == 404
    assert response.json()['detail'] == 'Trip 999 not found' 