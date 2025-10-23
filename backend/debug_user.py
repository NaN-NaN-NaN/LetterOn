#!/usr/bin/env python3
"""Debug script to check user in DynamoDB"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/Users/nan/Project/LetterOn/backend')

from app.settings import settings
from app.services.dynamo import dynamodb_client

print("=" * 60)
print("DynamoDB Configuration Debug")
print("=" * 60)
print(f"Region: {settings.aws_region}")
print(f"Endpoint: {settings.dynamodb_endpoint or '(AWS DynamoDB)'}")
print(f"Users Table: {settings.dynamodb_users_table}")
print("=" * 60)

# Get email from command line
if len(sys.argv) < 2:
    print("\nUsage: python debug_user.py <email>")
    sys.exit(1)

email = sys.argv[1]

print(f"\nLooking up user: {email}")
print("-" * 60)

try:
    user = dynamodb_client.get_user_by_email(email)

    if user:
        print("✅ User found!")
        print(f"User ID: {user.get('user_id')}")
        print(f"Name: {user.get('name')}")
        print(f"Email: {user.get('email')}")
        print(f"Password Hash: {user.get('password_hash')[:50]}...")
        print(f"Created: {user.get('created_at')}")
    else:
        print("❌ User NOT found in database")
        print("\nPossible reasons:")
        print("1. User doesn't exist in this database")
        print("2. Wrong database (local vs AWS)")
        print("3. Wrong table name")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("=" * 60)
