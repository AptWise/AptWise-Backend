"""
Test script for LinkedIn OAuth integration.
This script demonstrates how to test the LinkedIn OAuth endpoints.
"""
import asyncio
import httpx
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

async def test_linkedin_endpoints():
    """Test LinkedIn OAuth endpoints."""
    async with httpx.AsyncClient() as client:
        
        print("=" * 50)
        print("LinkedIn OAuth Integration Test")
        print("=" * 50)
        
        # Test 1: Get authorization URL (should fail without credentials)
        print("\n1. Testing Authorization URL endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/auth/linkedin/authorize")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Expected error (no credentials): {e}")
        
        # Test 2: Test callback endpoint (should fail without credentials)
        print("\n2. Testing Callback endpoint...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/linkedin/callback",
                json={"code": "test_code", "state": "test_state"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Expected error (no credentials): {e}")
        
        # Test 3: Test regular endpoints still work
        print("\n3. Testing regular endpoints...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"Root endpoint - Status Code: {response.status_code}")
            print(f"Root endpoint - Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 50)
        print("Test completed!")
        print("To enable LinkedIn OAuth:")
        print("1. Create a .env file with your LinkedIn app credentials")
        print("2. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET")
        print("3. Restart the server")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_linkedin_endpoints())
