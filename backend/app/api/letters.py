"""
LetterOn Server - Letters API Routes
Purpose: Letter CRUD operations, image upload, OCR processing, and analysis
Testing: Use FastAPI TestClient with mocked AWS services
AWS Deployment: Ensure permissions for S3, Lambda, DynamoDB

Endpoints:
- POST /letters/process-images - Upload and process letter images
- GET /letters - List all letters (with filters)
- GET /letters/{letter_id} - Get letter details
- PATCH /letters/{letter_id} - Update letter
- DELETE /letters/{letter_id} - Delete letter (soft delete)
- POST /letters/{letter_id}/snooze - Snooze letter
- POST /letters/{letter_id}/archive - Archive letter
- POST /letters/{letter_id}/restore - Restore letter
- POST /letters/{letter_id}/translate - Translate letter
"""

import logging
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from datetime import datetime

from app.models import (
    LetterResponse,
    LetterUpdate,
    ImageProcessResponse,
    MessageResponse,
    ErrorResponse,
    TranslationRequest,
    TranslationResponse,
    LetterCategory,
    ActionStatus,
    Sender
)
from app.services.dynamo import dynamodb_client
from app.services.s3_client import s3_client
from app.services.lambda_client import lambda_client
from app.dependencies import get_current_user_id
from app.utils.helpers import generate_uuid, get_current_timestamp, get_current_iso_timestamp
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function to load prompt templates
def load_prompt_template(filename: str) -> str:
    """Load prompt template from file."""
    try:
        with open(f"app/prompts/{filename}", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt template {filename}: {str(e)}")
        return ""


# Helper function to convert DynamoDB letter to API response
def letter_to_response(letter: dict) -> LetterResponse:
    """Convert DynamoDB letter to API response format."""
    # Convert timestamps to ISO format
    letter_date = datetime.fromtimestamp(letter.get("letter_date", 0)).isoformat() if letter.get("letter_date") else get_current_iso_timestamp()
    record_created_at = datetime.fromtimestamp(letter.get("record_created_at", 0)).isoformat() if letter.get("record_created_at") else get_current_iso_timestamp()

    return LetterResponse(
        letter_id=letter["letter_id"],
        subject=letter.get("subject", ""),
        sender=letter.get("sender"),
        sender_name=letter.get("sender_name", ""),
        sender_email=letter.get("sender_email", ""),
        recipients=letter.get("recipients", []),
        content=letter.get("content", ""),
        date=letter_date,
        recordCreatedAt=record_created_at,
        read=letter.get("read", False),
        flagged=letter.get("flagged", False),
        snoozed=letter.get("snoozed", False),
        snoozeUntil=letter.get("snooze_until"),
        archived=letter.get("archived", False),
        deleted=letter.get("deleted", False),
        account=letter.get("account", "default"),
        letterCategory=letter.get("letter_category", LetterCategory.MISCELLANEOUS),
        actionStatus=letter.get("action_status", ActionStatus.NO_ACTION_NEEDED),
        actionDueDate=letter.get("action_due_date"),
        hasReminder=letter.get("has_reminder", False),
        aiSuggestion=letter.get("ai_suggestion", ""),
        userNote=letter.get("user_note", ""),
        translatedContent=letter.get("translated_content"),
        attachments=letter.get("attachments", []),
        originalImages=letter.get("original_images", [])
    )


@router.post(
    "/process-images",
    response_model=ImageProcessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid files or processing error"},
    }
)
async def process_images(
    files: List[UploadFile] = File(..., description="Letter images (max 3, 1MB each)"),
    include_translation: bool = Form(False),
    translation_language: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload and process letter images with OCR and AI analysis.

    Workflow:
    1. Validate uploaded files
    2. Upload images to S3
    3. Call LetterOnOCRHandler Lambda for text extraction
    4. Call LetterOnLLMHandler Lambda for analysis
    5. Create letter record in DynamoDB
    6. Return structured letter data

    Args:
        files: List of image files (max 3, 1MB each)
        include_translation: Whether to include translation
        translation_language: Target language for translation
        user_id: Current user ID from JWT

    Returns:
        ImageProcessResponse: Processed letter data
    """
    logger.info(f"Processing {len(files)} images for user {user_id}")

    # Validate number of files
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_files_per_upload} files allowed"
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    # Generate letter ID
    letter_id = generate_uuid()


    try:
        # Step 1: Upload images to S3
        s3_keys = []
        image_urls = []


        for file in files:
            # Validate file size
            content = await file.read()
            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds {settings.max_upload_size_mb}MB limit"
                )

            # Validate file type
            if file.content_type not in settings.allowed_image_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
    
            # Upload to S3
            upload_result = s3_client.upload_letter_image(
                file_content=content,
                letter_id=letter_id,
                filename=file.filename,
                content_type=file.content_type
            )

            s3_keys.append(upload_result["s3_key"])
            image_urls.append(upload_result["url"])

        logger.info(f"Uploaded {len(s3_keys)} images to S3 for letter {letter_id}")

        # Step 2: Call OCR Lambda
        logger.info(f"Calling OCR Lambda for letter {letter_id}")
        response = lambda_client.invoke_ocr_lambda(s3_keys)
        ocr_result = json.loads(   response.get("body"))['ocr_results']

        # Extract OCR text from all objects in the array
        ocr_texts = []
        if isinstance(ocr_result, list):
            for item in ocr_result:
                if isinstance(item, dict) and "text" in item:
                    text = item.get("text", "").strip()
                if text:  # Only add non-empty text
                    ocr_texts.append(text)
        elif isinstance(ocr_result, dict) and "text" in ocr_result:
        # Handle case where it's a single object instead of array
            text = ocr_result.get("text", "").strip()
            if text:
                ocr_texts.append(text)

        # Concatenate all texts with semicolon separator
        ocr_text = "; ".join(ocr_texts)

        # Extract OCR text
     
        logger.info(f"OCR completed, extracted {len(ocr_text)} characters")

        # Step 3: Call LLM Lambda for analysis
        logger.info(f"Calling LLM Lambda for letter analysis")
        analysis_prompt = load_prompt_template("analyze_prompt.txt")
        print("hahahahaa",s3_keys, ocr_text)
        # Replace placeholders in prompt
        analysis_prompt_filled = analysis_prompt.replace("{{OCR_TEXT}}", ocr_text)
        
        llm_result = lambda_client.invoke_llm_lambda(
            text=ocr_text,
            prompt_template=analysis_prompt_filled,
            temperature=0.5  # Lower temperature for more consistent structured output
        )
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",llm_result)
        # Parse LLM response (expected to be JSON)
        try:
            analysis_data = json.loads(llm_result.get("response", "{}"))
        except json.JSONDecodeError:
            logger.warning("LLM response is not valid JSON, using defaults")
            analysis_data = {}

        # Extract analysis fields with defaults
        subject = analysis_data.get("subject", "Untitled Letter")
        sender_name = analysis_data.get("sender", "Unknown Sender")
        category = analysis_data.get("category", "miscellaneous")
        action_status = analysis_data.get("action_status", "no-action-needed")
        has_reminder = analysis_data.get("has_reminder", False)
        action_due_date = analysis_data.get("action_due_date")
        ai_suggestion = analysis_data.get("ai_suggestion", "")

        # Step 4: Create letter in DynamoDB
        letter_data = {
            "user_id": user_id,
            "subject": subject,
            "sender_name": sender_name,
            "content": ocr_text,
            "ocr_text": ocr_text,
            "letter_category": category,
            "action_status": action_status,
            "has_reminder": has_reminder,
            "action_due_date": action_due_date,
            "ai_suggestion": ai_suggestion,
            "original_images": image_urls,
            "letter_date": get_current_timestamp(),
        }

        letter = dynamodb_client.create_letter(letter_data)
        logger.info(f"Letter created: {letter['letter_id']}")

        # Step 5: Handle translation if requested
        if include_translation and translation_language:
            # TODO: Call translation API or LLM for translation
            logger.info(f"Translation requested to {translation_language}")

        return ImageProcessResponse(
            letter_id=letter["letter_id"],
            subject=subject,
            sender=sender_name,
            content=ocr_text,
            letterCategory=category,
            actionStatus=action_status,
            hasReminder=has_reminder,
            actionDueDate=action_due_date,
            aiSuggestion=ai_suggestion,
            originalImages=image_urls
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing images: {str(e)}"
        )


@router.get(
    "",
    response_model=List[LetterResponse],
    responses={
        200: {"model": List[LetterResponse], "description": "List of letters"},
    }
)
async def list_letters(
    user_id: str = Depends(get_current_user_id),
    archived: Optional[bool] = None,
    deleted: Optional[bool] = None,
    flagged: Optional[bool] = None,
    snoozed: Optional[bool] = None,
    category: Optional[LetterCategory] = None,
    limit: int = 50
):
    """
    Get all letters for the current user with optional filters.

    Args:
        user_id: Current user ID from JWT
        archived: Filter by archived status
        deleted: Filter by deleted status
        flagged: Filter by flagged status
        snoozed: Filter by snoozed status
        category: Filter by letter category
        limit: Maximum number of results

    Returns:
        List[LetterResponse]: List of letters
    """
    logger.info(f"Fetching letters for user {user_id}")

    # Build filters
    filters = {}
    if archived is not None:
        filters["archived"] = archived
    if deleted is not None:
        filters["deleted"] = deleted
    if flagged is not None:
        filters["flagged"] = flagged
    if snoozed is not None:
        filters["snoozed"] = snoozed
    if category is not None:
        filters["letter_category"] = category

    # Get letters from DynamoDB
    result = dynamodb_client.get_letters_by_user(
        user_id=user_id,
        limit=limit,
        filters=filters
    )

    letters = result["items"]
    logger.info(f"Found {len(letters)} letters")

    # Convert to response format
    return [letter_to_response(letter) for letter in letters]


@router.get(
    "/{letter_id}",
    response_model=LetterResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def get_letter(
    letter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific letter by ID.

    Args:
        letter_id: Letter ID
        user_id: Current user ID from JWT

    Returns:
        LetterResponse: Letter details

    Raises:
        HTTPException 404: If letter not found or not owned by user
    """
    letter = dynamodb_client.get_letter(letter_id)

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Verify ownership
    if letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return letter_to_response(letter)


@router.patch(
    "/{letter_id}",
    response_model=LetterResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def update_letter(
    letter_id: str,
    updates: LetterUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a letter's properties.

    Args:
        letter_id: Letter ID
        updates: Fields to update
        user_id: Current user ID from JWT

    Returns:
        LetterResponse: Updated letter

    Raises:
        HTTPException 404: If letter not found or not owned by user
    """
    # Get letter
    letter = dynamodb_client.get_letter(letter_id)

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Verify ownership
    if letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Build update dict (only include non-None fields)
    update_dict = {}
    for field, value in updates.dict(exclude_unset=True).items():
        if value is not None:
            update_dict[field] = value

    if not update_dict:
        # No updates, return current letter
        return letter_to_response(letter)

    # Update letter
    updated_letter = dynamodb_client.update_letter(letter_id, update_dict)
    logger.info(f"Letter {letter_id} updated")

    return letter_to_response(updated_letter)


@router.delete(
    "/{letter_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def delete_letter(
    letter_id: str,
    permanent: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a letter (soft delete by default).

    Args:
        letter_id: Letter ID
        permanent: If True, permanently delete. If False, soft delete.
        user_id: Current user ID from JWT

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException 404: If letter not found or not owned by user
    """
    # Get letter
    letter = dynamodb_client.get_letter(letter_id)

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Verify ownership
    if letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Delete letter
    success = dynamodb_client.delete_letter(letter_id, soft_delete=not permanent)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting letter"
        )

    # Optionally delete S3 images for permanent deletion
    if permanent:
        s3_client.delete_letter_images(letter_id)

    logger.info(f"Letter {letter_id} deleted (permanent={permanent})")

    return MessageResponse(message="Letter deleted successfully")


@router.post(
    "/{letter_id}/snooze",
    response_model=LetterResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def snooze_letter(
    letter_id: str,
    snooze_until: str,  # ISO timestamp
    user_id: str = Depends(get_current_user_id)
):
    """
    Snooze a letter until a specific date.

    Args:
        letter_id: Letter ID
        snooze_until: ISO timestamp when letter should reappear
        user_id: Current user ID from JWT

    Returns:
        LetterResponse: Updated letter
    """
    # Get letter
    letter = dynamodb_client.get_letter(letter_id)

    if not letter or letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Update letter
    updated_letter = dynamodb_client.update_letter(
        letter_id,
        {"snoozed": True, "snooze_until": snooze_until}
    )

    return letter_to_response(updated_letter)


@router.post(
    "/{letter_id}/archive",
    response_model=LetterResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def archive_letter(
    letter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Archive a letter."""
    letter = dynamodb_client.get_letter(letter_id)

    if not letter or letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    updated_letter = dynamodb_client.update_letter(letter_id, {"archived": True})
    return letter_to_response(updated_letter)


@router.post(
    "/{letter_id}/restore",
    response_model=LetterResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def restore_letter(
    letter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Restore a letter from archive or snooze."""
    letter = dynamodb_client.get_letter(letter_id)

    if not letter or letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    updated_letter = dynamodb_client.update_letter(
        letter_id,
        {"archived": False, "snoozed": False, "deleted": False}
    )
    return letter_to_response(updated_letter)


@router.post(
    "/{letter_id}/translate",
    response_model=TranslationResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def translate_letter(
    letter_id: str,
    request: TranslationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Translate letter content to target language.

    Args:
        letter_id: Letter ID
        request: Translation request with target_language
        user_id: Current user ID from JWT

    Returns:
        TranslationResponse: Translated content
    """
    letter = dynamodb_client.get_letter(letter_id)

    if not letter or letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Call LLM for translation
    translation_prompt = f"Translate the following text to {request.target_language}:\n\n{letter['content']}"

    llm_result = lambda_client.invoke_llm_lambda(
        input_text=letter["content"],
        prompt_template=translation_prompt,
        temperature=0.3
    )

    translated_content = llm_result.get("response", "")

    # Store translation in letter
    translated_dict = letter.get("translated_content", {}) or {}
    translated_dict[request.target_language] = translated_content

    dynamodb_client.update_letter(letter_id, {"translated_content": translated_dict})

    return TranslationResponse(
        translated_content=translated_content,
        language=request.target_language
    )
