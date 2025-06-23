"""
LinkedIn OAuth configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print what we're loading (remove in production)
print("Loading LinkedIn OAuth config...")
print(f"CLIENT_ID: {os.getenv('LINKEDIN_CLIENT_ID')}")
client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
print(f"CLIENT_SECRET: {'*' * len(client_secret) if client_secret else 'None'}")
print(f"REDIRECT_URI: {os.getenv('LINKEDIN_REDIRECT_URI')}")

# LinkedIn OAuth settings
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI",
                                  "http://localhost:8000/auth/linkedin/callback")

# LinkedIn OAuth endpoints
LINKEDIN_AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/people/~"
LINKEDIN_EMAIL_URL = ("https://api.linkedin.com/v2/emailAddresses"
                      "?q=members&projection=(elements*(handle~))")

# OAuth scopes - Updated to use available scopes
# Note: Using space-separated string format for LinkedIn OAuth
LINKEDIN_SCOPES = ["profile", "openid", "email"]
