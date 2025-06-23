"""
GitHub OAuth configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print what we're loading (remove in production)
print(f"🔍 Loading GitHub OAuth config...")
print(f"CLIENT_ID: {os.getenv('GITHUB_CLIENT_ID')}")
print(f"CLIENT_SECRET: {'*' * len(os.getenv('GITHUB_CLIENT_SECRET', '')) if os.getenv('GITHUB_CLIENT_SECRET') else 'None'}")
print(f"REDIRECT_URI: {os.getenv('GITHUB_REDIRECT_URI')}")

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

# GitHub OAuth endpoints
GITHUB_AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_USER_EMAIL_URL = "https://api.github.com/user/emails"

# OAuth scopes - GitHub scopes for user profile and email access
GITHUB_SCOPES = ["user:email", "read:user"]
