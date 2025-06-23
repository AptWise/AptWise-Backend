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
        """Get user profile information from LinkedIn."""
        self._check_configured()
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            # Get basic profile information
            profile_response = await client.get(
                LINKEDIN_PROFILE_URL + "?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))",
                headers=headers
            )
            
            if profile_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get profile: {profile_response.text}"
                )
            
            # Get email address
            email_response = await client.get(
                LINKEDIN_EMAIL_URL,
                headers=headers
            )
            
            if email_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get email: {email_response.text}"
                )
            
            profile_data = profile_response.json()
            email_data = email_response.json()
            
            # Extract email
            email = None
            if "elements" in email_data and len(email_data["elements"]) > 0:
                email = email_data["elements"][0]["handle~"]["emailAddress"]
            
            # Extract profile picture URL
            profile_picture_url = None
            if "profilePicture" in profile_data and "displayImage~" in profile_data["profilePicture"]:
                elements = profile_data["profilePicture"]["displayImage~"]["elements"]
                if elements:
                    # Get the largest image
                    profile_picture_url = elements[-1]["identifiers"][0]["identifier"]
            
            return {
                "linkedin_id": profile_data["id"],
                "email": email,
                "first_name": profile_data["firstName"]["localized"].get("en_US", ""),
                "last_name": profile_data["lastName"]["localized"].get("en_US", ""),
                "profile_picture_url": profile_picture_url,
                "full_name": f"{profile_data['firstName']['localized'].get('en_US', '')} {profile_data['lastName']['localized'].get('en_US', '')}".strip()
            }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get complete user information including profile and email."""
        return await self.get_user_profile(access_token)


# Create a singleton instance
linkedin_oauth_service = LinkedInOAuthService()
