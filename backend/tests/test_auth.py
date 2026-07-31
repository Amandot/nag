"""
Unit tests for authentication endpoints.

Requirements: 1.1, 1.2, 1.3, 1.4
"""
import pytest
from app import create_app
from models import db
from models.user import User
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'name': 'John Doe',
        'phone': '1234567890',
        'email': 'john@example.com',
        'password': 'securepassword123'
    }


class TestRegistration:
    """Test user registration endpoint."""
    
    def test_successful_registration(self, client, sample_user_data):
        """Test successful user registration.
        
        Requirements: 1.1
        """
        response = client.post('/api/auth/register', json=sample_user_data)
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'user_id' in data
        assert data['message'] == 'User registered successfully'
        assert data['user_id'] is not None
    
    def test_duplicate_email_rejection(self, client, sample_user_data):
        """Test that duplicate email is rejected.
        
        Requirements: 1.2
        """
        # Register first user
        client.post('/api/auth/register', json=sample_user_data)
        
        # Try to register with same email but different phone
        duplicate_data = sample_user_data.copy()
        duplicate_data['phone'] = '9876543210'
        
        response = client.post('/api/auth/register', json=duplicate_data)
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
        assert 'Email already registered' in data['error']
    
    def test_duplicate_phone_rejection(self, client, sample_user_data):
        """Test that duplicate phone is rejected.
        
        Requirements: 1.2
        """
        # Register first user
        client.post('/api/auth/register', json=sample_user_data)
        
        # Try to register with same phone but different email
        duplicate_data = sample_user_data.copy()
        duplicate_data['email'] = 'different@example.com'
        
        response = client.post('/api/auth/register', json=duplicate_data)
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
        assert 'Phone number already registered' in data['error']
    
    def test_missing_required_fields(self, client):
        """Test registration with missing fields.
        
        Requirements: 1.1
        """
        incomplete_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
            # Missing phone and password
        }
        
        response = client.post('/api/auth/register', json=incomplete_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_email_format(self, client, sample_user_data):
        """Test registration with invalid email format.
        
        Requirements: 1.1
        """
        invalid_data = sample_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = client.post('/api/auth/register', json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid email format' in data['error']
    
    def test_invalid_phone_format(self, client, sample_user_data):
        """Test registration with invalid phone format.
        
        Requirements: 1.1
        """
        invalid_data = sample_user_data.copy()
        invalid_data['phone'] = 'abc123'
        
        response = client.post('/api/auth/register', json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid phone format' in data['error']
    
    def test_weak_password(self, client, sample_user_data):
        """Test registration with weak password.
        
        Requirements: 1.1
        """
        weak_data = sample_user_data.copy()
        weak_data['password'] = '123'
        
        response = client.post('/api/auth/register', json=weak_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'at least 6 characters' in data['error']


class TestLogin:
    """Test user login endpoint."""
    
    def test_successful_login_with_email(self, client, sample_user_data):
        """Test successful login using email.
        
        Requirements: 1.3
        """
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Login with email
        login_data = {
            'credential': sample_user_data['email'],
            'password': sample_user_data['password']
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user_id' in data
        assert data['email'] == sample_user_data['email']
        assert data['name'] == sample_user_data['name']
    
    def test_successful_login_with_phone(self, client, sample_user_data):
        """Test successful login using phone.
        
        Requirements: 1.3
        """
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Login with phone
        login_data = {
            'credential': sample_user_data['phone'],
            'password': sample_user_data['password']
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user_id' in data
    
    def test_login_with_invalid_email(self, client):
        """Test login with non-existent email.
        
        Requirements: 1.4
        """
        login_data = {
            'credential': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid credentials' in data['error']
    
    def test_login_with_wrong_password(self, client, sample_user_data):
        """Test login with incorrect password.
        
        Requirements: 1.4
        """
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Try to login with wrong password
        login_data = {
            'credential': sample_user_data['email'],
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid credentials' in data['error']
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials.
        
        Requirements: 1.3
        """
        response = client.post('/api/auth/login', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_invalid_credential_format(self, client):
        """Test login with invalid credential format.
        
        Requirements: 1.3
        """
        login_data = {
            'credential': 'invalid',
            'password': 'somepassword'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid credential format' in data['error']


class TestSessionValidation:
    """Test session validation endpoint."""
    
    def test_validate_valid_session(self, client, sample_user_data):
        """Test session validation with valid token.
        
        Requirements: 1.3, 15.3
        """
        # Register and login
        client.post('/api/auth/register', json=sample_user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': sample_user_data['email'],
            'password': sample_user_data['password']
        })
        
        token = login_response.get_json()['access_token']
        
        # Validate session
        response = client.get('/api/auth/validate', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user_id' in data
        assert data['email'] == sample_user_data['email']
        assert data['name'] == sample_user_data['name']
        assert 'trust_score' in data
    
    def test_validate_without_token(self, client):
        """Test session validation without token.
        
        Requirements: 15.3
        """
        response = client.get('/api/auth/validate')
        
        assert response.status_code == 401
    
    def test_validate_with_invalid_token(self, client):
        """Test session validation with invalid token.
        
        Requirements: 15.3
        """
        response = client.get('/api/auth/validate', headers={
            'Authorization': 'Bearer invalid_token'
        })
        
        assert response.status_code == 422
