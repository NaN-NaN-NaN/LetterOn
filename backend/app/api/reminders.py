"""
LetterOn Server - Reminders API Routes
Purpose: Create, update, and manage letter reminders
Testing: Use FastAPI TestClient with test data
AWS Deployment: No special configuration needed

Endpoints:
- POST /reminders - Create reminder
- GET /reminders - List reminders
- GET /reminders/{reminder_id} - Get reminder details
- PATCH /reminders/{reminder_id} - Update reminder
- DELETE /reminders/{reminder_id} - Delete reminder
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.models import (
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
    MessageResponse,
    ErrorResponse
)
from app.services.dynamo import dynamodb_client
from app.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
        400: {"model": ErrorResponse, "description": "Invalid reminder data"},
    }
)
async def create_reminder(
    reminder: ReminderCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a reminder for a letter.

    Args:
        reminder: Reminder creation data
        user_id: Current user ID from JWT

    Returns:
        ReminderResponse: Created reminder

    Raises:
        HTTPException 404: If letter not found or not owned by user
        HTTPException 400: If reminder time is in the past
    """
    logger.info(f"Creating reminder for letter {reminder.letter_id}")

    # Verify letter exists and belongs to user
    letter = dynamodb_client.get_letter(reminder.letter_id)

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    if letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Validate reminder time is in the future
    from app.utils.helpers import get_current_timestamp
    current_time = get_current_timestamp()

    if reminder.reminder_time <= current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminder time must be in the future"
        )

    try:
        # Create reminder
        created_reminder = dynamodb_client.create_reminder({
            "user_id": user_id,
            "letter_id": reminder.letter_id,
            "reminder_time": reminder.reminder_time,
            "message": reminder.message
        })

        # Update letter to mark has_reminder=True
        dynamodb_client.update_letter(reminder.letter_id, {"has_reminder": True})

        logger.info(f"Reminder created: {created_reminder['reminder_id']}")

        return ReminderResponse(
            reminder_id=created_reminder["reminder_id"],
            letter_id=created_reminder["letter_id"],
            user_id=created_reminder["user_id"],
            reminder_time=created_reminder["reminder_time"],
            message=created_reminder["message"],
            sent=created_reminder["sent"],
            created_at=created_reminder["created_at"]
        )

    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating reminder"
        )


@router.get(
    "",
    response_model=List[ReminderResponse],
    responses={
        200: {"model": List[ReminderResponse], "description": "List of reminders"},
    }
)
async def list_reminders(
    user_id: str = Depends(get_current_user_id),
    sent: Optional[bool] = Query(None, description="Filter by sent status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    Get all reminders for the current user.

    Args:
        user_id: Current user ID from JWT
        sent: Optional filter by sent status (True=sent, False=pending, None=all)
        limit: Maximum number of results

    Returns:
        List[ReminderResponse]: List of reminders
    """
    logger.info(f"Fetching reminders for user {user_id}")

    try:
        # Get all reminders for user
        reminders = dynamodb_client.get_reminders_by_user(user_id)

        # Apply sent filter if provided
        if sent is not None:
            reminders = [r for r in reminders if r.get("sent") == sent]

        # Limit results
        reminders = reminders[:limit]

        logger.info(f"Found {len(reminders)} reminders")

        return [
            ReminderResponse(
                reminder_id=r["reminder_id"],
                letter_id=r["letter_id"],
                user_id=r["user_id"],
                reminder_time=r["reminder_time"],
                message=r.get("message", ""),
                sent=r.get("sent", False),
                created_at=r["created_at"]
            )
            for r in reminders
        ]

    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching reminders"
        )


@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found"},
    }
)
async def get_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific reminder by ID.

    Args:
        reminder_id: Reminder ID
        user_id: Current user ID from JWT

    Returns:
        ReminderResponse: Reminder details

    Raises:
        HTTPException 404: If reminder not found or not owned by user
    """
    # Note: This would need a direct get_reminder_by_id function in dynamo.py
    # For now, get all reminders and filter
    reminders = dynamodb_client.get_reminders_by_user(user_id)
    reminder = next((r for r in reminders if r["reminder_id"] == reminder_id), None)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    return ReminderResponse(
        reminder_id=reminder["reminder_id"],
        letter_id=reminder["letter_id"],
        user_id=reminder["user_id"],
        reminder_time=reminder["reminder_time"],
        message=reminder.get("message", ""),
        sent=reminder.get("sent", False),
        created_at=reminder["created_at"]
    )


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found"},
    }
)
async def update_reminder(
    reminder_id: str,
    updates: ReminderUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a reminder.

    Args:
        reminder_id: Reminder ID
        updates: Fields to update
        user_id: Current user ID from JWT

    Returns:
        ReminderResponse: Updated reminder

    Raises:
        HTTPException 404: If reminder not found or not owned by user
    """
    # Verify reminder exists and belongs to user
    reminders = dynamodb_client.get_reminders_by_user(user_id)
    reminder = next((r for r in reminders if r["reminder_id"] == reminder_id), None)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Build update dict
    update_dict = {}
    if updates.reminder_time is not None:
        # Validate reminder time is in the future
        from app.utils.helpers import get_current_timestamp
        current_time = get_current_timestamp()

        if updates.reminder_time <= current_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reminder time must be in the future"
            )
        update_dict["reminder_time"] = updates.reminder_time

    if updates.message is not None:
        update_dict["message"] = updates.message

    if not update_dict:
        # No updates, return current reminder
        return ReminderResponse(
            reminder_id=reminder["reminder_id"],
            letter_id=reminder["letter_id"],
            user_id=reminder["user_id"],
            reminder_time=reminder["reminder_time"],
            message=reminder.get("message", ""),
            sent=reminder.get("sent", False),
            created_at=reminder["created_at"]
        )

    # Update reminder
    try:
        updated_reminder = dynamodb_client.update_reminder(reminder_id, update_dict)

        logger.info(f"Reminder {reminder_id} updated")

        return ReminderResponse(
            reminder_id=updated_reminder["reminder_id"],
            letter_id=updated_reminder["letter_id"],
            user_id=updated_reminder["user_id"],
            reminder_time=updated_reminder["reminder_time"],
            message=updated_reminder.get("message", ""),
            sent=updated_reminder.get("sent", False),
            created_at=updated_reminder["created_at"]
        )

    except Exception as e:
        logger.error(f"Error updating reminder: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating reminder"
        )


@router.delete(
    "/{reminder_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found"},
    }
)
async def delete_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a reminder.

    Args:
        reminder_id: Reminder ID
        user_id: Current user ID from JWT

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException 404: If reminder not found or not owned by user
    """
    # Verify reminder exists and belongs to user
    reminders = dynamodb_client.get_reminders_by_user(user_id)
    reminder = next((r for r in reminders if r["reminder_id"] == reminder_id), None)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Delete reminder
    success = dynamodb_client.delete_reminder(reminder_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting reminder"
        )

    # Check if there are other reminders for this letter
    letter_reminders = [r for r in reminders if r["letter_id"] == reminder["letter_id"] and r["reminder_id"] != reminder_id]

    # If no more reminders, update letter
    if not letter_reminders:
        dynamodb_client.update_letter(reminder["letter_id"], {"has_reminder": False})

    logger.info(f"Reminder {reminder_id} deleted")

    return MessageResponse(message="Reminder deleted successfully")
