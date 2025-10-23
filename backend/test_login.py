#!/usr/bin/env python3
"""Quick script to test login and debug 401 errors"""

import requests
import json
import sys

# Get credentials from command line
if len(sys.argv) < 3:
    print("Usage: python test_login.py <email> <password>")
    sys.exit(1)

email = sys.argv[1]
password = sys.argv[2]

print(f"Testing login for: {email}")
print("=" * 50)

# Test login
url = "http://localhost:8000/auth/login"
payload = {
    "email": email,
    "password": password
}

response = requests.post(url, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✅ Login successful!")
    print(f"Token: {response.json()['token'][:50]}...")
else:
    print("\n❌ Login failed!")
    print(f"Error: {response.json()['detail']}")
