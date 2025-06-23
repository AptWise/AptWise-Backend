"""
LinkedIn OAuth service for user authentication and profile management.
"""
import secrets
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import HTTPException, status
from ..config.linkedin_config import (
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    LINKEDIN_AUTHORIZATION_URL,
    LINKEDIN_TOKEN_URL,
    LINKEDIN_PROFILE_URL,
    LINKEDIN_EMAIL_URL,
    LINKEDIN_SCOPES
)


class LinkedInOAuthService:
    """Service class for LinkedIn OAuth operations."""
    
    def __init__(self):
        self.configured = bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)
        if not self.configured:
            print("WARNING: LinkedIn OAuth credentials not configured. LinkedIn features will be disabled.")
    
    def _check_configured(self):
        """Check if LinkedIn OAuth is properly configured."""
        if not self.configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LinkedIn OAuth is not configured on this server"
            )
    
    def generate_authorization_url(self) -> Dict[str, str]:
        """Generate LinkedIn OAuth authorization URL with state parameter."""
        self._check_configured()
        state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": LINKEDIN_CLIENT_ID,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "state": state,
            "scope": " ".join(LINKEDIN_SCOPES)
        }
        
        authorization_url = f"{LINKEDIN_AUTHORIZATION_URL}?{urlencode(params)}"
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        self._check_configured()
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINKEDIN_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get access token: {response.text}"
                )            
            return response.json()
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get user profile information from LinkedIn using newer API."""
        self._check_configured()
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            # Use the newer userinfo endpoint which works with 'profile' and 'email' scopes
            userinfo_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            
            if userinfo_response.status_code != 200:
                # Fallback to basic profile endpoint
                profile_response = await client.get(
                    "https://api.linkedin.com/v2/people/~:(id,localizedFirstName,localizedLastName)",
                    headers=headers
                )
                
                if profile_response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to get profile: {profile_response.text}"
                    )
                
                profile_data = profile_response.json()
                
                return {
                    "linkedin_id": profile_data.get("id"),
                    "email": None,  # Email not available with basic scope
                    "first_name": profile_data.get("localizedFirstName", ""),
                    "last_name": profile_data.get("localizedLastName", ""),
                    "profile_picture_url": None,
                    "full_name": f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}".strip()
                }
            
            # Parse userinfo response (contains email if available)
            userinfo_data = userinfo_response.json()
            
            return {
                "linkedin_id": userinfo_data.get("sub"),
                "email": userinfo_data.get("email"),
                "first_name": userinfo_data.get("given_name", ""),
                "last_name": userinfo_data.get("family_name", ""),
                "profile_picture_url": userinfo_data.get("picture"),
                "full_name": userinfo_data.get("name", f"{userinfo_data.get('given_name', '')} {userinfo_data.get('family_name', '')}").strip()
            }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get complete user information including profile and email."""
        return await self.get_user_profile(access_token)


# Create a singleton instance
linkedin_oauth_service = LinkedInOAuthService()
