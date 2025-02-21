"""Trip planning service implementation."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from decimal import Decimal

from ..agents.websurfer import WebSurferAgent
from ..models.trip import Trip, ItineraryDay, Activity, Accommodation, Budget, TripStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)

class TripPlanner:
    """Service for planning and managing trips."""
    
    def __init__(self, websurfer: WebSurferAgent):
        """Initialize trip planner.
        
        Args:
            websurfer: WebSurfer agent for data collection
        """
        self.websurfer = websurfer
        self.logger = logger
    
    async def research_destination(
        self,
        location: str,
        travel_dates: Dict[str, datetime],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research a destination for trip planning.
        
        Args:
            location: Destination location
            travel_dates: Start and end dates
            preferences: Trip preferences
            
        Returns:
            Dict containing destination research results
        """
        try:
            # Collect weather information
            weather_task = {
                'type': 'weather_info',
                'location': location
            }
            weather_info = await self.websurfer.execute(weather_task)
            
            # Collect location information
            location_task = {
                'type': 'location_info',
                'location': location
            }
            location_info = await self.websurfer.execute(location_task)
            
            # Search for activities
            activities_task = {
                'type': 'travel_search',
                'search_type': 'activities',
                'parameters': {
                    'location': location
                }
            }
            activities_info = await self.websurfer.execute(activities_task)
            
            # Search for hotels
            hotel_task = {
                'type': 'travel_search',
                'search_type': 'hotels',
                'parameters': {
                    'location': location,
                    'checkInDate': travel_dates['start'].strftime('%Y-%m-%d'),
                    'checkOutDate': travel_dates['end'].strftime('%Y-%m-%d'),
                    'adults': preferences.get('adults', 2)
                }
            }
            hotel_info = await self.websurfer.execute(hotel_task)
            
            return {
                'destination': location,
                'weather_forecast': weather_info.get('data', {}),
                'location_details': location_info.get('data', {}),
                'available_activities': activities_info.get('data', {}).get('results', []),
                'available_hotels': hotel_info.get('data', {}).get('data', []),
                'travel_dates': {
                    'start': travel_dates['start'].isoformat(),
                    'end': travel_dates['end'].isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error researching destination {location}: {e}")
            raise
    
    async def create_itinerary(
        self,
        trip: Trip,
        research_results: Dict[str, Any]
    ) -> List[ItineraryDay]:
        """Create a detailed itinerary for the trip.
        
        Args:
            trip: Trip model instance
            research_results: Results from destination research
            
        Returns:
            List of ItineraryDay instances
        """
        try:
            itinerary_days = []
            current_date = trip.start_date
            available_activities = research_results['available_activities']
            
            while current_date <= trip.end_date:
                # Create itinerary day
                day = ItineraryDay(
                    trip_id=trip.id,
                    date=current_date,
                    notes=f"Day {len(itinerary_days) + 1} of the trip"
                )
                
                # Schedule activities for the day
                day_activities = self._schedule_activities(
                    current_date,
                    available_activities,
                    trip.preferences
                )
                day.activities.extend(day_activities)
                
                # Find accommodation if not the last day
                if current_date < trip.end_date:
                    accommodation = await self._find_accommodation(
                        trip,
                        current_date,
                        research_results['location_details']
                    )
                    if accommodation:
                        day.accommodation = accommodation
                
                itinerary_days.append(day)
                current_date += timedelta(days=1)
            
            return itinerary_days
            
        except Exception as e:
            self.logger.error(f"Error creating itinerary for trip {trip.id}: {e}")
            raise
    
    def _schedule_activities(
        self,
        date: datetime,
        available_activities: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Activity]:
        """Schedule activities for a specific day.
        
        Args:
            date: Day to schedule for
            available_activities: List of available activities
            preferences: Trip preferences
            
        Returns:
            List of scheduled activities
        """
        activities = []
        current_time = datetime.combine(date.date(), datetime.min.time().replace(hour=9))  # Start at 9 AM
        
        # Filter activities based on preferences
        suitable_activities = [
            activity for activity in available_activities
            if self._matches_preferences(activity, preferences)
        ]
        
        # Schedule activities with appropriate time slots
        for activity_data in suitable_activities[:3]:  # Limit to 3 activities per day
            duration = timedelta(hours=2)  # Default duration
            if 'duration' in activity_data:
                duration = timedelta(minutes=activity_data['duration'])
            
            activity = Activity(
                name=activity_data['name'],
                description=activity_data.get('description', ''),
                start_time=current_time,
                end_time=current_time + duration,
                location=activity_data.get('location', ''),
                cost=Decimal(str(activity_data.get('price', 0))),
                booking_info=activity_data.get('booking', {})
            )
            
            activities.append(activity)
            current_time += duration + timedelta(minutes=30)  # Add 30-minute buffer
        
        return activities
    
    async def _find_accommodation(
        self,
        trip: Trip,
        date: datetime,
        location_details: Dict[str, Any]
    ) -> Optional[Accommodation]:
        """Find suitable accommodation for a specific date.
        
        Args:
            trip: Trip model instance
            date: Date to find accommodation for
            location_details: Location information
            
        Returns:
            Accommodation instance if found, None otherwise
        """
        try:
            # Search for hotels
            hotel_task = {
                'type': 'travel_search',
                'search_type': 'hotels',
                'parameters': {
                    'location': location_details['results'][0]['formatted_address'],
                    'checkInDate': date.strftime('%Y-%m-%d'),
                    'checkOutDate': (date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'adults': trip.preferences.get('adults', 2),
                    'priceRange': trip.preferences.get('hotel_budget', 'MODERATE')
                }
            }
            
            hotel_results = await self.websurfer.execute(hotel_task)
            
            if not hotel_results['data']:
                return None
            
            # Select best matching hotel
            hotel = hotel_results['data'][0]  # First result for now, could be improved
            
            return Accommodation(
                name=hotel['name'],
                address=hotel['address'],
                check_in=datetime.combine(date.date(), datetime.min.time().replace(hour=15)),  # 3 PM check-in
                check_out=datetime.combine((date + timedelta(days=1)).date(), datetime.min.time().replace(hour=11)),  # 11 AM check-out
                cost=Decimal(str(hotel.get('price', 0))),
                booking_info=hotel.get('booking', {})
            )
            
        except Exception as e:
            self.logger.error(f"Error finding accommodation for date {date}: {e}")
            return None
    
    def _matches_preferences(self, activity: Dict[str, Any], preferences: Dict[str, Any]) -> bool:
        """Check if an activity matches trip preferences.
        
        Args:
            activity: Activity data
            preferences: Trip preferences
            
        Returns:
            bool: True if activity matches preferences
        """
        # Check price range
        if 'max_activity_price' in preferences and activity.get('price', 0) > preferences['max_activity_price']:
            return False
        
        # Check activity type
        if 'activity_types' in preferences and activity.get('type') not in preferences['activity_types']:
            return False
        
        # Check family-friendly
        if preferences.get('family_friendly', True) and not activity.get('family_friendly', False):
            return False
        
        # Check accessibility
        if preferences.get('accessible', False) and not activity.get('accessible', False):
            return False
        
        return True
    
    def calculate_budget(self, trip: Trip, itinerary: List[ItineraryDay]) -> Budget:
        """Calculate trip budget based on itinerary.
        
        Args:
            trip: Trip model instance
            itinerary: List of itinerary days
            
        Returns:
            Budget instance with detailed breakdown
        """
        total = Decimal('0')
        activities_cost = Decimal('0')
        accommodations_cost = Decimal('0')
        transportation_cost = Decimal(str(trip.preferences.get('transportation_budget', 0)))
        food_cost = Decimal(str(trip.preferences.get('food_budget', 0)))
        misc_cost = Decimal(str(trip.preferences.get('misc_budget', 0)))
        
        # Calculate costs from itinerary
        for day in itinerary:
            # Activities
            for activity in day.activities:
                activities_cost += activity.cost
            
            # Accommodation
            if day.accommodation:
                accommodations_cost += day.accommodation.cost
        
        # Calculate total
        total = activities_cost + accommodations_cost + transportation_cost + food_cost + misc_cost
        
        # Convert Decimal values to strings for JSON serialization
        breakdown = {
            'activities': str(activities_cost),
            'accommodations': str(accommodations_cost),
            'transportation': str(transportation_cost),
            'food': str(food_cost),
            'miscellaneous': str(misc_cost)
        }
        
        return Budget(
            trip_id=trip.id,
            total=total,
            spent=Decimal('0'),
            currency=trip.preferences.get('currency', 'USD'),
            breakdown=breakdown
        ) 