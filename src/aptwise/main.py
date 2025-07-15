"""
Main FastAPI application for AptWise backend.
"""
import sys
import os
import time
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load environment variables first, before any other imports
load_dotenv()

# Debug: Print environment loading status
print("Environment Variables Status:")
print(f"LINKEDIN_CLIENT_ID: {os.getenv('LINKEDIN_CLIENT_ID')}")
linkedin_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
print(f"LINKEDIN_CLIENT_SECRET: {'Present' if linkedin_secret else 'Missing'}")
print(f"LINKEDIN_REDIRECT_URI: {os.getenv('LINKEDIN_REDIRECT_URI')}")

from .auth.routes import router as auth_router  # noqa: E402
from .auth.utils import get_current_user  # noqa: E402
from .config import get_session  # noqa: E402
from .vector_search.routes import router as vector_router  # noqa: E402
from .interview.routes import router as interview_router  # noqa: E402

app = FastAPI(
    title="AptWise Backend API",
    description="Backend API for AptWise application with authentication "
                "and LinkedIn OAuth",
    version="1.0.0"
)


# Add middleware to log all requests (for debugging)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🌐 {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Response: {response.status_code}")
    return response


# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],   # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check database connection
session = get_session()
if not session:
    print("ERROR: Failed to connect to PostgreSQL database. "
          "Application will exit.")
    # Add a small delay before exiting to allow error messages to be printed
    time.sleep(1)
    sys.exit(1)

# Note: Tables are now managed by Alembic migrations

# Include authentication routes
app.include_router(auth_router)

# Include vector search routes
app.include_router(vector_router)

# Include interview routes
app.include_router(interview_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to AptWise Backend API"}


@app.get("/protected")
async def protected(current_user: Optional[str] = Depends(get_current_user)):
    """A protected endpoint that requires JWT authentication."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": current_user, "message": "You are authenticated"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
