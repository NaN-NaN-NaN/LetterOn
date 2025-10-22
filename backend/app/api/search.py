"""
LetterOn Server - Search API Routes
Purpose: Full-text search across letters
Testing: Use FastAPI TestClient with test data
AWS Deployment: Consider using OpenSearch for production

Endpoints:
- GET /search?q=query - Search letters by text
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.models import SearchResponse, LetterResponse, ErrorResponse
from app.services.dynamo import dynamodb_client
from app.dependencies import get_current_user_id
from app.api.letters import letter_to_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid search query"},
    }
)
async def search_letters(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Search letters by text content.

    Searches across:
    - Letter subject
    - Sender name
    - Letter content
    - OCR text
    - AI suggestions

    Note: This is a simple implementation using DynamoDB scan.
    For production with large datasets, consider:
    - Amazon OpenSearch (Elasticsearch)
    - DynamoDB Streams + Lambda + OpenSearch
    - Algolia or similar search service

    Args:
        q: Search query string
        limit: Maximum number of results
        user_id: Current user ID from JWT

    Returns:
        SearchResponse: List of matching letters

    Example:
        GET /search?q=credit%20card&limit=10
    """
    logger.info(f"Search request from user {user_id}: query='{q}', limit={limit}")

    if not q or len(q.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    try:
        # Perform search using DynamoDB
        results = dynamodb_client.search_letters(
            user_id=user_id,
            query=q,
            limit=limit
        )

        logger.info(f"Search found {len(results)} results")

        # Convert to response format
        letter_responses = [letter_to_response(letter) for letter in results]

        return SearchResponse(
            results=letter_responses,
            total=len(letter_responses),
            query=q
        )

    except Exception as e:
        logger.error(f"Error performing search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing search"
        )


@router.get(
    "/suggestions",
    response_model=dict,
    responses={
        200: {"description": "Search suggestions"},
    }
)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(5, ge=1, le=10, description="Maximum suggestions"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get search suggestions based on partial query.

    This is a simple implementation that returns common search terms.
    For production, implement:
    - Autocomplete with trie data structure
    - Popular searches tracking
    - Personalized suggestions based on user's letters

    Args:
        q: Partial search query
        limit: Maximum suggestions
        user_id: Current user ID from JWT

    Returns:
        dict: List of suggested queries
    """
    logger.info(f"Search suggestions request: query='{q}'")

    # Simple implementation: return common categories and terms
    suggestions = []

    # Category suggestions
    categories = [
        "bills", "bank", "insurance", "government", "medical",
        "education", "legal", "delivery", "subscription", "utilities"
    ]

    for cat in categories:
        if q.lower() in cat.lower():
            suggestions.append(cat)

    # Limit suggestions
    suggestions = suggestions[:limit]

    return {
        "query": q,
        "suggestions": suggestions
    }
