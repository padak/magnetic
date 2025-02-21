#!/usr/bin/env python
"""Script to test Docker environment setup."""

import asyncio
import httpx
import sys
import time
from typing import Dict, Any

async def test_api_health(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Test API health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")
        return response.json()

async def main():
    """Main test function."""
    print("Testing Docker environment...")
    
    # Wait for services to be ready
    retries = 5
    while retries > 0:
        try:
            result = await test_api_health()
            services = result["services"]
            
            if all(s == "healthy" for s in services.values()):
                print("\n✅ All services are healthy!")
                print("\nService Status:")
                for service, status in services.items():
                    print(f"- {service}: {status}")
                return 0
            
            print("\n⚠️ Some services are not healthy:")
            for service, status in services.items():
                print(f"- {service}: {status}")
            
        except Exception as e:
            print(f"\n⚠️ Error connecting to API: {e}")
        
        retries -= 1
        if retries > 0:
            print(f"\nRetrying in 5 seconds... ({retries} attempts remaining)")
            time.sleep(5)
    
    print("\n❌ Failed to connect to all services after multiple attempts")
    return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 