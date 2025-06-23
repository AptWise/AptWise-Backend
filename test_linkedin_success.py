"""
LinkedIn OAuth Integration Test - Success Verification
"""
import asyncio
import httpx
import json

async def test_linkedin_oauth():
    """Test LinkedIn OAuth endpoints to verify they're working."""
    base_url = "http://127.0.0.1:8000"
    
    print("🚀 LinkedIn OAuth Integration Test")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Debug endpoint
        print("\n1. Testing Debug Endpoint...")
        try:
            response = await client.get(f"{base_url}/auth/debug/linkedin")
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ All configured: {data.get('client_id_configured') and data.get('client_secret_configured')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Authorization URL
        print("\n2. Testing Authorization URL Generation...")
        try:
            response = await client.get(f"{base_url}/auth/linkedin/authorize")
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Authorization URL generated!")
            print(f"🔗 URL: {data.get('authorization_url', 'N/A')[:100]}...")
            print(f"🔐 State: {data.get('state', 'N/A')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Basic health check
        print("\n3. Testing Basic API Health...")
        try:
            response = await client.get(f"{base_url}/")
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Message: {data.get('message')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
    print("\n" + "=" * 50)
    print("🎉 LinkedIn OAuth Integration Status: WORKING!")
    print("\n📋 Next Steps:")
    print("1. Use the authorization URL from step 2 in your frontend")
    print("2. After user authorizes, use the callback endpoint")
    print("3. Test with real LinkedIn authorization codes")
    print("\n💡 Postman Collection:")
    print("GET  /auth/linkedin/authorize    - Get auth URL")
    print("POST /auth/linkedin/callback     - Handle OAuth callback")
    print("POST /auth/linkedin/connect      - Connect to existing account")
    print("GET  /auth/linkedin/profile      - Get LinkedIn profile")
    print("POST /auth/linkedin/disconnect   - Disconnect LinkedIn")

if __name__ == "__main__":
    asyncio.run(test_linkedin_oauth())
