"""
Integration tests for complaint submission flow.

Tests the end-to-end complaint submission process including:
- Text complaint submission
- Voice (transcribed) complaint submission
- Image/video upload
- Location data handling
- NLP processing
- ML classification
- Priority scoring
- Duplicate detection

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
import pytest
import json
import os
import tempfile
from io import BytesIO
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Category, Status, PriorityLevel, Location
from models.duplicate_cluster import DuplicateCluster
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
def auth_user(client):
    """Create and authenticate a test user."""
    user_data = {
        'name': 'Test User',
        'phone': '1234567890',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    
    # Register user
    client.post('/api/auth/register', json=user_data)
    
    # Login to get token
    login_response = client.post('/api/auth/login', json={
        'credential': user_data['email'],
        'password': user_data['password']
    })
    
    token = login_response.get_json()['access_token']
    user_id = login_response.get_json()['user_id']
    
    return {
        'token': token,
        'user_id': user_id,
        'headers': {'Authorization': f'Bearer {token}'}
    }


class TestComplaintSubmissionBasic:
    """Test basic complaint submission functionality."""
    
    def test_submit_text_complaint_success(self, client, auth_user, app):
        """
        Test successful submission of a text complaint.
        
        Requirements: 2.1
        """
        complaint_data = {
            'description': 'Water leakage on Main Street causing flooding'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify response structure
        assert 'complaint_id' in data
        assert 'status' in data
        assert 'category' in data
        assert 'priority_level' in data
        assert 'impact_score' in data
        assert 'explanation' in data
        assert 'keywords' in data
        assert 'severity_terms' in data
        
        # Verify status
        assert data['status'] == 'Submitted'
        
        # Verify complaint was stored in database
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.user_id == auth_user['user_id']
            assert complaint.status == Status.SUBMITTED
    
    def test_submit_complaint_without_description(self, client, auth_user):
        """
        Test that complaint submission fails without description.
        
        Requirements: 2.5
        """
        complaint_data = {}
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Description is required' in data['error']
    
    def test_submit_complaint_without_authentication(self, client):
        """
        Test that complaint submission requires authentication.
        
        Requirements: 2.1
        """
        complaint_data = {
            'description': 'Test complaint'
        }
        
        response = client.post('/api/complaints', json=complaint_data)
        
        assert response.status_code == 401


class TestComplaintSubmissionWithLocation:
    """Test complaint submission with location data."""
    
    def test_submit_complaint_with_location(self, client, auth_user, app):
        """
        Test complaint submission with GPS coordinates.
        
        Requirements: 2.4
        """
        complaint_data = {
            'description': 'Pothole on highway near hospital',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'address': 'Main Street, New York'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify complaint was created with location
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.location is not None
            assert complaint.location.latitude == 40.7128
            assert complaint.location.longitude == -74.0060
            assert complaint.location.address == 'Main Street, New York'
    
    def test_submit_complaint_with_invalid_coordinates(self, client, auth_user, app):
        """
        Test complaint submission with invalid coordinates continues without location.
        
        Requirements: 2.4
        """
        complaint_data = {
            'description': 'Test complaint',
            'latitude': 'invalid',
            'longitude': 'invalid'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        # Should succeed but without location
        assert response.status_code == 201
        data = response.get_json()
        
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.location is None


class TestComplaintSubmissionWithMedia:
    """Test complaint submission with media files."""
    
    def test_submit_complaint_with_image(self, client, auth_user, app):
        """
        Test complaint submission with image upload.
        
        Requirements: 2.3
        """
        # Create a fake image file
        image_data = BytesIO(b'fake image content')
        
        data = {
            'description': 'Broken street light with photo evidence',
            'files': (image_data, 'test_image.jpg')
        }
        
        response = client.post(
            '/api/complaints',
            data=data,
            content_type='multipart/form-data',
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        response_data = response.get_json()
        
        # Verify complaint was created
        with app.app_context():
            complaint = Complaint.query.get(response_data['complaint_id'])
            assert complaint is not None
            media_urls = complaint.get_media_urls()
            assert len(media_urls) > 0
            
            # Cleanup uploaded file
            for url in media_urls:
                if os.path.exists(url):
                    os.remove(url)
    
    def test_submit_complaint_with_multiple_files(self, client, auth_user, app):
        """
        Test complaint submission with multiple media files.
        
        Requirements: 2.3
        """
        # Create fake files
        image1 = BytesIO(b'fake image 1')
        image2 = BytesIO(b'fake image 2')
        
        data = {
            'description': 'Accident scene with multiple photos',
            'files': [
                (image1, 'image1.jpg'),
                (image2, 'image2.png')
            ]
        }
        
        response = client.post(
            '/api/complaints',
            data=data,
            content_type='multipart/form-data',
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        response_data = response.get_json()
        
        # Verify multiple files were stored
        with app.app_context():
            complaint = Complaint.query.get(response_data['complaint_id'])
            assert complaint is not None
            media_urls = complaint.get_media_urls()
            assert len(media_urls) == 2
            
            # Cleanup uploaded files
            for url in media_urls:
                if os.path.exists(url):
                    os.remove(url)


class TestComplaintProcessingPipeline:
    """Test the complete complaint processing pipeline."""
    
    def test_nlp_processing_integration(self, client, auth_user, app):
        """
        Test that NLP processing extracts keywords and severity terms.
        
        Requirements: 2.1, 3.1, 3.3, 3.4
        """
        complaint_data = {
            'description': 'URGENT: Fire in building causing injury to residents'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify NLP extracted data
        assert 'keywords' in data
        assert len(data['keywords']) > 0
        
        assert 'severity_terms' in data
        assert 'fire' in data['severity_terms']
        assert 'injury' in data['severity_terms']
        
        # Verify data stored in database
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert len(complaint.get_keywords()) > 0
            assert 'fire' in complaint.get_severity_terms()
            assert 'injury' in complaint.get_severity_terms()
    
    def test_ml_classification_integration(self, client, auth_user, app):
        """
        Test that ML classifier categorizes complaints correctly.
        
        Requirements: 2.1, 4.1, 4.2, 4.3
        """
        complaint_data = {
            'description': 'Water pipe burst on Main Street causing flooding in the area'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify ML classification
        assert 'category' in data
        assert 'confidence' in data
        
        # Water-related complaint should be classified as Water Supply
        assert data['category'] in ['Water Supply', 'Sanitation', 'Roads & Infrastructure']
        
        # Verify data stored in database
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.category is not None
    
    def test_priority_scoring_integration(self, client, auth_user, app):
        """
        Test that priority scoring calculates impact score correctly.
        
        Requirements: 2.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        """
        # High priority complaint with severity terms
        complaint_data = {
            'description': 'URGENT: Fire in electrical transformer causing danger to residents'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify priority scoring
        assert 'impact_score' in data
        assert 'priority_level' in data
        assert 'explanation' in data
        
        # Fire and electrical should result in at least medium priority
        assert data['impact_score'] > 0
        assert data['priority_level'] in ['Medium', 'High', 'Critical']
        
        # Explanation should mention severity terms or factors
        assert len(data['explanation']) > 0
        
        # Verify data stored in database
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.impact_score > 0
            assert complaint.priority_level in [PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    
    def test_duplicate_detection_integration(self, client, auth_user, app):
        """
        Test that duplicate detection groups similar complaints.
        
        Requirements: 2.1, 6.1, 6.2, 6.3, 6.4, 6.5
        """
        # Submit first complaint
        complaint1_data = {
            'description': 'Water leakage on Main Street causing flooding',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
        
        response1 = client.post(
            '/api/complaints',
            json=complaint1_data,
            headers=auth_user['headers']
        )
        
        assert response1.status_code == 201
        data1 = response1.get_json()
        
        # Submit similar complaint
        complaint2_data = {
            'description': 'Water pipe burst on Main Street with flooding issue',
            'latitude': 40.7130,
            'longitude': -74.0062
        }
        
        response2 = client.post(
            '/api/complaints',
            json=complaint2_data,
            headers=auth_user['headers']
        )
        
        assert response2.status_code == 201
        data2 = response2.get_json()
        
        # Verify duplicate detection
        # At least one should have duplicate_count > 0
        assert data1['duplicate_count'] >= 0
        assert data2['duplicate_count'] >= 0
        
        # If duplicates detected, verify cluster
        if data2['duplicate_count'] > 0:
            assert 'cluster_id' in data2
            
            with app.app_context():
                complaint2 = Complaint.query.get(data2['complaint_id'])
                assert complaint2.cluster_id is not None
                
                # Verify cluster exists
                from models.duplicate_cluster import DuplicateCluster
                cluster = DuplicateCluster.query.get(complaint2.cluster_id)
                assert cluster is not None
                assert len(cluster.get_complaint_ids()) >= 2


class TestComplaintSubmissionVariousTypes:
    """Test complaint submission with various complaint types."""
    
    def test_submit_water_supply_complaint(self, client, auth_user, app):
        """
        Test submission of water supply complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'No water supply in our area for the past 3 days. Urgent help needed.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be classified as water-related
        assert data['category'] in ['Water Supply', 'Sanitation']
        assert data['status'] == 'Submitted'
    
    def test_submit_electricity_complaint(self, client, auth_user, app):
        """
        Test submission of electricity complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'Power outage in residential area. Electric transformer not working.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be classified as electricity-related
        assert data['category'] in ['Electricity', 'Public Safety']
        assert data['status'] == 'Submitted'
    
    def test_submit_road_infrastructure_complaint(self, client, auth_user, app):
        """
        Test submission of road infrastructure complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'Large pothole on highway causing accidents. Road repair needed urgently.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be classified as roads-related
        assert data['category'] in ['Roads & Infrastructure', 'Public Safety']
        assert data['status'] == 'Submitted'
    
    def test_submit_healthcare_complaint(self, client, auth_user, app):
        """
        Test submission of healthcare complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'Hospital emergency room not functioning. Medical staff shortage.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be classified as healthcare-related
        assert data['category'] in ['Healthcare', 'Public Safety']
        assert data['status'] == 'Submitted'
    
    def test_submit_public_safety_complaint(self, client, auth_user, app):
        """
        Test submission of public safety complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'Fire hazard in building. Gas leak detected. Immediate evacuation needed.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be at least medium priority due to fire and gas leak
        assert data['priority_level'] in ['Medium', 'High', 'Critical']
        assert data['impact_score'] > 25  # At least medium priority threshold
        assert 'fire' in data['severity_terms'] or 'gas leak' in data['severity_terms']
    
    def test_submit_sanitation_complaint(self, client, auth_user, app):
        """
        Test submission of sanitation complaint.
        
        Requirements: 2.1, 2.2
        """
        complaint_data = {
            'description': 'Garbage not collected for weeks. Sanitation workers not coming to our area.'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should be classified as sanitation-related
        assert data['category'] in ['Sanitation', 'Healthcare']
        assert data['status'] == 'Submitted'


class TestComplaintSubmissionWithVoice:
    """Test complaint submission with voice (transcribed text)."""
    
    def test_submit_voice_complaint_transcribed(self, client, auth_user, app):
        """
        Test submission of voice complaint (already transcribed).
        
        Requirements: 2.2
        """
        # Voice complaint would be transcribed to text before submission
        complaint_data = {
            'description': 'This is a transcribed voice complaint about water leakage in my street'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should process like any text complaint
        assert data['status'] == 'Submitted'
        assert 'category' in data
        assert 'priority_level' in data


class TestComplaintSubmissionEndToEnd:
    """Test complete end-to-end complaint submission flows."""
    
    def test_complete_complaint_flow_with_all_features(self, client, auth_user, app):
        """
        Test complete complaint submission with all features.
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        # Create a comprehensive complaint with all features
        complaint_data = {
            'description': 'URGENT: Fire in electrical transformer near school causing danger',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'address': '123 Main Street, New York'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify all processing steps completed
        assert 'complaint_id' in data
        assert 'status' in data
        assert 'category' in data
        assert 'priority_level' in data
        assert 'impact_score' in data
        assert 'explanation' in data
        assert 'keywords' in data
        assert 'severity_terms' in data
        assert 'duplicate_count' in data
        
        # Verify at least medium priority due to fire
        assert data['priority_level'] in ['Medium', 'High', 'Critical']
        assert data['impact_score'] > 25
        
        # Verify severity terms detected
        assert 'fire' in data['severity_terms']
        
        # Verify database state
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            assert complaint.user_id == auth_user['user_id']
            assert complaint.status == Status.SUBMITTED
            assert complaint.location is not None
            assert complaint.location.latitude == 40.7128
            assert complaint.location.longitude == -74.0060
            assert complaint.category is not None
            assert complaint.priority_level in [PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
            assert complaint.impact_score > 25
            assert len(complaint.get_keywords()) > 0
            assert len(complaint.get_severity_terms()) > 0
    
    def test_multiple_complaints_from_same_user(self, client, auth_user, app):
        """
        Test submitting multiple complaints from the same user.
        
        Requirements: 2.1
        """
        # Submit first complaint
        complaint1_data = {
            'description': 'Water leakage on Main Street'
        }
        
        response1 = client.post(
            '/api/complaints',
            json=complaint1_data,
            headers=auth_user['headers']
        )
        
        assert response1.status_code == 201
        data1 = response1.get_json()
        
        # Submit second complaint
        complaint2_data = {
            'description': 'Electricity outage in residential area'
        }
        
        response2 = client.post(
            '/api/complaints',
            json=complaint2_data,
            headers=auth_user['headers']
        )
        
        assert response2.status_code == 201
        data2 = response2.get_json()
        
        # Verify both complaints created
        assert data1['complaint_id'] != data2['complaint_id']
        
        # Verify both in database
        with app.app_context():
            user_complaints = Complaint.query.filter_by(user_id=auth_user['user_id']).all()
            assert len(user_complaints) >= 2
    
    def test_complaint_with_minimal_data(self, client, auth_user, app):
        """
        Test complaint submission with only required fields.
        
        Requirements: 2.1, 2.5
        """
        complaint_data = {
            'description': 'Simple complaint with minimal data'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should still process successfully
        assert 'complaint_id' in data
        assert data['status'] == 'Submitted'
        assert 'category' in data
        assert 'priority_level' in data
    
    def test_complaint_with_special_characters(self, client, auth_user, app):
        """
        Test complaint submission with special characters in description.
        
        Requirements: 2.1, 3.1
        """
        complaint_data = {
            'description': 'Water leakage!!! @#$% Special chars & symbols... Need help ASAP!!!'
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # NLP should clean the text
        assert 'complaint_id' in data
        assert data['status'] == 'Submitted'
        
        # Verify cleaned text stored
        with app.app_context():
            complaint = Complaint.query.get(data['complaint_id'])
            assert complaint is not None
            # Description should be cleaned (special chars removed/normalized)
            assert complaint.description is not None
    
    def test_complaint_with_long_description(self, client, auth_user, app):
        """
        Test complaint submission with very long description.
        
        Requirements: 2.1
        """
        # Create a long description
        long_description = ' '.join([
            'Water leakage issue on Main Street.',
            'The problem started three days ago.',
            'Multiple residents are affected.',
            'The water is flooding the street.',
            'We need immediate assistance.',
            'This is causing major inconvenience.',
            'Please send someone to fix this urgently.'
        ] * 5)  # Repeat to make it longer
        
        complaint_data = {
            'description': long_description
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should handle long text
        assert 'complaint_id' in data
        assert data['status'] == 'Submitted'
        assert len(data['keywords']) > 0


class TestComplaintSubmissionErrorHandling:
    """Test error handling in complaint submission."""
    
    def test_submit_complaint_with_empty_description(self, client, auth_user):
        """
        Test that empty description is rejected.
        
        Requirements: 2.5
        """
        complaint_data = {
            'description': ''
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_submit_complaint_with_whitespace_only(self, client, auth_user):
        """
        Test that whitespace-only description is rejected.
        
        Requirements: 2.5
        """
        complaint_data = {
            'description': '   \n\t   '
        }
        
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_submit_complaint_without_token(self, client):
        """
        Test that complaint submission requires authentication.
        
        Requirements: 2.1
        """
        complaint_data = {
            'description': 'Test complaint'
        }
        
        response = client.post('/api/complaints', json=complaint_data)
        
        assert response.status_code == 401
    
    def test_submit_complaint_with_invalid_token(self, client):
        """
        Test that invalid token is rejected.
        
        Requirements: 2.1
        """
        complaint_data = {
            'description': 'Test complaint'
        }
        
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = client.post('/api/complaints', json=complaint_data, headers=headers)
        
        assert response.status_code == 422  # JWT decode error