"""
Test script to verify GitHub OAuth configuration and basic functionality.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.aptwise.config.github_config import (
    GITHUB_CLIENT_ID, 
    GITHUB_CLIENT_SECRET, 
    GITHUB_REDIRECT_URI,
    GITHUB_AUTHORIZATION_URL,
    GITHUB_TOKEN_URL,
    GITHUB_USER_URL,
    GITHUB_SCOPES
)
from src.aptwise.auth.github_service import github_oauth_service

def test_github_config():
    """Test GitHub OAuth configuration."""
    print("🔍 Testing GitHub OAuth Configuration...")
    
    print(f"CLIENT_ID configured: {bool(GITHUB_CLIENT_ID)}")
    print(f"CLIENT_SECRET configured: {bool(GITHUB_CLIENT_SECRET)}")
    print(f"REDIRECT_URI: {GITHUB_REDIRECT_URI}")
    print(f"AUTHORIZATION_URL: {GITHUB_AUTHORIZATION_URL}")
    print(f"TOKEN_URL: {GITHUB_TOKEN_URL}")
    print(f"USER_URL: {GITHUB_USER_URL}")
    print(f"SCOPES: {GITHUB_SCOPES}")
    
    print(f"\nService configured: {github_oauth_service.configured}")
    
    if github_oauth_service.configured:
        try:
            auth_data = github_oauth_service.generate_authorization_url()
            print(f"\n✅ Successfully generated authorization URL")
            print(f"State: {auth_data['state']}")
            print(f"Authorization URL: {auth_data['authorization_url'][:100]}...")
        except Exception as e:
            print(f"\n❌ Failed to generate authorization URL: {e}")
    else:
        print("\n⚠️  GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.")
        print("\nTo configure GitHub OAuth:")
        print("1. Go to https://github.com/settings/applications/new")
        print("2. Create a new OAuth App")
        print("3. Set Authorization callback URL to: http://localhost:8000/auth/github/callback")
        print("4. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in your .env file")

if __name__ == "__main__":
    test_github_config()
