"""
Manual test script for authentication endpoints.
This is a quick verification script, not a formal test suite.
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

def test_registration():
    """Test user registration."""
    print("\n=== Testing Registration ===")
    
    # Test successful registration
    data = {
        "name": "Test User",
        "phone": "1234567890",
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        print("✓ Registration successful")
        return response.json()['user_id']
    else:
        print("✗ Registration failed")
        return None

def test_duplicate_registration():
    """Test duplicate email/phone rejection."""
    print("\n=== Testing Duplicate Registration ===")
    
    data = {
        "name": "Test User 2",
        "phone": "1234567890",  # Same phone
        "email": "test2@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 409:
        print("✓ Duplicate phone correctly rejected")
    else:
        print("✗ Duplicate phone not rejected")

def test_login():
    """Test user login."""
    print("\n=== Testing Login ===")
    
    # Test with email
    data = {
        "credential": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✓ Login successful")
        return response.json()['access_token']
    else:
        print("✗ Login failed")
        return None

def test_invalid_login():
    """Test login with invalid credentials."""
    print("\n=== Testing Invalid Login ===")
    
    data = {
        "credential": "test@example.com",
        "password": "wrongpassword"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        print("✓ Invalid credentials correctly rejected")
    else:
        print("✗ Invalid credentials not rejected")

def test_session_validation(token):
    """Test session validation."""
    print("\n=== Testing Session Validation ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/validate", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✓ Session validation successful")
    else:
        print("✗ Session validation failed")

if __name__ == "__main__":
    print("Starting Authentication Tests")
    print("Make sure the Flask server is running on http://localhost:5000")
    print("=" * 50)
    
    try:
        # Test registration
        user_id = test_registration()
        
        # Test duplicate registration
        test_duplicate_registration()
        
        # Test login
        token = test_login()
        
        # Test invalid login
        test_invalid_login()
        
        # Test session validation
        if token:
            test_session_validation(token)
        
        print("\n" + "=" * 50)
        print("Tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server.")
        print("Please start the Flask server first: python app.py")
