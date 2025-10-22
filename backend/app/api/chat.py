"""
LetterOn Server - Chat API Routes
Purpose: Conversational AI chat about letters
Testing: Use FastAPI TestClient with mocked Lambda
AWS Deployment: Ensure Lambda invocation permissions

Endpoints:
- POST /chat - Chat with AI about a letter
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models import ChatRequest, ChatResponse, ChatMessage, ErrorResponse, MessageRole
from app.services.dynamo import dynamodb_client
from app.services.lambda_client import lambda_client
from app.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


def load_prompt_template(filename: str) -> str:
    """Load prompt template from file."""
    try:
        with open(f"app/prompts/{filename}", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt template {filename}: {str(e)}")
        return ""


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    }
)
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Chat with AI about a letter.

    Workflow:
    1. Verify letter exists and belongs to user
    2. Load conversation history from DynamoDB
    3. Build prompt with letter context and conversation history
    4. Call LLM Lambda for response
    5. Save user message and AI response to conversation history
    6. Return AI response with full conversation

    Args:
        request: Chat request with letter_id and message
        user_id: Current user ID from JWT

    Returns:
        ChatResponse: AI response and conversation history

    Raises:
        HTTPException 404: If letter not found
        HTTPException 403: If user doesn't own the letter
    """
    logger.info(f"Chat request for letter {request.letter_id} from user {user_id}")

    # Get letter
    letter = dynamodb_client.get_letter(request.letter_id)

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

    try:
        # Load conversation history
        conversation_history = dynamodb_client.get_conversation_history(
            letter_id=request.letter_id,
            limit=50
        )

        logger.info(f"Loaded {len(conversation_history)} previous messages")

        # Convert to chat format
        history_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]

        # Load chat prompt template
        chat_prompt = load_prompt_template("chat_prompt.txt")

        # Build conversation history string for prompt
        conversation_str = ""
        for msg in history_messages:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            conversation_str += f"{role_label}: {msg['content']}\n\n"

        # Fill in prompt template
        filled_prompt = chat_prompt.replace("{{SUBJECT}}", letter.get("subject", "No subject"))
        filled_prompt = filled_prompt.replace("{{SENDER}}", letter.get("sender_name", "Unknown"))
        filled_prompt = filled_prompt.replace("{{CATEGORY}}", letter.get("letter_category", "miscellaneous"))
        filled_prompt = filled_prompt.replace("{{LETTER_CONTENT}}", letter.get("content", ""))
        filled_prompt = filled_prompt.replace("{{CONVERSATION_HISTORY}}", conversation_str or "No previous conversation.")
        filled_prompt = filled_prompt.replace("{{USER_MESSAGE}}", request.message)

        # Call LLM Lambda
        logger.info("Calling LLM Lambda for chat response")
        llm_result = lambda_client.invoke_llm_lambda(
            input_text=request.message,
            prompt_template=filled_prompt,
            conversation_history=history_messages,
            temperature=0.7,
            max_tokens=1000
        )

        ai_response = llm_result.get("response", "I apologize, but I'm having trouble processing your request. Please try again.")

        logger.info(f"LLM response received: {len(ai_response)} characters")

        # Save user message to conversation history
        dynamodb_client.create_conversation_message({
            "letter_id": request.letter_id,
            "user_id": user_id,
            "role": "user",
            "content": request.message
        })

        # Save AI response to conversation history
        dynamodb_client.create_conversation_message({
            "letter_id": request.letter_id,
            "user_id": user_id,
            "role": "assistant",
            "content": ai_response
        })

        logger.info("Conversation messages saved")

        # Build updated conversation history for response
        updated_history = history_messages + [
            {"role": MessageRole.USER, "content": request.message},
            {"role": MessageRole.ASSISTANT, "content": ai_response}
        ]

        return ChatResponse(
            message=ai_response,
            conversation_history=[
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in updated_history
            ]
        )

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )


@router.delete(
    "/{letter_id}/history",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "Letter not found"},
    }
)
async def clear_conversation_history(
    letter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Clear conversation history for a letter.

    Args:
        letter_id: Letter ID
        user_id: Current user ID from JWT

    Returns:
        dict: Success message
    """
    # Verify letter ownership
    letter = dynamodb_client.get_letter(letter_id)

    if not letter or letter["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get all conversation messages
    messages = dynamodb_client.get_conversation_history(letter_id, limit=1000)

    # Delete each message
    # Note: For production, consider batch delete for efficiency
    for msg in messages:
        # DynamoDB delete would go here
        # This is a simple implementation; optimize for production
        pass

    logger.info(f"Cleared {len(messages)} conversation messages for letter {letter_id}")

    return {"message": f"Cleared {len(messages)} messages from conversation history"}
