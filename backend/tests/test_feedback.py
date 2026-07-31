"""
Unit tests for feedback service and endpoints.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""
import pytest
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Status, PriorityLevel, Category
from models.feedback import Feedback
from config import TestingConfig
from datetime import datetime


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
            name='Test User',
            phone='1234567890',
            email='test@example.com',
            password_hash='hashed_password',
            trust_score=50
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


@pytest.fixture
def test_resolved_complaint(app, auth_token):
    """Create a resolved test complaint for the auth user."""
    token, user_id = auth_token
    with app.app_context():
        complaint = Complaint(
            user_id=user_id,
            description='Test complaint',
            category=Category.WATER_SUPPLY,
            status=Status.RESOLVED,
            priority_level=PriorityLevel.MEDIUM,
            resolved_at=datetime.utcnow()
        )
        db.session.add(complaint)
        db.session.commit()
        return complaint.complaint_id


@pytest.fixture
def test_unresolved_complaint(app, auth_token):
    """Create an unresolved test complaint for the auth user."""
    token, user_id = auth_token
    with app.app_context():
        complaint = Complaint(
            user_id=user_id,
            description='Test complaint',
            category=Category.WATER_SUPPLY,
            status=Status.SUBMITTED,
            priority_level=PriorityLevel.MEDIUM
        )
        db.session.add(complaint)
        db.session.commit()
        return complaint.complaint_id


@pytest.fixture
def auth_token(client, app):
    """Get authentication token for test user."""
    with app.app_context():
        from bcrypt import hashpw, gensalt
        
        # Create user directly in database with proper password hash
        user = User(
            name='Auth Test User',
            phone='9999999999',
            email='authtest@example.com',
            password_hash=hashpw('password123'.encode('utf-8'), gensalt()).decode('utf-8'),
            trust_score=50
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id
    
    # Login
    response = client.post('/api/auth/login', json={
        'credential': 'authtest@example.com',
        'password': 'password123'
    })
    
    return response.get_json()['access_token'], user_id


class TestFeedbackSubmission:
    """Test feedback submission endpoint."""
    
    def test_submit_feedback_success(self, client, test_resolved_complaint, auth_token):
        """Test successful feedback submission.
        
        Requirements: 13.1, 13.2
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5,
                'comments': 'Great service!'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'feedback_id' in data
        assert data['rating'] == 5
        assert data['comments'] == 'Great service!'
        assert 'new_trust_score' in data
    
    def test_submit_feedback_without_comments(self, client, test_resolved_complaint, auth_token):
        """Test feedback submission without comments.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 4
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['rating'] == 4
        assert data['comments'] is None
    
    def test_submit_feedback_missing_rating(self, client, test_resolved_complaint, auth_token):
        """Test feedback submission without rating.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'comments': 'Good service'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Rating is required' in data['error']
    
    def test_submit_feedback_invalid_rating(self, client, test_resolved_complaint, auth_token):
        """Test feedback submission with invalid rating.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 6  # Invalid: should be 1-5
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_submit_feedback_for_unresolved_complaint(self, client, test_unresolved_complaint, auth_token):
        """Test feedback submission for unresolved complaint.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_unresolved_complaint}/feedback',
            json={
                'rating': 5,
                'comments': 'Great!'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'resolved' in data['error'].lower()
    
    def test_submit_duplicate_feedback(self, client, test_resolved_complaint, auth_token):
        """Test submitting feedback twice for same complaint.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        # Submit first feedback
        client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5,
                'comments': 'Great!'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Try to submit again
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 4,
                'comments': 'Changed my mind'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
        assert 'already been submitted' in data['error']
    
    def test_submit_feedback_without_authentication(self, client, test_resolved_complaint):
        """Test feedback submission without authentication.
        
        Requirements: 13.1
        """
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5
            }
        )
        
        assert response.status_code == 401


class TestTrustScoreUpdate:
    """Test trust score update logic."""
    
    def test_trust_score_increase_positive_feedback(self, client, test_resolved_complaint, auth_token, app):
        """Test trust score increases with positive feedback.
        
        Requirements: 13.3, 13.5
        """
        token, user_id = auth_token
        # Submit positive feedback (rating >= 4)
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'new_trust_score' in data
        # Trust score should increase by 2 for rating >= 4
        assert data['new_trust_score'] == 52  # 50 + 2
    
    def test_trust_score_increase_neutral_feedback(self, client, test_resolved_complaint, auth_token, app):
        """Test trust score increases slightly with neutral feedback.
        
        Requirements: 13.3, 13.5
        """
        token, user_id = auth_token
        # Submit neutral feedback (rating = 3)
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 3
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'new_trust_score' in data
        # Trust score should increase by 1 for rating = 3
        assert data['new_trust_score'] == 51  # 50 + 1
    
    def test_trust_score_decrease_negative_feedback(self, client, test_resolved_complaint, auth_token, app):
        """Test trust score decreases with negative feedback.
        
        Requirements: 13.3, 13.5
        """
        token, user_id = auth_token
        # Submit negative feedback (rating < 3)
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 2
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'new_trust_score' in data
        # Trust score should decrease by 1 for rating < 3
        assert data['new_trust_score'] == 49  # 50 - 1


class TestDissatisfactionFlagging:
    """Test dissatisfaction flagging."""
    
    def test_dissatisfaction_flagged_low_rating(self, client, test_resolved_complaint, auth_token):
        """Test that low ratings are flagged for review.
        
        Requirements: 13.3, 13.5
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 2,
                'comments': 'Not satisfied with resolution'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'flagged_for_review' in data
        assert data['flagged_for_review'] is True
    
    def test_dissatisfaction_not_flagged_high_rating(self, client, test_resolved_complaint, auth_token):
        """Test that high ratings are not flagged.
        
        Requirements: 13.3
        """
        token, user_id = auth_token
        response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        # Should not have flagged_for_review key or it should be False
        assert data.get('flagged_for_review', False) is False


class TestFeedbackRetrieval:
    """Test feedback retrieval endpoint."""
    
    def test_get_feedback_success(self, client, test_resolved_complaint, auth_token):
        """Test successful feedback retrieval.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        # Submit feedback first
        submit_response = client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 4,
                'comments': 'Good service'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        feedback_id = submit_response.get_json()['feedback_id']
        
        # Retrieve feedback
        response = client.get(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['feedback_id'] == feedback_id
        assert data['rating'] == 4
        assert data['comments'] == 'Good service'
    
    def test_get_feedback_not_found(self, client, test_resolved_complaint, auth_token):
        """Test feedback retrieval when no feedback exists.
        
        Requirements: 13.1
        """
        token, user_id = auth_token
        response = client.get(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


class TestTrainingDataExport:
    """Test training data export endpoint."""
    
    def test_export_training_data_json(self, client, test_resolved_complaint, auth_token):
        """Test exporting training data in JSON format.
        
        Requirements: 13.4
        """
        token, user_id = auth_token
        # Submit some feedback first
        client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 5,
                'comments': 'Excellent'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Export training data
        response = client.get(
            '/api/admin/feedback/training-data',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'training_data' in data
        assert 'total_records' in data
        assert data['total_records'] > 0
        
        # Check structure of training data
        training_record = data['training_data'][0]
        assert 'complaint_id' in training_record
        assert 'description' in training_record
        assert 'category' in training_record
        assert 'rating' in training_record
    
    def test_export_training_data_csv(self, client, test_resolved_complaint, auth_token):
        """Test exporting training data in CSV format.
        
        Requirements: 13.4
        """
        token, user_id = auth_token
        # Submit some feedback first
        client.post(
            f'/api/complaints/{test_resolved_complaint}/feedback',
            json={
                'rating': 4,
                'comments': 'Good'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Export training data as CSV
        response = client.get(
            '/api/admin/feedback/training-data?format=csv',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'Content-Disposition' in response.headers
        
        # Check CSV content
        csv_content = response.data.decode('utf-8')
        assert 'complaint_id' in csv_content
        assert 'rating' in csv_content
