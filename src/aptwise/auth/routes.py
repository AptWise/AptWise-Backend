"""
Authentication routes for user registration, login, and logout.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Response, status
from fastapi.responses import RedirectResponse
from .models import (UserCreate, UserLogin, UserResponse,
                     LinkedInAuthRequest, GitHubAuthRequest,
                     UserProfileUpdate, PasswordUpdate,
                     SkillAdd, SkillRemove, UserInterviewCreate,
                     UserInterviewResponse)
from .utils import (create_access_token, set_access_cookies,
                    unset_jwt_cookies, get_current_user,
                    hash_password, verify_password)
from ..database import (get_user_by_email, create_user, delete_user,
                        get_user_by_linkedin_id, create_user_with_linkedin,
                        update_user_linkedin_connection,
                        disconnect_user_linkedin,
                        get_user_by_github_id, create_user_with_github,
                        update_user_github_connection,
                        disconnect_user_github, create_user_skills,
                        delete_all_user_skills, get_user_skills,
                        update_user_profile, add_user_skill, remove_user_skill,
                        create_user_interview, get_user_interviews,
                        get_user_interview_by_id, delete_user_interview)
from .linkedin_service import linkedin_oauth_service
from .github_service import github_oauth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/create-account", response_model=UserResponse)
async def create_account(user_data: UserCreate, response: Response):
    """Create a new user account with optional OAuth data."""
    # Check if email already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400,
                            detail="Email already registered")

    # Handle password for OAuth-only users
    password_to_hash = user_data.password
    if user_data.is_oauth_only and not password_to_hash:
        # Generate a secure random password for OAuth-only users
        # They won't need this password as they'll login via OAuth
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password_to_hash = ''.join(secrets.choice(alphabet) for i in range(32))
    elif not password_to_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required for non-OAuth registration"
        )

    # Hash the password
    hashed_password = hash_password(password_to_hash)

    # Create new user record with OAuth data if provided
    new_user = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "linkedin_url": user_data.linkedin_url,
        "github_url": user_data.github_url,
        # OAuth fields
        "linkedin_id": user_data.linkedin_id,
        "linkedin_access_token": user_data.linkedin_access_token,
        "github_id": user_data.github_id,
        "github_access_token": user_data.github_access_token,
        "profile_picture_url": user_data.profile_picture_url,
        "is_linkedin_connected": bool(user_data.linkedin_id),
        "is_github_connected": bool(user_data.github_id)
    }

    # Add user to database
    success = create_user(new_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    # Create user skills if provided
    if user_data.skills:
        skills_success = create_user_skills(user_data.email, user_data.skills)
        if not skills_success:
            # If skills creation fails, we could either:
            # 1. Continue without skills (current approach)
            # 2. Delete the user and raise an error
            print(f"Warning: \
                  Failed to create skills for user {user_data.email}")

    # Create access token with JWT
    access_token = create_access_token(data={"sub": user_data.email})
    set_access_cookies(response, access_token)

    # Return user data (without password and access tokens)
    return {
        "name": new_user["name"],
        "email": new_user["email"],
        "linkedin_url": new_user["linkedin_url"],
        "github_url": new_user["github_url"],
        "linkedin_id": new_user["linkedin_id"],
        "github_id": new_user["github_id"],
        "profile_picture_url": new_user["profile_picture_url"],
        "is_linkedin_connected": new_user["is_linkedin_connected"],
        "is_github_connected": new_user["is_github_connected"]
    }


@router.post("/login")
async def login(user_data: UserLogin, response: Response):
    """Authenticate a user."""
    hashed_password = hash_password(user_data.password)
    # Try to find user in database
    user = get_user_by_email(user_data.email)

    if user and user["password"] == hashed_password:
        # Create access token with JWT
        access_token = create_access_token(
            data={"sub": user_data.email}
        )
        # Set the JWT cookies
        set_access_cookies(response, access_token)
        return {"status": "success", "message": "Login successful"}

    raise HTTPException(
        status_code=401, detail="Invalid email or password"
    )


@router.post("/logout")
async def logout(response: Response):
    """Log out a user by clearing the JWT cookie."""
    unset_jwt_cookies(response)
    return {"status": "success", "message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get current user information."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Find user in database
    db_user = get_user_by_email(current_user)
    if db_user:
        return {
            "name": db_user["name"],
            "email": db_user["email"],
            "linkedin_url": db_user["linkedin_url"],
            "github_url": db_user["github_url"],
            "linkedin_id": db_user.get("linkedin_id"),
            "github_id": db_user.get("github_id"),
            "profile_picture_url": db_user.get("profile_picture_url"),
            "is_linkedin_connected": db_user.get(
                "is_linkedin_connected", False
            ),
            "is_github_connected": db_user.get(
                "is_github_connected", False
            )
        }

    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/delete-account")
async def delete_account(
    response: Response,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Delete a user account."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    # Delete user skills first
    delete_all_user_skills(current_user)

    # Delete from database
    db_success = delete_user(current_user)

    if db_success:
        unset_jwt_cookies(response)  # Log the user out
        return {
            "status": "success",
            "message": "Account deleted successfully"
        }

    # If we couldn't delete the user,
    # it might not exist or there was a database error
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not delete user account"
    )


# Debug endpoint to check LinkedIn configuration
@router.get("/debug/linkedin")
async def debug_linkedin_config():
    """Debug LinkedIn OAuth configuration - REMOVE IN PRODUCTION."""
    from ..config.linkedin_config import (
        LINKEDIN_CLIENT_ID,
        LINKEDIN_CLIENT_SECRET,
        LINKEDIN_REDIRECT_URI
    )

    return {
        "client_id_configured": bool(LINKEDIN_CLIENT_ID),
        "client_secret_configured": bool(LINKEDIN_CLIENT_SECRET),
        "redirect_uri_configured": bool(LINKEDIN_REDIRECT_URI),
        "client_id_value": LINKEDIN_CLIENT_ID,  # Remove in production
        "redirect_uri_value": LINKEDIN_REDIRECT_URI,
        "service_configured": (
            linkedin_oauth_service.configured
            if hasattr(linkedin_oauth_service, 'configured')
            else "Unknown"
        )
    }


# LinkedIn OAuth routes
@router.get("/linkedin/authorize")
async def linkedin_authorize():
    """Generate LinkedIn OAuth authorization URL."""
    try:
        auth_data = linkedin_oauth_service.generate_authorization_url()
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Failed to generate LinkedIn authorization URL: {str(e)}"
            )
        )


@router.get("/linkedin/callback")
async def linkedin_redirect_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Handle LinkedIn OAuth redirect and forward to frontend callback."""
    frontend_callback_url = "http://localhost:5174/auth/linkedin/callback"

    if error:
        # Redirect to frontend with error
        redirect_url = (
            f"{frontend_callback_url}?error={error}"
            f"&error_description={error_description or ''}"
        )
    elif code and state:
        # Redirect to frontend with auth code
        redirect_url = f"{frontend_callback_url}?code={code}&state={state}"
    else:
        # Redirect to frontend with generic error
        redirect_url = (
            f"{frontend_callback_url}?error=invalid_request"
            "&error_description=Missing required parameters"
        )

    return RedirectResponse(url=redirect_url)


