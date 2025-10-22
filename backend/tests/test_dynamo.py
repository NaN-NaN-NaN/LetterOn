"""
LetterOn Server - DynamoDB Service Tests
Purpose: Unit tests for DynamoDB operations using moto for mocking
Testing: pytest tests/test_dynamo.py
AWS Deployment: Not deployed (tests only)

These tests validate:
- User CRUD operations
- Letter CRUD operations
- Reminder CRUD operations
- Conversation message operations
"""

import pytest
from moto import mock_dynamodb
import boto3
from decimal import Decimal

from app.services.dynamo import DynamoDBClient
from app.settings import settings


@pytest.fixture
def dynamodb_tables():
    """
    Create mock DynamoDB tables for testing.
    Uses moto to mock AWS DynamoDB service.
    """
    with mock_dynamodb():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create Users table
        users_table = dynamodb.create_table(
            TableName=settings.dynamodb_users_table,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Create Letters table
        letters_table = dynamodb.create_table(
            TableName=settings.dynamodb_letters_table,
            KeySchema=[
                {'AttributeName': 'letter_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'letter_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_created_at', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'record_created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Create Reminders table
        reminders_table = dynamodb.create_table(
            TableName=settings.dynamodb_reminders_table,
            KeySchema=[
                {'AttributeName': 'reminder_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'reminder_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Create Conversations table
        conversations_table = dynamodb.create_table(
            TableName=settings.dynamodb_conversations_table,
            KeySchema=[
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                {'AttributeName': 'letter_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'letter_id-index',
                    'KeySchema': [
                        {'AttributeName': 'letter_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        yield dynamodb


@pytest.fixture
def db_client(dynamodb_tables):
    """Create DynamoDB client instance for testing."""
    return DynamoDBClient()


# ===== USER TESTS =====

def test_create_user(db_client):
    """Test creating a user."""
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "name": "Test User"
    }

    user = db_client.create_user(user_data)

    assert user["email"] == "test@example.com"
    assert user["name"] == "Test User"
    assert "user_id" in user
    assert "created_at" in user


def test_get_user_by_id(db_client):
    """Test retrieving a user by ID."""
    # Create user
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "name": "Test User"
    }
    created_user = db_client.create_user(user_data)

    # Get user by ID
    user = db_client.get_user_by_id(created_user["user_id"])

    assert user is not None
    assert user["user_id"] == created_user["user_id"]
    assert user["email"] == "test@example.com"


def test_get_user_by_email(db_client):
    """Test retrieving a user by email."""
    # Create user
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "name": "Test User"
    }
    db_client.create_user(user_data)

    # Get user by email
    user = db_client.get_user_by_email("test@example.com")

    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["name"] == "Test User"


def test_update_user(db_client):
    """Test updating a user."""
    # Create user
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "name": "Test User"
    }
    created_user = db_client.create_user(user_data)

    # Update user
    updated_user = db_client.update_user(
        created_user["user_id"],
        {"name": "Updated Name"}
    )

    assert updated_user["name"] == "Updated Name"
    assert updated_user["email"] == "test@example.com"


# ===== LETTER TESTS =====

def test_create_letter(db_client):
    """Test creating a letter."""
    # First create a user
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    # Create letter
    letter_data = {
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "sender_name": "John Doe",
        "content": "This is a test letter",
        "letter_category": "miscellaneous",
        "action_status": "no-action-needed"
    }

    letter = db_client.create_letter(letter_data)

    assert letter["subject"] == "Test Letter"
    assert letter["sender_name"] == "John Doe"
    assert "letter_id" in letter
    assert letter["user_id"] == user["user_id"]


def test_get_letter(db_client):
    """Test retrieving a letter."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    created_letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Get letter
    letter = db_client.get_letter(created_letter["letter_id"])

    assert letter is not None
    assert letter["letter_id"] == created_letter["letter_id"]
    assert letter["subject"] == "Test Letter"


def test_get_letters_by_user(db_client):
    """Test retrieving letters for a user."""
    # Create user
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    # Create multiple letters
    for i in range(3):
        db_client.create_letter({
            "user_id": user["user_id"],
            "subject": f"Letter {i}",
            "content": f"Content {i}"
        })

    # Get letters
    result = db_client.get_letters_by_user(user["user_id"], limit=10)

    assert len(result["items"]) == 3


def test_update_letter(db_client):
    """Test updating a letter."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Original Subject",
        "content": "Original content"
    })

    # Update letter
    updated_letter = db_client.update_letter(
        letter["letter_id"],
        {"subject": "Updated Subject", "flagged": True}
    )

    assert updated_letter["subject"] == "Updated Subject"
    assert updated_letter["flagged"] is True


def test_delete_letter_soft(db_client):
    """Test soft deleting a letter."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Soft delete
    success = db_client.delete_letter(letter["letter_id"], soft_delete=True)

    assert success is True

    # Verify letter still exists but marked as deleted
    deleted_letter = db_client.get_letter(letter["letter_id"])
    assert deleted_letter["deleted"] is True


# ===== REMINDER TESTS =====

def test_create_reminder(db_client):
    """Test creating a reminder."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Create reminder
    reminder_data = {
        "user_id": user["user_id"],
        "letter_id": letter["letter_id"],
        "reminder_time": 1705000000,
        "message": "Don't forget!"
    }

    reminder = db_client.create_reminder(reminder_data)

    assert reminder["message"] == "Don't forget!"
    assert reminder["reminder_time"] == 1705000000
    assert "reminder_id" in reminder


def test_get_reminders_by_user(db_client):
    """Test retrieving reminders for a user."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Create reminders
    for i in range(2):
        db_client.create_reminder({
            "user_id": user["user_id"],
            "letter_id": letter["letter_id"],
            "reminder_time": 1705000000 + i,
            "message": f"Reminder {i}"
        })

    # Get reminders
    reminders = db_client.get_reminders_by_user(user["user_id"])

    assert len(reminders) == 2


def test_update_reminder(db_client):
    """Test updating a reminder."""
    # Create user, letter, and reminder
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    reminder = db_client.create_reminder({
        "user_id": user["user_id"],
        "letter_id": letter["letter_id"],
        "reminder_time": 1705000000,
        "message": "Original message"
    })

    # Update reminder
    updated_reminder = db_client.update_reminder(
        reminder["reminder_id"],
        {"message": "Updated message", "sent": True}
    )

    assert updated_reminder["message"] == "Updated message"
    assert updated_reminder["sent"] is True


def test_delete_reminder(db_client):
    """Test deleting a reminder."""
    # Create user, letter, and reminder
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    reminder = db_client.create_reminder({
        "user_id": user["user_id"],
        "letter_id": letter["letter_id"],
        "reminder_time": 1705000000,
        "message": "Test reminder"
    })

    # Delete reminder
    success = db_client.delete_reminder(reminder["reminder_id"])

    assert success is True


# ===== CONVERSATION TESTS =====

def test_create_conversation_message(db_client):
    """Test creating a conversation message."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Create message
    message_data = {
        "letter_id": letter["letter_id"],
        "user_id": user["user_id"],
        "role": "user",
        "content": "What is this letter about?"
    }

    message = db_client.create_conversation_message(message_data)

    assert message["role"] == "user"
    assert message["content"] == "What is this letter about?"
    assert "conversation_id" in message


def test_get_conversation_history(db_client):
    """Test retrieving conversation history."""
    # Create user and letter
    user = db_client.create_user({
        "email": "test@example.com",
        "password_hash": "hash",
        "name": "Test User"
    })

    letter = db_client.create_letter({
        "user_id": user["user_id"],
        "subject": "Test Letter",
        "content": "Test content"
    })

    # Create messages
    db_client.create_conversation_message({
        "letter_id": letter["letter_id"],
        "user_id": user["user_id"],
        "role": "user",
        "content": "Question 1"
    })

    db_client.create_conversation_message({
        "letter_id": letter["letter_id"],
        "user_id": user["user_id"],
        "role": "assistant",
        "content": "Answer 1"
    })

    # Get conversation history
    history = db_client.get_conversation_history(letter["letter_id"])

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


# ===== DATA CONVERSION TESTS =====

def test_python_to_dynamodb_conversion(db_client):
    """Test Python to DynamoDB data type conversion."""
    data = {
        "string": "test",
        "integer": 123,
        "float": 45.67,
        "list": [1, 2.5, "three"],
        "dict": {"nested": 10.5}
    }

    converted = db_client.python_to_dynamodb(data)

    assert isinstance(converted["float"], Decimal)
    assert isinstance(converted["list"][1], Decimal)
    assert isinstance(converted["dict"]["nested"], Decimal)


def test_dynamodb_to_python_conversion(db_client):
    """Test DynamoDB to Python data type conversion."""
    data = {
        "string": "test",
        "decimal": Decimal("45.67"),
        "list": [Decimal("1.5"), Decimal("2")],
        "dict": {"nested": Decimal("10.5")}
    }

    converted = db_client.dynamodb_to_python(data)

    assert isinstance(converted["decimal"], float)
    assert isinstance(converted["list"][0], float)
    assert isinstance(converted["list"][1], int)
    assert isinstance(converted["dict"]["nested"], float)
