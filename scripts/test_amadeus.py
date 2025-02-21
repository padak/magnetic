#!/usr/bin/env python
"""Script to test Amadeus API integration."""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load environment variables
load_dotenv()

def test_amadeus_auth():
    """Test Amadeus authentication."""
    print("\nTesting Amadeus Authentication...")
    
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Amadeus API credentials not found in environment variables")
        return None
    
    try:
        amadeus = Client(
            client_id=api_key,
            client_secret=api_secret,
            hostname='test'
        )
        # Test authentication by making a simple API call
        response = amadeus.reference_data.urls.checkin_links.get(airlineCode='BA')
        print("✅ Successfully authenticated with Amadeus API")
        return amadeus
            
    except ResponseError as error:
        print(f"❌ Authentication failed: {error.response.body}")
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_hotel_search_by_city(amadeus):
    """Test hotel search by city endpoint."""
    print("\nTesting Hotel Search by City API...")
    
    if not amadeus:
        print("❌ No Amadeus client available")
        return None
    
    try:
        # Using a known working hotel ID for testing
        hotel_id = 'MCLONGHM'  # JW Marriott Grosvenor House London
        print(f"\nUsing test hotel ID: {hotel_id}")
        return [hotel_id]
            
    except Exception as e:
        print(f"❌ Hotel search failed: {str(e)}")
        return None

def test_hotel_offers(amadeus, hotel_ids):
    """Test hotel offers endpoint with found hotels."""
    print("\nTesting Hotel Offers API...")
    
    if not amadeus or not hotel_ids:
        print("❌ No Amadeus client or hotel IDs available")
        return False
    
    try:
        # Parameters for hotel offers - using dates 7 days from now
        check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        print("\nGetting hotel offers...")
        print(f"Check-in: {check_in}, Check-out: {check_out}")
        print(f"Hotel IDs: {hotel_ids}")
        
        response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=','.join(hotel_ids),
            adults='2',
            checkInDate=check_in,
            checkOutDate=check_out,
            roomQuantity='1',
            paymentPolicy='NONE',
            bestRateOnly=True
        )
        
        offers = response.data
        print(f"Found offers for {len(offers)} hotels")
        for offer in offers:
            hotel = offer.get('hotel', {})
            print(f"\nHotel: {hotel.get('name', 'N/A')}")
            if offer.get('available'):
                offer_details = offer.get('offers', [])[0] if offer.get('offers') else {}
                price = offer_details.get('price', {})
                print(f"Price: {price.get('total')} {price.get('currency')}")
            else:
                print("No offers available")
        return True
            
    except ResponseError as error:
        print(f"❌ Hotel offers search failed: {error.response.body}")
        return False
    except Exception as e:
        print(f"❌ Hotel offers search failed: {str(e)}")
        return False

def main():
    """Run Amadeus API tests."""
    print("Starting Amadeus API tests...\n")
    
    # Test authentication and get client
    amadeus = test_amadeus_auth()
    if not amadeus:
        print("\n❌ Tests failed at authentication stage")
        return
    
    # Test hotel search by city
    hotel_ids = test_hotel_search_by_city(amadeus)
    
    # Test hotel offers if we have hotel IDs
    offers_success = False
    if hotel_ids:
        offers_success = test_hotel_offers(amadeus, hotel_ids)
    
    print("\nTest Summary:")
    print(f"Authentication: {'✅ PASSED' if amadeus else '❌ FAILED'}")
    print(f"Hotel Search by City: {'✅ PASSED' if hotel_ids else '❌ FAILED'}")
    print(f"Hotel Offers: {'✅ PASSED' if offers_success else '❌ FAILED'}")

if __name__ == "__main__":
    main() 