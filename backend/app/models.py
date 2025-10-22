"""
LetterOn Server - Pydantic Data Models
Purpose: Request/response schemas and data validation
Testing: Pydantic validates data automatically
AWS Deployment: No special configuration needed

This module defines all Pydantic models for:
- Authentication requests/responses
- Letter data structures
- Chat messages
- Reminders
- API responses

These models match the frontend TypeScript interfaces.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


# ===== ENUMS =====

class LetterCategory(str, Enum):
    """Letter category enumeration (15 types)."""
    OFFICIAL_GOVERNMENT = "official-government"
    FINANCIAL_BILLING = "financial-billing"
    BANKING_INSURANCE = "banking-insurance"
    EMPLOYMENT_HR = "employment-hr"
    EDUCATION_ACADEMIC = "education-academic"
    HEALTHCARE_MEDICAL = "healthcare-medical"
    LEGAL_COMPLIANCE = "legal-compliance"
    LOGISTICS_DELIVERY = "logistics-delivery"
    PERSONAL_SOCIAL = "personal-social"
    REAL_ESTATE_UTILITIES = "real-estate-utilities"
    SUBSCRIPTION_MEMBERSHIP = "subscription-membership"
    MARKETING_PROMOTIONS = "marketing-promotions"
    TRAVEL_TICKETING = "travel-ticketing"
    NONPROFIT_NGO = "nonprofit-ngo"
    MISCELLANEOUS = "miscellaneous"


class ActionStatus(str, Enum):
    """Action status enumeration."""
    REQUIRE_ACTION = "require-action"
    ACTION_DONE = "action-done"
    NO_ACTION_NEEDED = "no-action-needed"


class MessageRole(str, Enum):
    """Chat message role."""
    USER = "user"
    ASSISTANT = "assistant"


# ===== AUTHENTICATION MODELS =====

class UserRegisterRequest(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100, description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }


class UserResponse(BaseModel):
    """User information response."""
    id: str = Field(..., description="User ID", alias="user_id")
    name: str
    email: str

    class Config:
        populate_by_name = True


class AuthResponse(BaseModel):
    """Authentication response with token."""
    token: str = Field(..., description="JWT access token")
    user: UserResponse


# ===== SENDER & RECIPIENT MODELS =====

class SocialLink(BaseModel):
    """Social media link."""
    platform: str
    url: str
    username: Optional[str] = None


class Organization(BaseModel):
    """Organization information."""
    name: str
    logo: Optional[str] = None
    website: Optional[str] = None


class Sender(BaseModel):
    """Letter sender information."""
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    organization: Optional[Organization] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    socialLinks: Optional[List[SocialLink]] = None
    lastContacted: Optional[str] = None
    firstContacted: Optional[str] = None
    emailCount: Optional[int] = None


class Recipient(BaseModel):
    """Letter recipient information."""
    name: str
    email: str
    avatar: Optional[str] = None


class Attachment(BaseModel):
    """Letter attachment information."""
    name: str
    size: str  # e.g., "156 KB"
    type: str  # MIME type
    url: str


# ===== LETTER MODELS =====

class LetterBase(BaseModel):
    """Base letter model with common fields."""
    subject: str = Field(default="", description="Letter subject/title")
    sender_name: str = Field(default="", description="Sender name")
    sender_email: str = Field(default="", description="Sender email")
    content: str = Field(default="", description="Letter content/body text")
    letter_category: LetterCategory = Field(default=LetterCategory.MISCELLANEOUS)
    action_status: ActionStatus = Field(default=ActionStatus.NO_ACTION_NEEDED)
    has_reminder: bool = Field(default=False)
    ai_suggestion: str = Field(default="", description="AI-generated suggestion")


class LetterCreate(LetterBase):
    """Letter creation request (internal use after OCR)."""
    user_id: str
    letter_date: Optional[int] = None
    original_images: List[str] = Field(default_factory=list)
    ocr_text: str = Field(default="")
    action_due_date: Optional[str] = None
    sender: Optional[Sender] = None
    recipients: Optional[List[Recipient]] = None
    attachments: Optional[List[Attachment]] = None


class LetterUpdate(BaseModel):
    """Letter update request (partial updates)."""
    subject: Optional[str] = None
    letter_category: Optional[LetterCategory] = None
    action_status: Optional[ActionStatus] = None
    has_reminder: Optional[bool] = None
    flagged: Optional[bool] = None
    read: Optional[bool] = None
    user_note: Optional[str] = None
    action_due_date: Optional[str] = None
    archived: Optional[bool] = None
    snoozed: Optional[bool] = None
    snooze_until: Optional[str] = None


class LetterResponse(BaseModel):
    """Letter response with all fields."""
    id: str = Field(..., alias="letter_id")
    subject: str
    sender: Optional[Sender] = None
    sender_name: str = Field(default="")
    sender_email: str = Field(default="")
    recipients: Optional[List[Recipient]] = None
    content: str
    date: str = Field(..., description="ISO timestamp when letter was sent")
    recordCreatedAt: str = Field(..., description="ISO timestamp when record was created")

    # Status & Flags
    read: bool = False
    flagged: bool = False
    snoozed: bool = False
    snoozeUntil: Optional[str] = None
    archived: bool = False
    deleted: bool = False

    # Metadata
    account: str = "default"
    letterCategory: LetterCategory = Field(default=LetterCategory.MISCELLANEOUS)
    actionStatus: ActionStatus = Field(default=ActionStatus.NO_ACTION_NEEDED)
    actionDueDate: Optional[str] = None
    hasReminder: bool = False

    # AI & Content
    aiSuggestion: str = Field(default="")
    userNote: str = Field(default="")
    translatedContent: Optional[Dict[str, str]] = None

    # Attachments & Images
    attachments: Optional[List[Attachment]] = None
    originalImages: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class LetterListResponse(BaseModel):
    """Paginated letter list response."""
    items: List[LetterResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ===== IMAGE UPLOAD MODELS =====

class ImageProcessRequest(BaseModel):
    """Image processing request metadata."""
    includeTranslation: bool = False
    translationLanguage: Optional[str] = None


class ImageProcessResponse(BaseModel):
    """Response from image OCR and analysis."""
    letter_id: str
    subject: str
    sender: str
    content: str
    letterCategory: LetterCategory
    actionStatus: ActionStatus
    hasReminder: bool
    actionDueDate: Optional[str] = None
    aiSuggestion: str
    originalImages: List[str]


# ===== CHAT MODELS =====

class ChatMessage(BaseModel):
    """Chat message."""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    letter_id: str = Field(..., description="Letter ID to chat about")
    message: str = Field(..., min_length=1, description="User's message")


class ChatResponse(BaseModel):
    """Chat response."""
    message: str = Field(..., description="Assistant's response")
    conversation_history: List[ChatMessage] = Field(default_factory=list)


# ===== REMINDER MODELS =====

class ReminderCreate(BaseModel):
    """Reminder creation request."""
    letter_id: str
    reminder_time: int = Field(..., description="Unix timestamp when reminder should trigger")
    message: str = Field(default="", description="Optional reminder message")


class ReminderResponse(BaseModel):
    """Reminder response."""
    id: str = Field(..., alias="reminder_id")
    letter_id: str
    user_id: str
    reminder_time: int
    message: str
    sent: bool
    created_at: int

    class Config:
        populate_by_name = True


class ReminderUpdate(BaseModel):
    """Reminder update request."""
    reminder_time: Optional[int] = None
    message: Optional[str] = None


# ===== SEARCH MODELS =====

class SearchRequest(BaseModel):
    """Search request."""
    q: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


class SearchResponse(BaseModel):
    """Search response."""
    results: List[LetterResponse]
    total: int
    query: str


# ===== TRANSLATION MODELS =====

class TranslationRequest(BaseModel):
    """Translation request."""
    target_language: str = Field(..., description="Target language for translation")


class TranslationResponse(BaseModel):
    """Translation response."""
    translated_content: str
    language: str


# ===== COMMON RESPONSE MODELS =====

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    detail: Optional[Any] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    environment: str
