"""
LinkedIn OAuth Scope Fix Guide

The error you encountered:
"Scope r_emailaddress is not authorized for your application"

This happens because LinkedIn restricts email access to certain applications.
"""

# SOLUTION 1: Update LinkedIn Developer App Settings
print("""
🔧 SOLUTION 1: Update your LinkedIn Developer App
============================================

1. Go to https://www.linkedin.com/developers/apps
2. Select your app
3. Go to "Auth" tab
4. In "OAuth 2.0 scopes" section, make sure these are enabled:
   ✅ r_liteprofile (Sign In with LinkedIn)
   ✅ r_emailaddress (if available - may require approval)

If r_emailaddress is not available, continue to Solution 2.
""")

# SOLUTION 2: Use OpenID Connect (Recommended)
print("""
🔧 SOLUTION 2: Use OpenID Connect Scopes (Recommended)
==================================================

LinkedIn now prefers OpenID Connect. Update your app to use:
- profile
- openid  
- email

These scopes are more widely available and don't require special approval.
""")

# SOLUTION 3: Alternative Implementation
print("""
🔧 SOLUTION 3: Fallback Implementation
===================================

If email access is not available, we can:
1. Get basic profile information
2. Ask user to provide email separately
3. Or use profile data without email
""")

import asyncio
import httpx

async def test_new_scopes():
    """Test the new LinkedIn OAuth configuration."""
    print("\n🧪 Testing New LinkedIn OAuth Configuration...")
    
    try:
        response = await httpx.AsyncClient().get("http://127.0.0.1:8000/auth/linkedin/authorize")
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_url = data.get("authorization_url", "")
            print(f"✅ New Authorization URL generated!")
            print(f"🔍 Check scopes in URL: {auth_url}")
            
            # Extract and show scopes
            if "scope=" in auth_url:
                scope_part = auth_url.split("scope=")[1].split("&")[0]
                from urllib.parse import unquote
                scopes = unquote(scope_part).split(" ")
                print(f"📋 Scopes being requested: {scopes}")
        else:
            print(f"❌ Error: {data}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_scopes())
