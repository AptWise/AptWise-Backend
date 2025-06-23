"""
Debug 405 Method Not Allowed Error
"""
import asyncio
import httpx

async def test_all_endpoints():
    """Test all LinkedIn OAuth endpoints to find the 405 error."""
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        ("GET", "/auth/linkedin/authorize"),
        ("GET", "/auth/debug/linkedin"),
        ("POST", "/auth/linkedin/callback"),
        ("POST", "/auth/linkedin/connect"),
        ("POST", "/auth/linkedin/disconnect"),
        ("GET", "/auth/linkedin/profile"),
        ("GET", "/"),
        ("GET", "/docs"),
    ]
    
    print("🔍 Testing All Endpoints for 405 Errors")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        for method, endpoint in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{base_url}{endpoint}")
                elif method == "POST":
                    response = await client.post(
                        f"{base_url}{endpoint}",
                        json={"test": "data"}
                    )
                
                status = response.status_code
                if status == 405:
                    print(f"❌ {method} {endpoint} - 405 METHOD NOT ALLOWED")
                elif status < 400:
                    print(f"✅ {method} {endpoint} - {status} SUCCESS")
                else:
                    print(f"⚠️  {method} {endpoint} - {status} {response.reason_phrase}")
                    
            except Exception as e:
                print(f"💥 {method} {endpoint} - ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("💡 Common 405 Fixes:")
    print("1. Check if you're using the correct HTTP method")
    print("2. Verify the endpoint URL is exactly correct")
    print("3. Check if trailing slash is required")
    print("4. Make sure the server is running on the correct port")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
