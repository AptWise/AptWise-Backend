"""
GitHub OAuth service for user authentication and profile management.
"""
import secrets
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import HTTPException, status
from ..config.github_config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
    GITHUB_AUTHORIZATION_URL,
    GITHUB_TOKEN_URL,
    GITHUB_USER_URL,
    GITHUB_USER_EMAIL_URL,
    GITHUB_SCOPES
)


class GitHubOAuthService:
    """Service class for GitHub OAuth operations."""
    
    def __init__(self):
        self.configured = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
        if not self.configured:
            print("WARNING: GitHub OAuth credentials not configured. GitHub features will be disabled.")
    
    def _check_configured(self):
        """Check if GitHub OAuth is properly configured."""
        if not self.configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub OAuth is not configured on this server"
            )
    
    def generate_authorization_url(self) -> Dict[str, str]:
        """Generate GitHub OAuth authorization URL with state parameter."""
        self._check_configured()
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "scope": " ".join(GITHUB_SCOPES),
            "state": state,
            "allow_signup": "true"
        }
        
        authorization_url = f"{GITHUB_AUTHORIZATION_URL}?{urlencode(params)}"
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        self._check_configured()
        token_data = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data=token_data,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get access token: {response.text}"
                )
            
            return response.json()
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get user profile information from GitHub."""
        self._check_configured()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AptWise-Backend"
        }
        
        async with httpx.AsyncClient() as client:
            # Get user profile
            profile_response = await client.get(GITHUB_USER_URL, headers=headers)
            
            if profile_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get profile: {profile_response.text}"
                )
            
            profile_data = profile_response.json()
            
            # Get user email (GitHub might not provide email in profile if it's private)
            email = profile_data.get("email")
            if not email:
                # Try to get email from emails endpoint
                email_response = await client.get(GITHUB_USER_EMAIL_URL, headers=headers)
                if email_response.status_code == 200:
                    emails = email_response.json()
                    # Find primary email or first verified email
                    for email_info in emails:
                        if email_info.get("primary", False) and email_info.get("verified", False):
                            email = email_info.get("email")
                            break
                    # If no primary, get first verified email
                    if not email:
                        for email_info in emails:
                            if email_info.get("verified", False):
                                email = email_info.get("email")
                                break
            
            return {
                "github_id": str(profile_data.get("id")),
                "username": profile_data.get("login"),
                "email": email,
                "name": profile_data.get("name") or profile_data.get("login"),
                "avatar_url": profile_data.get("avatar_url"),
                "bio": profile_data.get("bio"),
                "company": profile_data.get("company"),
                "blog": profile_data.get("blog"),
                "location": profile_data.get("location"),
                "public_repos": profile_data.get("public_repos", 0),
                "followers": profile_data.get("followers", 0),
                "following": profile_data.get("following", 0),
                "github_url": profile_data.get("html_url")
            }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get complete user information including profile."""
        return await self.get_user_profile(access_token)


# Create a singleton instance
github_oauth_service = GitHubOAuthService()
