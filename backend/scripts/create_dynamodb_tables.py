"""
LetterOn Server - DynamoDB Table Creation Script
Purpose: Create all required DynamoDB tables with proper schema
Testing: python scripts/create_dynamodb_tables.py
AWS Deployment: Run once during initial setup

This script creates:
- LetterOn-Users table with email GSI
- LetterOn-Letters table with user_id GSI
- LetterOn-Reminders table with user_id GSI
- LetterOn-Conversations table with letter_id GSI
"""

import boto3
import sys
import time
from botocore.exceptions import ClientError

# Load settings
try:
    from app.settings import settings
except ImportError:
    print("Error: Cannot import settings. Make sure you're in the project root directory.")
    sys.exit(1)


def create_tables():
    """Create all DynamoDB tables for LetterOn."""

    # Initialize DynamoDB client
    aws_config = settings.get_aws_credentials()
    dynamodb = boto3.client('dynamodb', **aws_config)

    print("Creating DynamoDB tables...")
    print(f"Region: {settings.aws_region}")

    tables_created = []

    # ===== CREATE USERS TABLE =====
    try:
        print(f"\n1. Creating table: {settings.dynamodb_users_table}")
        dynamodb.create_table(
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
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'LetterOn'},
                {'Key': 'Environment', 'Value': settings.environment}
            ]
        )
        print(f"✓ {settings.dynamodb_users_table} created successfully")
        tables_created.append(settings.dynamodb_users_table)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ {settings.dynamodb_users_table} already exists")
        else:
            print(f"✗ Error creating {settings.dynamodb_users_table}: {e}")

    # ===== CREATE LETTERS TABLE =====
    try:
        print(f"\n2. Creating table: {settings.dynamodb_letters_table}")
        dynamodb.create_table(
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
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'LetterOn'},
                {'Key': 'Environment', 'Value': settings.environment}
            ]
        )
        print(f"✓ {settings.dynamodb_letters_table} created successfully")
        tables_created.append(settings.dynamodb_letters_table)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ {settings.dynamodb_letters_table} already exists")
        else:
            print(f"✗ Error creating {settings.dynamodb_letters_table}: {e}")

    # ===== CREATE REMINDERS TABLE =====
    try:
        print(f"\n3. Creating table: {settings.dynamodb_reminders_table}")
        dynamodb.create_table(
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
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'LetterOn'},
                {'Key': 'Environment', 'Value': settings.environment}
            ]
        )
        print(f"✓ {settings.dynamodb_reminders_table} created successfully")
        tables_created.append(settings.dynamodb_reminders_table)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ {settings.dynamodb_reminders_table} already exists")
        else:
            print(f"✗ Error creating {settings.dynamodb_reminders_table}: {e}")

    # ===== CREATE CONVERSATIONS TABLE =====
    try:
        print(f"\n4. Creating table: {settings.dynamodb_conversations_table}")
        dynamodb.create_table(
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
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'LetterOn'},
                {'Key': 'Environment', 'Value': settings.environment}
            ]
        )
        print(f"✓ {settings.dynamodb_conversations_table} created successfully")
        tables_created.append(settings.dynamodb_conversations_table)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ {settings.dynamodb_conversations_table} already exists")
        else:
            print(f"✗ Error creating {settings.dynamodb_conversations_table}: {e}")

    # Wait for tables to become active
    if tables_created:
        print("\n⏳ Waiting for tables to become active...")
        waiter = dynamodb.get_waiter('table_exists')

        for table_name in tables_created:
            try:
                waiter.wait(
                    TableName=table_name,
                    WaiterConfig={'Delay': 2, 'MaxAttempts': 30}
                )
                print(f"✓ {table_name} is now active")
            except Exception as e:
                print(f"⚠ Error waiting for {table_name}: {e}")

    print("\n" + "="*60)
    print("✅ DynamoDB table setup complete!")
    print("="*60)

    # Print table summary
    print("\nCreated/Verified Tables:")
    print(f"  • {settings.dynamodb_users_table} (Users)")
    print(f"  • {settings.dynamodb_letters_table} (Letters)")
    print(f"  • {settings.dynamodb_reminders_table} (Reminders)")
    print(f"  • {settings.dynamodb_conversations_table} (Conversations)")

    print("\nNext steps:")
    print("  1. Verify tables in AWS Console: https://console.aws.amazon.com/dynamodb")
    print("  2. Run the FastAPI server: uvicorn app.main:app --reload")
    print("  3. Test endpoints at: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
