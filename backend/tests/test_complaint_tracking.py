"""
Tests for complaint tracking endpoints.

Requirements: 9.1, 9.2, 9.3, 7.3
"""
import pytest
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Status, Category, PriorityLevel
from models.status_history import StatusHistory
from config import TestingConfig
from datetime import datetime
import bcrypt


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


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
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            name="Test User",
            phone="1234567890",
            email="test@example.com",
            password_hash=hash_password("password123")
        )
        db.session.add(user)
        db.session.commit()
        
        user_id = user.user_id
        
    yield user_id
    
    # Cleanup
    with app.app_context():
        User.query.filter_by(user_id=user_id).delete()
        db.session.commit()


@pytest.fixture
def test_complaint(app, test_user):
    """Create a test complaint."""
    with app.app_context():
        complaint = Complaint(
            user_id=test_user,
            description="Test complaint description",
            category=Category.WATER_SUPPLY,
            status=Status.SUBMITTED,
            priority_level=PriorityLevel.MEDIUM,
            impact_score=50,
            explanation="Test explanation",
            created_at=datetime.utcnow()
        )
        db.session.add(complaint)
        db.session.flush()  # Flush to get complaint_id
        
        # Add initial status history
        status_history = StatusHistory(
            complaint_id=complaint.complaint_id,
            old_status=None,
            new_status=Status.SUBMITTED.value,
            changed_by=test_user,
            notes="Complaint submitted"
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        complaint_id = complaint.complaint_id
        
    yield complaint_id
    
    # Cleanup
    with app.app_context():
        StatusHistory.query.filter_by(complaint_id=complaint_id).delete()
        Complaint.query.filter_by(complaint_id=complaint_id).delete()
        db.session.commit()


@pytest.fixture
def auth_token(client, test_user, app):
    """Get authentication token for test user."""
    with app.app_context():
        user = User.query.get(test_user)
        
    response = client.post('/api/auth/login', json={
        'credential': user.email,
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    return data['access_token']


class TestComplaintRetrieval:
    """Test complaint status retrieval endpoint."""
    
    def test_get_complaint_success(self, client, test_complaint, auth_token, app):
        """Test successful complaint retrieval."""
        response = client.get(
            f'/api/complaints/{test_complaint}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['complaint_id'] == test_complaint
        assert data['description'] == "Test complaint description"
        assert data['category'] == "Water Supply"
        assert data['status'] == "Submitted"
        assert data['priority_level'] == "Medium"
        assert data['impact_score'] == 50
        assert data['explanation'] == "Test explanation"
        assert 'duplicate_count' in data
    
    def test_get_complaint_not_found(self, client, auth_token):
        """Test complaint retrieval with invalid ID."""
        response = client.get(
            '/api/complaints/invalid-id',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_get_complaint_unauthorized(self, client, test_complaint):
        """Test complaint retrieval without authentication."""
        response = client.get(f'/api/complaints/{test_complaint}')
        
        assert response.status_code == 401


class TestComplaintHistory:
    """Test complaint history endpoint."""
    
    def test_get_complaint_history_success(self, client, test_complaint, auth_token, app):
        """Test successful complaint history retrieval."""
        # Add another status change
        with app.app_context():
            complaint = Complaint.query.get(test_complaint)
            complaint.status = Status.ASSIGNED
            
            status_history = StatusHistory(
                complaint_id=test_complaint,
                old_status=Status.SUBMITTED.value,
                new_status=Status.ASSIGNED.value,
                changed_by=complaint.user_id,
                notes="Assigned to officer"
            )
            db.session.add(status_history)
            db.session.commit()
        
        response = client.get(
            f'/api/complaints/{test_complaint}/history',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['complaint_id'] == test_complaint
        assert 'history' in data
        assert len(data['history']) >= 2
        
        # Verify history entries are ordered by timestamp
        history = data['history']
        assert history[0]['old_status'] is None
        assert history[0]['new_status'] == "Submitted"
        assert history[1]['old_status'] == "Submitted"
        assert history[1]['new_status'] == "Assigned"
    
    def test_get_complaint_history_not_found(self, client, auth_token):
        """Test complaint history retrieval with invalid ID."""
        response = client.get(
            '/api/complaints/invalid-id/history',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 404
    
    def test_get_complaint_history_unauthorized(self, client, test_complaint):
        """Test complaint history retrieval without authentication."""
        response = client.get(f'/api/complaints/{test_complaint}/history')
        
        assert response.status_code == 401


class TestUserComplaints:
    """Test user complaints list endpoint."""
    
    def test_get_user_complaints_success(self, client, test_user, test_complaint, auth_token, app):
        """Test successful user complaints retrieval."""
        # Create another complaint for the same user
        with app.app_context():
            complaint2 = Complaint(
                user_id=test_user,
                description="Second test complaint",
                category=Category.ELECTRICITY,
                status=Status.SUBMITTED,
                priority_level=PriorityLevel.HIGH,
                impact_score=70,
                explanation="Test explanation 2",
                created_at=datetime.utcnow()
            )
            db.session.add(complaint2)
            db.session.commit()
            complaint2_id = complaint2.complaint_id
        
        try:
            response = client.get(
                f'/api/complaints/user/{test_user}',
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['user_id'] == test_user
            assert data['total_complaints'] >= 2
            assert 'complaints' in data
            assert len(data['complaints']) >= 2
            
            # Verify complaints are ordered by creation date (newest first)
            complaints = data['complaints']
            assert all('complaint_id' in c for c in complaints)
            assert all('status' in c for c in complaints)
            assert all('duplicate_count' in c for c in complaints)
        
        finally:
            # Cleanup
            with app.app_context():
                Complaint.query.filter_by(complaint_id=complaint2_id).delete()
                db.session.commit()
    
    def test_get_user_complaints_empty(self, client, app, auth_token):
        """Test user complaints retrieval with no complaints."""
        # Create a new user with no complaints
        with app.app_context():
            user = User(
                name="Empty User",
                phone="9999999999",
                email="empty@example.com",
                password_hash=hash_password("password123")
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.user_id
        
        try:
            # Login as the new user
            response = client.post('/api/auth/login', json={
                'credential': 'empty@example.com',
                'password': 'password123'
            })
            token = response.get_json()['access_token']
            
            response = client.get(
                f'/api/complaints/user/{user_id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['user_id'] == user_id
            assert data['total_complaints'] == 0
            assert data['complaints'] == []
        
        finally:
            # Cleanup
            with app.app_context():
                User.query.filter_by(user_id=user_id).delete()
                db.session.commit()
    
    def test_get_user_complaints_forbidden(self, client, test_user, auth_token, app):
        """Test user complaints retrieval for another user."""
        # Create another user
        with app.app_context():
            user2 = User(
                name="Other User",
                phone="8888888888",
                email="other@example.com",
                password_hash=hash_password("password123")
            )
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.user_id
        
        try:
            # Try to access other user's complaints
            response = client.get(
                f'/api/complaints/user/{user2_id}',
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data
        
        finally:
            # Cleanup
            with app.app_context():
                User.query.filter_by(user_id=user2_id).delete()
                db.session.commit()
    
    def test_get_user_complaints_unauthorized(self, client, test_user):
        """Test user complaints retrieval without authentication."""
        response = client.get(f'/api/complaints/user/{test_user}')
        
        assert response.status_code == 401
