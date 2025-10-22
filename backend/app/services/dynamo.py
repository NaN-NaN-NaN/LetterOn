"""
LetterOn Server - DynamoDB Service Layer
Purpose: Complete data access layer for all DynamoDB operations
Testing: Use moto for mocking DynamoDB in unit tests
AWS Deployment: Ensure DynamoDB read/write permissions in IAM role

This module provides CRUD operations for:
- Users (LetterOn-Users)
- Letters (LetterOn-Letters)
- Reminders (LetterOn-Reminders)
- Conversations (LetterOn-Conversations)

All functions use boto3 DynamoDB resource for simplified operations.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.settings import settings
from app.utils.helpers import get_current_timestamp, generate_uuid

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """
    DynamoDB client for all database operations.

    Uses boto3 DynamoDB resource for high-level operations.
    """

    def __init__(self):
        """Initialize boto3 DynamoDB resource with configured credentials."""
        aws_config = settings.get_aws_credentials()
        self.dynamodb = boto3.resource('dynamodb', **aws_config)

        # Table references
        self.users_table = self.dynamodb.Table(settings.dynamodb_users_table)
        self.letters_table = self.dynamodb.Table(settings.dynamodb_letters_table)
        self.reminders_table = self.dynamodb.Table(settings.dynamodb_reminders_table)
        self.conversations_table = self.dynamodb.Table(settings.dynamodb_conversations_table)

        logger.info("DynamoDB client initialized")

    # ===== HELPER METHODS =====

    @staticmethod
    def python_to_dynamodb(obj: Any) -> Any:
        """Convert Python objects to DynamoDB compatible format (float -> Decimal)."""
        if isinstance(obj, dict):
            return {k: DynamoDBClient.python_to_dynamodb(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBClient.python_to_dynamodb(v) for v in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        return obj

    @staticmethod
    def dynamodb_to_python(obj: Any) -> Any:
        """Convert DynamoDB objects to Python format (Decimal -> float)."""
        if isinstance(obj, dict):
            return {k: DynamoDBClient.dynamodb_to_python(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBClient.dynamodb_to_python(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return obj

    # ===== USER OPERATIONS =====

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in DynamoDB.

        Args:
            user_data: User information including email, password_hash, name

        Returns:
            Dict: Created user data with user_id

        Example:
            user = db.create_user({
                "email": "user@example.com",
                "password_hash": "hashed_password",
                "name": "John Doe"
            })
        """
        user_id = generate_uuid()
        timestamp = get_current_timestamp()

        item = {
            "user_id": user_id,
            "email": user_data["email"],
            "password_hash": user_data["password_hash"],
            "name": user_data.get("name", ""),
            "created_at": timestamp,
            "updated_at": timestamp
        }

        try:
            self.users_table.put_item(Item=self.python_to_dynamodb(item))
            logger.info(f"User created: {user_id}")
            return self.dynamodb_to_python(item)

        except ClientError as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id."""
        try:
            response = self.users_table.get_item(Key={"user_id": user_id})
            item = response.get("Item")
            return self.dynamodb_to_python(item) if item else None

        except ClientError as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address using GSI.

        Args:
            email: User email address

        Returns:
            Dict: User data or None if not found
        """
        try:
            response = self.users_table.query(
                IndexName="email-index",
                KeyConditionExpression=Key("email").eq(email)
            )

            items = response.get("Items", [])
            if not items:
                return None

            return self.dynamodb_to_python(items[0])

        except ClientError as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user fields."""
        updates["updated_at"] = get_current_timestamp()

        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
        expr_attr_names = {f"#{k}": k for k in updates.keys()}
        expr_attr_values = {f":{k}": v for k, v in self.python_to_dynamodb(updates).items()}

        try:
            response = self.users_table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW"
            )

            return self.dynamodb_to_python(response["Attributes"])

        except ClientError as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise

    # ===== LETTER OPERATIONS =====

    def create_letter(self, letter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new letter in DynamoDB.

        Args:
            letter_data: Letter information

        Returns:
            Dict: Created letter data with letter_id
        """
        letter_id = generate_uuid()
        timestamp = get_current_timestamp()

        item = {
            "letter_id": letter_id,
            "user_id": letter_data["user_id"],
            "subject": letter_data.get("subject", ""),
            "sender_name": letter_data.get("sender_name", ""),
            "sender_email": letter_data.get("sender_email", ""),
            "content": letter_data.get("content", ""),
            "letter_date": letter_data.get("letter_date", timestamp),
            "record_created_at": timestamp,
            "read": letter_data.get("read", False),
            "flagged": letter_data.get("flagged", False),
            "snoozed": letter_data.get("snoozed", False),
            "archived": letter_data.get("archived", False),
            "deleted": letter_data.get("deleted", False),
            "account": letter_data.get("account", "default"),
            "letter_category": letter_data.get("letter_category", "miscellaneous"),
            "action_status": letter_data.get("action_status", "no-action-needed"),
            "has_reminder": letter_data.get("has_reminder", False),
            "original_images": letter_data.get("original_images", []),
            "ocr_text": letter_data.get("ocr_text", ""),
            "ai_suggestion": letter_data.get("ai_suggestion", ""),
            "user_note": letter_data.get("user_note", ""),
        }

        # Optional fields
        if "snooze_until" in letter_data:
            item["snooze_until"] = letter_data["snooze_until"]
        if "action_due_date" in letter_data:
            item["action_due_date"] = letter_data["action_due_date"]
        if "sender" in letter_data:
            item["sender"] = letter_data["sender"]
        if "recipients" in letter_data:
            item["recipients"] = letter_data["recipients"]
        if "attachments" in letter_data:
            item["attachments"] = letter_data["attachments"]

        try:
            self.letters_table.put_item(Item=self.python_to_dynamodb(item))
            logger.info(f"Letter created: {letter_id}")
            return self.dynamodb_to_python(item)

        except ClientError as e:
            logger.error(f"Error creating letter: {str(e)}")
            raise

    def get_letter(self, letter_id: str) -> Optional[Dict[str, Any]]:
        """Get letter by letter_id."""
        try:
            response = self.letters_table.get_item(Key={"letter_id": letter_id})
            item = response.get("Item")
            return self.dynamodb_to_python(item) if item else None

        except ClientError as e:
            logger.error(f"Error getting letter {letter_id}: {str(e)}")
            return None

    def get_letters_by_user(
        self,
        user_id: str,
        limit: int = 50,
        last_evaluated_key: Optional[Dict] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get all letters for a user with optional filters.

        Args:
            user_id: User ID
            limit: Maximum number of results
            last_evaluated_key: For pagination
            filters: Optional filters (e.g., {"archived": False, "deleted": False})

        Returns:
            Dict with "items" and "last_evaluated_key"
        """
        try:
            query_params = {
                "IndexName": "user_id-index",
                "KeyConditionExpression": Key("user_id").eq(user_id),
                "Limit": limit,
                "ScanIndexForward": False  # Sort by record_created_at descending
            }

            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key

            # Add filters
            if filters:
                filter_expressions = []
                for key, value in filters.items():
                    if value is not None:
                        filter_expressions.append(Attr(key).eq(value))

                if filter_expressions:
                    combined_filter = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr
                    query_params["FilterExpression"] = combined_filter

            response = self.letters_table.query(**query_params)

            return {
                "items": self.dynamodb_to_python(response.get("Items", [])),
                "last_evaluated_key": response.get("LastEvaluatedKey")
            }

        except ClientError as e:
            logger.error(f"Error querying letters for user {user_id}: {str(e)}")
            raise

    def update_letter(self, letter_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update letter fields.

        Args:
            letter_id: Letter ID
            updates: Dictionary of fields to update

        Returns:
            Dict: Updated letter data
        """
        # Build update expression
        update_expr_parts = []
        expr_attr_names = {}
        expr_attr_values = {}

        for key, value in updates.items():
            update_expr_parts.append(f"#{key} = :{key}")
            expr_attr_names[f"#{key}"] = key
            expr_attr_values[f":{key}"] = value

        update_expr = "SET " + ", ".join(update_expr_parts)

        try:
            response = self.letters_table.update_item(
                Key={"letter_id": letter_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=self.python_to_dynamodb(expr_attr_values),
                ReturnValues="ALL_NEW"
            )

            logger.info(f"Letter updated: {letter_id}")
            return self.dynamodb_to_python(response["Attributes"])

        except ClientError as e:
            logger.error(f"Error updating letter {letter_id}: {str(e)}")
            raise

    def delete_letter(self, letter_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a letter (soft delete by default).

        Args:
            letter_id: Letter ID
            soft_delete: If True, mark as deleted. If False, remove from DB.

        Returns:
            bool: True if successful
        """
        try:
            if soft_delete:
                self.update_letter(letter_id, {"deleted": True})
            else:
                self.letters_table.delete_item(Key={"letter_id": letter_id})

            logger.info(f"Letter deleted: {letter_id} (soft={soft_delete})")
            return True

        except ClientError as e:
            logger.error(f"Error deleting letter {letter_id}: {str(e)}")
            return False

    def search_letters(self, user_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search letters by text (simple scan for MVP).

        Args:
            user_id: User ID
            query: Search query string
            limit: Maximum results

        Returns:
            List of matching letters

        Note: This uses a scan operation which is expensive.
        For production, consider using Amazon OpenSearch or DynamoDB Streams.
        """
        try:
            query_lower = query.lower()

            response = self.letters_table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id),
                FilterExpression=(
                    Attr("content").contains(query) |
                    Attr("subject").contains(query) |
                    Attr("sender_name").contains(query) |
                    Attr("ocr_text").contains(query)
                ),
                Limit=limit
            )

            return self.dynamodb_to_python(response.get("Items", []))

        except ClientError as e:
            logger.error(f"Error searching letters: {str(e)}")
            return []

    # ===== REMINDER OPERATIONS =====

    def create_reminder(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder."""
        reminder_id = generate_uuid()
        timestamp = get_current_timestamp()

        item = {
            "reminder_id": reminder_id,
            "user_id": reminder_data["user_id"],
            "letter_id": reminder_data["letter_id"],
            "reminder_time": reminder_data["reminder_time"],
            "message": reminder_data.get("message", ""),
            "sent": reminder_data.get("sent", False),
            "created_at": timestamp,
        }

        try:
            self.reminders_table.put_item(Item=self.python_to_dynamodb(item))
            logger.info(f"Reminder created: {reminder_id}")
            return self.dynamodb_to_python(item)

        except ClientError as e:
            logger.error(f"Error creating reminder: {str(e)}")
            raise

    def get_reminders_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all reminders for a user."""
        try:
            response = self.reminders_table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id)
            )

            return self.dynamodb_to_python(response.get("Items", []))

        except ClientError as e:
            logger.error(f"Error getting reminders for user {user_id}: {str(e)}")
            return []

    def get_pending_reminders(self, current_time: int) -> List[Dict[str, Any]]:
        """
        Get all pending reminders that should be sent.

        Args:
            current_time: Current timestamp

        Returns:
            List of reminders where reminder_time <= current_time and sent=False
        """
        try:
            # Note: This requires a scan, which is not ideal for production
            # Consider using a GSI on sent + reminder_time for better performance
            response = self.reminders_table.scan(
                FilterExpression=Attr("sent").eq(False) & Attr("reminder_time").lte(current_time)
            )

            return self.dynamodb_to_python(response.get("Items", []))

        except ClientError as e:
            logger.error(f"Error getting pending reminders: {str(e)}")
            return []

    def update_reminder(self, reminder_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update reminder fields."""
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
        expr_attr_names = {f"#{k}": k for k in updates.keys()}
        expr_attr_values = {f":{k}": v for k, v in self.python_to_dynamodb(updates).items()}

        try:
            response = self.reminders_table.update_item(
                Key={"reminder_id": reminder_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW"
            )

            return self.dynamodb_to_python(response["Attributes"])

        except ClientError as e:
            logger.error(f"Error updating reminder {reminder_id}: {str(e)}")
            raise

    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder."""
        try:
            self.reminders_table.delete_item(Key={"reminder_id": reminder_id})
            logger.info(f"Reminder deleted: {reminder_id}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting reminder {reminder_id}: {str(e)}")
            return False

    # ===== CONVERSATION OPERATIONS =====

    def create_conversation_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation message."""
        conversation_id = generate_uuid()
        timestamp = get_current_timestamp()

        item = {
            "conversation_id": conversation_id,
            "letter_id": message_data["letter_id"],
            "user_id": message_data["user_id"],
            "role": message_data["role"],  # "user" or "assistant"
            "content": message_data["content"],
            "timestamp": timestamp,
        }

        try:
            self.conversations_table.put_item(Item=self.python_to_dynamodb(item))
            logger.info(f"Conversation message created: {conversation_id}")
            return self.dynamodb_to_python(item)

        except ClientError as e:
            logger.error(f"Error creating conversation message: {str(e)}")
            raise

    def get_conversation_history(
        self,
        letter_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a letter.

        Args:
            letter_id: Letter ID
            limit: Maximum number of messages

        Returns:
            List of conversation messages sorted by timestamp ascending
        """
        try:
            response = self.conversations_table.query(
                IndexName="letter_id-index",
                KeyConditionExpression=Key("letter_id").eq(letter_id),
                Limit=limit,
                ScanIndexForward=True  # Ascending order (oldest first)
            )

            return self.dynamodb_to_python(response.get("Items", []))

        except ClientError as e:
            logger.error(f"Error getting conversation history for letter {letter_id}: {str(e)}")
            return []


# Global DynamoDB client instance
dynamodb_client = DynamoDBClient()
