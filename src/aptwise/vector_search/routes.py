"""
Vector search routes for AptWise backend using Qdrant.
Provides API endpoints for vector similarity search.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

# Import from the proper utils module
from ..utils.qdrant_service import get_qdrant_service, \
    initialize_vector_database, force_reindex_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vector", tags=["vector"])


class VectorSearchRequest(BaseModel):
    text: str
    n_chunks: int = 5


class VectorSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query_text: str


@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """
    Search for similar vectors based on input text.

    This endpoint automatically initializes the database if needed,
    so no manual initialization is required.
    """
    try:
        logger.info(f"Vector search request: {request.text[:50]}...")

        # Get service
        service = get_qdrant_service()
        if not service:
            raise HTTPException(
                status_code=500,
                detail="Vector service not available. \
                    Please check Qdrant configuration."
            )

        # Auto-initialize only if needed (first time or if collection is empty)
        if not service.collection_exists_and_has_data():
            logger.info("Collection needs initialization, initializing now...")
            if not service.auto_initialize_if_needed():
                raise HTTPException(
                    status_code=500,
                    detail="Failed to initialize vector database"
                )

        # Perform search
        results = service.search(request.text, request.n_chunks)

        logger.info(f"Found {len(results)} results")

        return VectorSearchResponse(
            results=results,
            total_found=len(results),
            query_text=request.text
        )

    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/initialize")
async def initialize_database():
    """
    Manually initialize vector database.

    This is optional - the system auto-initializes when needed.
    """
    try:
        service = initialize_vector_database()
        if service:
            return {
                "message": "Vector database initialized successfully",
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize vector database"
            )
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Initialization failed: {str(e)}")


@router.post("/reindex")
async def force_reindex():
    """
    Force a complete re-indexing of the vector database.

    This clears existing data and reloads everything from JSON files.
    Use this to fix duplicate entries or refresh the database.
    """
    try:
        logger.info("🔄 Starting force re-index...")
        service = force_reindex_database()
        if service:
            collection_info = service.get_collection_info()
            return {
                "message": "Vector database re-indexed successfully",
                "status": "success",
                "collection_info": collection_info
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to re-index vector database"
            )
    except Exception as e:
        logger.error(f"Database re-index error: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Re-index failed: {str(e)}")


@router.get("/status")
async def get_status():
    """Get vector service status."""
    try:
        service = get_qdrant_service()
        if not service:
            return {
                "status": "unavailable",
                "message": "Vector service not available"
            }

        collection_info = service.get_collection_info()

        return {
            "status": "active",
            "model_name": service.model_name,
            "embedding_dimension": service.embedding_dim,
            "collection_name": service.collection_name,
            "collection_info": collection_info
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "status": "error",
            "message": f"Status check failed: {str(e)}"
        }


@router.get("/collections")
async def get_collections():
    """Get all collections."""
    try:
        service = get_qdrant_service()
        if not service or not service.qdrant_client:
            raise HTTPException(
                status_code=500,
                detail="Vector service not available"
            )

        collections = service.qdrant_client.get_collections()
        collection_info = service.get_collection_info()

        return {
            "collections": [
                {
                    "name": col.name,
                    "status": "active"
                }
                for col in collections.collections
            ],
            "current_collection": collection_info
        }

    except Exception as e:
        logger.error(f"Collections retrieval error: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Failed to get collections: {str(e)}")
