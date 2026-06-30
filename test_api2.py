import requests
import json

url = "http://127.0.0.1:5000/api/process"
payload = {
    "text": "Testing fresh database",
    "location": "Fresh DB Test",
    "guest_name": "Jane",
    "guest_email": "jane@example.com",
    "guest_phone": "1234567890"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