@router.post("/linkedin/callback")
async def linkedin_callback(
    auth_request: LinkedInAuthRequest, response: Response
):
    """Handle LinkedIn OAuth callback and create/login user."""
    try:        # Exchange code for access token
        token_data = await linkedin_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from LinkedIn
        linkedin_profile = await linkedin_oauth_service.get_user_info(
            access_token
        )

        if not linkedin_profile.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from LinkedIn profile"
            )

        # Check if user exists by email
        existing_user = get_user_by_email(linkedin_profile["email"])

        if existing_user:
            # Update existing user with LinkedIn connection
            linkedin_data = {
                "linkedin_id": linkedin_profile["linkedin_id"],
                "linkedin_access_token": access_token,
                "profile_picture_url": linkedin_profile.get(
                    "profile_picture_url"
                )
            }

            success = update_user_linkedin_connection(
                linkedin_profile["email"], linkedin_data
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to update LinkedIn connection"
                )
        else:
            # Check if LinkedIn ID is already connected to another account
            linkedin_user = get_user_by_linkedin_id(
                linkedin_profile["linkedin_id"]
            )
            if linkedin_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This LinkedIn account is already connected to "
                        "another user"
                    )
                )

            # Create new user with LinkedIn data
            new_user_data = {
                "name": linkedin_profile["full_name"],
                "email": linkedin_profile["email"],
                "linkedin_id": linkedin_profile["linkedin_id"],
                "linkedin_access_token": access_token,
                "profile_picture_url": linkedin_profile.get(
                    "profile_picture_url"
                )
            }

            success = create_user_with_linkedin(new_user_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to create user account"
                )

        # Create JWT token for the user
        jwt_token = create_access_token(
            data={"sub": linkedin_profile["email"]}
        )
        set_access_cookies(response, jwt_token)

        return {
            "status": "success",
            "message": "LinkedIn authentication successful",
            "user": {
                "name": linkedin_profile["full_name"],
                "email": linkedin_profile["email"],
                "linkedin_id": linkedin_profile["linkedin_id"],
                "profile_picture_url": linkedin_profile.get(
                    "profile_picture_url"
                ),
                "is_linkedin_connected": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LinkedIn authentication failed: {str(e)}"
        )


@router.post("/linkedin/connect")
async def connect_linkedin(
    auth_request: LinkedInAuthRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Connect LinkedIn account to existing authenticated user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Exchange code for access token
        token_data = await linkedin_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from LinkedIn
        linkedin_profile = await linkedin_oauth_service.get_user_info(
            access_token
        )

        # Check if LinkedIn ID is already connected to another account
        linkedin_user = get_user_by_linkedin_id(
            linkedin_profile["linkedin_id"]
        )
        if linkedin_user and linkedin_user["email"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This LinkedIn account is already connected to "
                    "another user"
                )
            )

        # Update user with LinkedIn connection
        linkedin_data = {
            "linkedin_id": linkedin_profile["linkedin_id"],
            "linkedin_access_token": access_token,
            "profile_picture_url": linkedin_profile.get(
                "profile_picture_url"
            )
        }

        success = update_user_linkedin_connection(current_user, linkedin_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect LinkedIn account"
            )

        return {
            "status": "success",
            "message": "LinkedIn account connected successfully",
            "linkedin_profile": {
                "linkedin_id": linkedin_profile["linkedin_id"],
                "profile_picture_url": linkedin_profile.get(
                    "profile_picture_url"
                )
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect LinkedIn account: {str(e)}"
        )


@router.post("/linkedin/disconnect")
async def disconnect_linkedin(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Disconnect LinkedIn account from current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        success = disconnect_user_linkedin(current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to disconnect LinkedIn account"
            )

        return {
            "status": "success",
            "message": "LinkedIn account disconnected successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect LinkedIn account: {str(e)}"
        )


@router.get("/linkedin/profile")
async def get_linkedin_profile(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get LinkedIn profile information for the current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Get user from database
        db_user = get_user_by_email(current_user)
        if not db_user or not db_user.get("is_linkedin_connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected"
            )

        # Check if we have a valid access token
        access_token = db_user.get("linkedin_access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn access token not available"
            )

        # Fetch fresh profile data from LinkedIn
        linkedin_profile = await linkedin_oauth_service.get_user_info(
            access_token
        )

        return {
            "status": "success",
            "linkedin_profile": linkedin_profile,
            "cached_data": {
                "linkedin_id": db_user.get("linkedin_id"),
                "profile_picture_url": db_user.get("profile_picture_url"),
                "is_linkedin_connected": db_user.get("is_linkedin_connected")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch LinkedIn profile: {str(e)}"
        )


# GitHub OAuth routes
@router.get("/github/authorize")
async def github_authorize():
    """Generate GitHub OAuth authorization URL."""
    try:
        auth_data = github_oauth_service.generate_authorization_url()
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Failed to generate GitHub authorization URL: {str(e)}"
            )
        )


@router.get("/github/callback")
async def github_redirect_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Handle GitHub OAuth redirect and forward to frontend callback."""
    frontend_callback_url = "http://localhost:5174/auth/github/callback"

    if error:
        # Redirect to frontend with error
        redirect_url = (
            f"{frontend_callback_url}?error={error}"
            f"&error_description={error_description or ''}"
        )
    elif code and state:
        # Redirect to frontend with auth code
        redirect_url = f"{frontend_callback_url}?code={code}&state={state}"
    else:
        # Redirect to frontend with generic error
        redirect_url = (
            f"{frontend_callback_url}?error=invalid_request"
            "&error_description=Missing required parameters"
        )

    return RedirectResponse(url=redirect_url)


@router.post("/github/callback")
async def github_callback(auth_request: GitHubAuthRequest, response: Response):
    """Handle GitHub OAuth callback and create/login user."""
    try:
        # Exchange code for access token
        token_data = await github_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from GitHub
        github_profile = await github_oauth_service.get_user_info(
            access_token
        )

        if not github_profile.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from GitHub profile"
            )

        # Check if user exists by email
        existing_user = get_user_by_email(github_profile["email"])

        if existing_user:
            # Update existing user with GitHub connection
            github_data = {
                "github_id": github_profile["github_id"],
                "github_access_token": access_token,
                "profile_picture_url": github_profile.get("avatar_url"),
                "github_url": github_profile.get("github_url")
            }

            success = update_user_github_connection(
                github_profile["email"], github_data
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to update GitHub connection"
                )
        else:
            # Check if GitHub ID is already connected to another account
            github_user = get_user_by_github_id(github_profile["github_id"])
            if github_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This GitHub account is already connected to "
                        "another user"
                    )
                )

            # Create new user with GitHub data
            new_user_data = {
                "name": github_profile["name"],
                "email": github_profile["email"],
                "github_id": github_profile["github_id"],
                "github_access_token": access_token,
                "profile_picture_url": github_profile.get("avatar_url"),
                "github_url": github_profile.get("github_url")
            }

            success = create_user_with_github(new_user_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to create user account"
                )

        # Create JWT token for the user
        jwt_token = create_access_token(
            data={"sub": github_profile["email"]}
        )
        set_access_cookies(response, jwt_token)

        return {
            "status": "success",
            "message": "GitHub authentication successful",
            "user": {
                "name": github_profile["name"],
                "email": github_profile["email"],
                "github_id": github_profile["github_id"],
                "username": github_profile["username"],
                "avatar_url": github_profile.get("avatar_url"),
                "github_url": github_profile.get("github_url"),
                "is_github_connected": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub authentication failed: {str(e)}"
        )


@router.post("/github/connect")
async def connect_github(
    auth_request: GitHubAuthRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Connect GitHub account to existing authenticated user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Exchange code for access token
        token_data = await github_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from GitHub
        github_profile = await github_oauth_service.get_user_info(
            access_token
        )

        # Check if GitHub ID is already connected to another account
        github_user = get_user_by_github_id(github_profile["github_id"])
        if github_user and github_user["email"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This GitHub account is already connected to "
                    "another user"
                )
            )

        # Update user with GitHub connection
        github_data = {
            "github_id": github_profile["github_id"],
            "github_access_token": access_token,
            "profile_picture_url": github_profile.get("avatar_url"),
            "github_url": github_profile.get("github_url")
        }

        success = update_user_github_connection(current_user, github_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect GitHub account"
            )

        return {
            "status": "success",
            "message": "GitHub account connected successfully",
            "github_profile": {
                "github_id": github_profile["github_id"],
                "username": github_profile["username"],
                "avatar_url": github_profile.get("avatar_url"),
                "github_url": github_profile.get("github_url")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect GitHub account: {str(e)}"
        )


@router.post("/github/disconnect")
async def disconnect_github(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Disconnect GitHub account from current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        success = disconnect_user_github(current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to disconnect GitHub account"
            )

        return {
            "status": "success",
            "message": "GitHub account disconnected successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect GitHub account: {str(e)}"
        )


@router.get("/github/profile")
async def get_github_profile(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get GitHub profile information for the current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Get user from database
        db_user = get_user_by_email(current_user)
        if not db_user or not db_user.get("is_github_connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account not connected"
            )

        # Check if we have a valid access token
        access_token = db_user.get("github_access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub access token not available"
            )

        # Fetch fresh profile data from GitHub
        github_profile = await github_oauth_service.get_user_info(
            access_token
        )

        return {
            "status": "success",
            "github_profile": github_profile,
            "cached_data": {
                "github_id": db_user.get("github_id"),
                "github_url": db_user.get("github_url"),
                "is_github_connected": db_user.get("is_github_connected")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GitHub profile: {str(e)}"
        )


# Debug endpoint to check GitHub configuration
@router.get("/debug/github")
async def debug_github_config():
    """Debug GitHub OAuth configuration - REMOVE IN PRODUCTION."""
    from ..config.github_config import (
        GITHUB_CLIENT_ID,
        GITHUB_CLIENT_SECRET,
        GITHUB_REDIRECT_URI
    )

    return {
        "client_id_configured": bool(GITHUB_CLIENT_ID),
        "client_secret_configured": bool(GITHUB_CLIENT_SECRET),
        "redirect_uri_configured": bool(GITHUB_REDIRECT_URI),
        "client_id_value": GITHUB_CLIENT_ID,  # Remove in production
        "redirect_uri_value": GITHUB_REDIRECT_URI,
        "service_configured": (
            github_oauth_service.configured
            if hasattr(github_oauth_service, 'configured')
            else "Unknown"
        )
    }


# Temporary OAuth endpoints for registration (don't create users immediately)
@router.post("/linkedin/profile")
async def get_linkedin_profile_for_registration(auth_request:
                                                LinkedInAuthRequest):
    """Get LinkedIn profile data for registration without creating user."""
    try:
        # Exchange code for access token
        token_data = await linkedin_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from LinkedIn
        linkedin_profile = await linkedin_oauth_service.get_user_info(
            access_token
        )

        if not linkedin_profile.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from LinkedIn profile"
            )

        # Check if LinkedIn ID is already connected to another account
        linkedin_user = get_user_by_linkedin_id(
            linkedin_profile["linkedin_id"]
        )
        if linkedin_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This LinkedIn account is already connected to "
                    "another user"
                )
            )
        prof = linkedin_profile.get('vanity_name', '')

        # Return profile data with access token for later use
        return {
            "status": "success",
            "message": "LinkedIn profile retrieved successfully",
            "profile": {
                "name": linkedin_profile["full_name"],
                "email": linkedin_profile["email"],
                "linkedin_id": linkedin_profile["linkedin_id"],
                "linkedin_access_token": access_token,
                "profile_picture_url": linkedin_profile.get(
                    "profile_picture_url"
                ),
                "linkedin_url":
                f"https://www.linkedin.com/in/{prof}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LinkedIn profile: {str(e)}"
        )


@router.post("/github/profile")
async def get_github_profile_for_registration(auth_request: GitHubAuthRequest):
    """Get GitHub profile data for registration without creating user."""
    try:
        # Exchange code for access token
        token_data = await github_oauth_service.exchange_code_for_token(
            auth_request.code
        )
        access_token = token_data["access_token"]

        # Get user profile from GitHub
        github_profile = await github_oauth_service.get_user_info(
            access_token
        )

        if not github_profile.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from GitHub profile"
            )

        # Check if GitHub ID is already connected to another account
        github_user = get_user_by_github_id(
            str(github_profile["github_id"])
        )
        if github_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This GitHub account is already connected to "
                    "another user"
                )
            )

        # Return profile data with access token for later use
        return {
            "status": "success",
            "message": "GitHub profile retrieved successfully",
            "profile": {
                "name": github_profile["name"],
                "email": github_profile["email"],
                "github_id": str(github_profile["github_id"]),
                "github_access_token": access_token,
                "profile_picture_url": github_profile.get("avatar_url"),
                "github_url": github_profile.get("github_url")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GitHub profile: {str(e)}"
        )


@router.get("/skills")
async def get_current_user_skills(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get skills for the current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        skills = get_user_skills(current_user)
        return {
            "status": "success",
            "skills": skills
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user skills: {str(e)}"
        )


@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Update user profile information."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        success = update_user_profile(
            email=current_user,
            name=profile_data.name,
            linkedin_url=profile_data.linkedin_url,
            github_url=profile_data.github_url
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

        return {"status": "success", "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.put("/password")
async def update_password(
    password_data: PasswordUpdate,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Update user password."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Get current user data to verify current password
        user_data = get_user_by_email(current_user)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password,
                               user_data["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password and update
        new_hashed_password = hash_password(password_data.new_password)
        success = update_user_profile(
            email=current_user,
            password=new_hashed_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        return {
            "status": "success",
            "message": "Password updated successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )


@router.post("/skills")
async def add_skill(
    skill_data: SkillAdd,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Add a new skill for the current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        success = add_user_skill(current_user, skill_data.skill)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill already exists or failed to add"
            )

        return {"status": "success", "message": "Skill added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add skill: {str(e)}"
        )


@router.delete("/skills")
async def remove_skill(
    skill_data: SkillRemove,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Remove a skill for the current user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        success = remove_user_skill(current_user, skill_data.skill)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found or failed to remove"
            )

        return {"status": "success", "message": "Skill removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove skill: {str(e)}"
        )


@router.post("/interviews", response_model=UserInterviewResponse)
async def save_interview(
    interview_data: UserInterviewCreate,
    current_user: str = Depends(get_current_user)
):
    """Save a user interview."""
    try:
        interview = create_user_interview(
            email=current_user,
            title=interview_data.title,
            interview_text=interview_data.interview_text
        )

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save interview"
            )

        return UserInterviewResponse(**interview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save interview: {str(e)}"
        )


@router.get("/interviews", response_model=list[UserInterviewResponse])
async def get_interviews(current_user: str = Depends(get_current_user)):
    """Get all interviews for the current user."""
    try:
        interviews = get_user_interviews(current_user)
        return [UserInterviewResponse(**interview) for interview in interviews]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interviews: {str(e)}"
        )


@router.get("/interviews/{interview_id}", response_model=UserInterviewResponse)
async def get_interview(
    interview_id: int,
    current_user: str = Depends(get_current_user)
):
    """Get a specific interview by ID."""
    try:
        interview = get_user_interview_by_id(interview_id, current_user)

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        return UserInterviewResponse(**interview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interview: {str(e)}"
        )


@router.delete("/interviews/{interview_id}")
async def delete_interview(
    interview_id: int,
    current_user: str = Depends(get_current_user)
):
    """Delete a specific interview by ID."""
    try:
        success = delete_user_interview(interview_id, current_user)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found or could not be deleted"
            )

        return {"message": "Interview deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete interview: {str(e)}"
        )
