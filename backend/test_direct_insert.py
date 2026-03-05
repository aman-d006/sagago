# test_direct.py
import requests
import json

# Your Turso credentials - copy these from your .env or settings
TURSO_URL = "libsql://sagago-aman-d006.aws-us-west-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI2OTY5MTQsImlkIjoiMDE5Y2JjZjYtMWEwMS03NmI1LTljNDgtMWU1NjNjZTgxZmU3IiwicmlkIjoiMjFkYjllNDUtYWM1ZC00YTdmLThmNzMtYTI4NjNiNmU2MjE3In0.JJM_fU0GmetvGuyLmKYTbu9s3MxJ6oU1nwCdT0ohNN9c4-nQUKzmdGzPtJU9jFYin36tMyxV2VQNv_GpOPpSBA"
# Convert to HTTPS URL
https_url = TURSO_URL.replace("libsql://", "https://")

print(f"Testing connection to: {https_url}")

headers = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: Simple SELECT
print("\n=== Test 1: SELECT 1 ===")
payload1 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": "SELECT 1",
                "params": []
            }
        }
    ]
}

try:
    response = requests.post(f"{https_url}/v2/pipeline", json=payload1, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Check users table
print("\n=== Test 2: Check users table ===")
payload2 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": "SELECT COUNT(*) FROM users",
                "params": []
            }
        }
    ]
}

try:
    response = requests.post(f"{https_url}/v2/pipeline", json=payload2, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Try to insert a test user with literal values
print("\n=== Test 3: Insert test user ===")
payload3 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": "INSERT INTO users (username, email, password_hash, is_active) VALUES ('test123', 'test123@test.com', 'hash123', 1)",
                "params": []
            }
        }
    ]
}

try:
    response = requests.post(f"{https_url}/v2/pipeline", json=payload3, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        if 'results' in result and result['results'][0].get('type') == 'error':
            print(f"❌ Insert failed: {result['results'][0]['error']['message']}")
        else:
            print("✅ Insert succeeded!")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Verify the user was inserted
print("\n=== Test 4: Verify insert ===")
payload4 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": "SELECT username, email FROM users WHERE username = 'test123'",
                "params": []
            }
        }
    ]
}

try:
    response = requests.post(f"{https_url}/v2/pipeline", json=payload4, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")


