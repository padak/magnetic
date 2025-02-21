#!/usr/bin/env python
"""Script to test API integrations."""

import os
import asyncio
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_amadeus_api():
    """Test Amadeus API integration."""
    print("\nTesting Amadeus API...")
    
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Amadeus API credentials not found in environment variables")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            # Get access token
            token_response = await client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret
                }
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            print("✅ Successfully obtained Amadeus access token")
            
            # Test flight search
            tomorrow = datetime.now() + timedelta(days=1)
            headers = {"Authorization": f"Bearer {access_token}"}
            flight_response = await client.get(
                "https://test.api.amadeus.com/v2/shopping/flight-offers",
                params={
                    "originLocationCode": "SFO",
                    "destinationLocationCode": "LAX",
                    "departureDate": tomorrow.strftime("%Y-%m-%d"),
                    "adults": 1
                },
                headers=headers
            )
            flight_response.raise_for_status()
            print("✅ Successfully tested flight search API")
            
            # Test hotel search
            hotel_response = await client.get(
                "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city",
                params={"cityCode": "LAX"},
                headers=headers
            )
            hotel_response.raise_for_status()
            print("✅ Successfully tested hotel search API")
            
            return True
            
    except Exception as e:
        print(f"❌ Amadeus API test failed: {str(e)}")
        return False

async def test_weather_api():
    """Test Open-Meteo Weather API integration."""
    print("\nTesting Open-Meteo Weather API...")
    
    try:
        async with httpx.AsyncClient() as client:
            # San Francisco coordinates
            lat = 37.7749
            lon = -122.4194
            
            # Test current weather
            print("Testing current weather data...")
            current_response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m"],
                    "temperature_unit": "celsius",
                    "wind_speed_unit": "kmh",
                    "timezone": "America/Los_Angeles"
                }
            )
            current_response.raise_for_status()
            current_data = current_response.json()
            
            if "current" in current_data:
                print("✅ Successfully retrieved current weather")
                print(f"   Temperature: {current_data['current']['temperature_2m']}°C")
                print(f"   Humidity: {current_data['current']['relative_humidity_2m']}%")
                print(f"   Wind Speed: {current_data['current']['wind_speed_10m']} km/h")
            
            # Test forecast
            print("\nTesting 7-day forecast...")
            forecast_response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code"],
                    "temperature_unit": "celsius",
                    "timezone": "America/Los_Angeles"
                }
            )
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            if "daily" in forecast_data:
                print("✅ Successfully retrieved 7-day forecast")
                print(f"   Forecast days: {len(forecast_data['daily']['time'])}")
                print(f"   Tomorrow's High: {forecast_data['daily']['temperature_2m_max'][1]}°C")
                print(f"   Tomorrow's Low: {forecast_data['daily']['temperature_2m_min'][1]}°C")
            
            return True
            
    except Exception as e:
        print(f"❌ Weather API test failed: {str(e)}")
        return False

async def test_maps_api():
    """Test Google Maps API integration."""
    print("\nTesting Google Maps API...")
    
    api_key = os.getenv("MAPS_API_KEY")
    
    if not api_key:
        print("❌ Maps API key not found in environment variables")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            # Test Geocoding API
            geocode_response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": "Golden Gate Bridge, San Francisco",
                    "key": api_key
                }
            )
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()
            
            if geocode_data["status"] == "OK":
                location = geocode_data["results"][0]["geometry"]["location"]
                print("✅ Successfully tested Geocoding API")
                print(f"   Location: {location['lat']}, {location['lng']}")
                
                # Test Places API with the coordinates
                places_response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params={
                        "location": f"{location['lat']},{location['lng']}",
                        "radius": "1000",
                        "type": "tourist_attraction",
                        "key": api_key
                    }
                )
                places_response.raise_for_status()
                places_data = places_response.json()
                
                if places_data["status"] == "OK":
                    print("✅ Successfully tested Places API")
                    print(f"   Found {len(places_data['results'])} nearby attractions")
                else:
                    print(f"❌ Places API returned status: {places_data['status']}")
                    
            else:
                print(f"❌ Geocoding API returned status: {geocode_data['status']}")
                
            return True
            
    except Exception as e:
        print(f"❌ Maps API test failed: {str(e)}")
        return False

async def main():
    """Run all API tests."""
    print("Starting API integration tests...\n")
    
    results = await asyncio.gather(
        test_amadeus_api(),
        test_weather_api(),
        test_maps_api()
    )
    
    print("\nTest Summary:")
    apis = ["Amadeus", "Open-Meteo Weather", "Google Maps"]
    for api, success in zip(apis, results):
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{api}: {status}")

if __name__ == "__main__":
    asyncio.run(main()) 