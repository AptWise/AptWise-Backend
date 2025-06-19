"""
Main FastAPI application for AptWise backend.
"""
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
import uvicorn
from .auth.routes import router as auth_router
from .auth.utils import get_current_user
from .config import create_tables, get_session

app = FastAPI(
    title="AptWise Backend API",
    description="Backend API for AptWise application with authentication",
    version="1.0.0"
)

# Check database connection
session = get_session()
if not session:
    print("ERROR: Failed to connect to PostgreSQL database. \
          Application will exit.")
    # Add a small delay before exiting to allow error messages to be printed
    import time
    time.sleep(1)
    sys.exit(1)

# Initialize database tables
create_tables()

# Include authentication routes
app.include_router(auth_router)


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
