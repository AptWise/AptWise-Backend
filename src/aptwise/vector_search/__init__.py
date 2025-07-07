"""
Vector search module for AptWise backend.

This module provides vector similarity search functionality using Qdrant
for finding similar questions and answers based on semantic similarity.
"""

from .routes import (
    router,
    VectorSearchRequest,
    VectorSearchResponse
)

__all__ = [
    "router",
    "VectorSearchRequest",
    "VectorSearchResponse"
]
