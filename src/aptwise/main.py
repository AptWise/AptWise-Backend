"""
Main FastAPI application for AptWise backend.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from typing import Optional
import uvicorn
from .auth.routes import router as auth_router
from .auth.utils import get_current_user

app = FastAPI(
    title="AptWise Backend API",
    description="Backend API for AptWise application with authentication",
    version="1.0.0"
)

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
