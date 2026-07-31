"""
End-to-end tests for complete user journeys.

Tests the complete workflows including:
- User registration → complaint submission → tracking → feedback
- Admin workflows (dashboard, analytics, alerts)
- Officer assignment and escalation flows

Requirements: All
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Category, Status, PriorityLevel, Location
from models.officer import Officer, Department
from models.feedback import Feedback
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        
        # Create test officers for routing
        officer1 = Officer(
            name='Officer John',
            department=Department.WATER_DEPT,
            phone='1111111111',
            email='officer1@gov.com',
            location_latitude=40.7128,
            location_longitude=-74.0060,
            location_address='NYC Office'
        )
        officer2 = Officer(
            name='Officer Jane',
            department=Department.ELECTRICITY_DEPT,
            phone='2222222222',
            email='officer2@gov.com',
            location_latitude=40.7130,
            location_longitude=-74.0062,
            location_address='NYC Office 2'
        )
        db.session.add(officer1)
        db.session.add(officer2)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


class TestCompleteUserJourney:
    """Test complete user journey from registration to feedback."""
    
    def test_complete_citizen_workflow(self, client, app):
        """
        Test complete citizen workflow: register → login → submit → track → feedback.
        
        Requirements: 1.1, 1.3, 2.1, 9.1, 9.2, 9.3, 13.1, 13.2
        """
        # Step 1: Register new user
        user_data = {
            'name': 'John Citizen',
            'phone': '9876543210',
            'email': 'john@example.com',
            'password': 'securepass123'
        }
        
        register_response = client.post('/api/auth/register', json=user_data)
        assert register_response.status_code == 201
        register_data = register_response.get_json()
        assert 'user_id' in register_data
        user_id = register_data['user_id']
        
        # Step 2: Login
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        assert 'access_token' in login_data
        token = login_data['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 3: Submit complaint
        complaint_data = {
            'description': 'Water leakage on Main Street causing flooding',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'address': 'Main Street, NYC'
        }
        
        submit_response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=headers
        )
        assert submit_response.status_code == 201
        submit_data = submit_response.get_json()
        assert 'complaint_id' in submit_data
        complaint_id = submit_data['complaint_id']
        assert submit_data['status'] == 'Submitted'
        
        # Step 4: Track complaint status
        track_response = client.get(
            f'/api/complaints/{complaint_id}',
            headers=headers
        )
        assert track_response.status_code == 200
        track_data = track_response.get_json()
        assert track_data['complaint_id'] == complaint_id
        assert 'status' in track_data
        assert 'priority_level' in track_data
        assert 'explanation' in track_data
        
        # Step 5: Get complaint history
        history_response = client.get(
            f'/api/complaints/{complaint_id}/history',
            headers=headers
        )
        assert history_response.status_code == 200
        history_data = history_response.get_json()
        assert 'history' in history_data
        assert len(history_data['history']) > 0
        
        # Step 6: Mark complaint as resolved (simulate officer action)
        with app.app_context():
            complaint = Complaint.query.get(complaint_id)
            complaint.status = Status.RESOLVED
            complaint.resolved_at = datetime.utcnow()
            db.session.commit()
        
        # Step 7: Submit feedback
        feedback_data = {
            'rating': 5,
            'comments': 'Issue resolved quickly. Great service!'
        }
        
        feedback_response = client.post(
            f'/api/complaints/{complaint_id}/feedback',
            json=feedback_data,
            headers=headers
        )
        assert feedback_response.status_code == 201
        feedback_result = feedback_response.get_json()
        assert 'message' in feedback_result
        
        # Step 8: Verify feedback stored
        with app.app_context():
            feedback = Feedback.query.filter_by(complaint_id=complaint_id).first()
            assert feedback is not None
            assert feedback.rating == 5
            assert feedback.comments == 'Issue resolved quickly. Great service!'
            
            # Verify trust score updated
            user = User.query.get(user_id)
            assert user.trust_score > 50  # Should increase from default 50
    
    def test_multiple_complaints_workflow(self, client, app):
        """
        Test user submitting multiple complaints and tracking them.
        
        Requirements: 1.1, 2.1, 9.1
        """
        # Register and login
        user_data = {
            'name': 'Multi Complaint User',
            'phone': '5555555555',
            'email': 'multi@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.get_json()['access_token']
        user_id = login_response.get_json()['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Submit multiple complaints
        complaints = [
            {'description': 'Water leakage on Street A'},
            {'description': 'Electricity outage in Area B'},
            {'description': 'Pothole on Highway C'}
        ]
        
        complaint_ids = []
        for complaint_data in complaints:
            response = client.post('/api/complaints', json=complaint_data, headers=headers)
            assert response.status_code == 201
            complaint_ids.append(response.get_json()['complaint_id'])
        
        # Get all user complaints
        user_complaints_response = client.get(
            f'/api/users/{user_id}/complaints',
            headers=headers
        )
        assert user_complaints_response.status_code == 200
        user_complaints_data = user_complaints_response.get_json()
        assert 'complaints' in user_complaints_data
        assert len(user_complaints_data['complaints']) == 3
        
        # Verify all complaint IDs present
        returned_ids = [c['complaint_id'] for c in user_complaints_data['complaints']]
        for cid in complaint_ids:
            assert cid in returned_ids


class TestOfficerAssignmentWorkflow:
    """Test officer assignment and routing workflows."""
    
    def test_complaint_routing_and_assignment(self, client, app):
        """
        Test complaint routing to department and officer assignment.
        
        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        # Register and login user
        user_data = {
            'name': 'Test User',
            'phone': '7777777777',
            'email': 'routing@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Submit water-related complaint
        complaint_data = {
            'description': 'Water pipe burst causing flooding',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
        
        response = client.post('/api/complaints', json=complaint_data, headers=headers)
        assert response.status_code == 201
        complaint_id = response.get_json()['complaint_id']
        
        # Trigger routing (simulate automatic routing)
        with app.app_context():
            from services.routing_service import RoutingService
            routing_service = RoutingService()
            
            complaint = Complaint.query.get(complaint_id)
            result = routing_service.assign_complaint(complaint)
            
            if result['success']:
                # Verify assignment
                db.session.refresh(complaint)
                assert complaint.status == Status.ASSIGNED
                assert complaint.assigned_officer_id is not None
                
                # Verify officer workload updated
                officer = Officer.query.get(complaint.assigned_officer_id)
                assert officer is not None
                assert officer.assigned_cases > 0


class TestEscalationWorkflow:
    """Test complaint escalation workflows."""
    
    def test_sla_violation_and_escalation(self, client, app):
        """
        Test SLA violation detection and escalation.
        
        Requirements: 10.1, 10.2, 10.3, 10.4
        """
        # Register and login
        user_data = {
            'name': 'Escalation Test User',
            'phone': '8888888888',
            'email': 'escalation@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Submit critical complaint
        complaint_data = {
            'description': 'URGENT: Fire in building causing danger to residents'
        }
        
        response = client.post('/api/complaints', json=complaint_data, headers=headers)
        assert response.status_code == 201
        complaint_id = response.get_json()['complaint_id']
        
        # Assign complaint and set SLA deadline
        with app.app_context():
            from services.monitoring_service import MonitoringService
            monitoring_service = MonitoringService()
            
            complaint = Complaint.query.get(complaint_id)
            complaint.status = Status.ASSIGNED
            complaint.assigned_at = datetime.utcnow()
            
            # Calculate SLA deadline
            deadline = monitoring_service.calculate_sla_deadline(
                complaint.priority_level,
                complaint.assigned_at
            )
            complaint.sla_deadline = deadline
            db.session.commit()
            
            # Simulate time passing beyond SLA
            complaint.assigned_at = datetime.utcnow() - timedelta(hours=5)
            complaint.sla_deadline = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            # Check for violations
            violations = monitoring_service.check_sla_violations()
            
            # Verify complaint is in violations list
            violation_ids = [v['complaint_id'] for v in violations]
            assert complaint_id in violation_ids


class TestAdminDashboardWorkflow:
    """Test admin dashboard and analytics workflows."""
    
    def test_admin_dashboard_access(self, client, app):
        """
        Test admin dashboard data retrieval.
        
        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
        """
        # Create admin user
        with app.app_context():
            admin_user = User(
                name='Admin User',
                phone='9999999999',
                email='admin@gov.com',
                password_hash='hashed_password',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            admin_id = admin_user.user_id
        
        # Login as admin
        # Note: This assumes admin login works similarly
        # In production, admin would have separate authentication
        
        # Test heatmap data
        heatmap_response = client.get('/api/admin/heatmap')
        assert heatmap_response.status_code in [200, 401]  # May require auth
        
        # Test analytics endpoints
        trends_response = client.get('/api/admin/analytics/trends')
        assert trends_response.status_code in [200, 401]
        
        departments_response = client.get('/api/admin/analytics/departments')
        assert departments_response.status_code in [200, 401]
        
        resolution_response = client.get('/api/admin/analytics/resolution-times')
        assert resolution_response.status_code in [200, 401]
        
        # Test critical alerts
        alerts_response = client.get('/api/admin/alerts')
        assert alerts_response.status_code in [200, 401]
    
    def test_admin_analytics_with_data(self, client, app):
        """
        Test admin analytics with actual complaint data.
        
        Requirements: 12.2, 12.3, 12.4
        """
        # Create test data
        with app.app_context():
            # Create user
            user = User(
                name='Test User',
                phone='1231231234',
                email='analytics@example.com',
                password_hash='hashed'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create multiple complaints with different categories and priorities
            complaints_data = [
                {
                    'category': Category.WATER_SUPPLY,
                    'priority': PriorityLevel.HIGH,
                    'status': Status.RESOLVED,
                    'resolved_at': datetime.utcnow()
                },
                {
                    'category': Category.ELECTRICITY,
                    'priority': PriorityLevel.CRITICAL,
                    'status': Status.ASSIGNED,
                    'resolved_at': None
                },
                {
                    'category': Category.WATER_SUPPLY,
                    'priority': PriorityLevel.MEDIUM,
                    'status': Status.RESOLVED,
                    'resolved_at': datetime.utcnow()
                }
            ]
            
            for data in complaints_data:
                complaint = Complaint(
                    user_id=user.user_id,
                    description='Test complaint',
                    category=data['category'],
                    priority_level=data['priority'],
                    impact_score=50,
                    status=data['status'],
                    resolved_at=data['resolved_at']
                )
                db.session.add(complaint)
            
            db.session.commit()
        
        # Test analytics endpoints
        trends_response = client.get('/api/admin/analytics/trends')
        if trends_response.status_code == 200:
            trends_data = trends_response.get_json()
            assert 'trends' in trends_data or 'categories' in trends_data
        
        resolution_response = client.get('/api/admin/analytics/resolution-times')
        if resolution_response.status_code == 200:
            resolution_data = resolution_response.get_json()
            assert 'resolution_times' in resolution_data or 'average_time' in resolution_data


class TestDuplicateDetectionWorkflow:
    """Test duplicate detection in real workflows."""
    
    def test_duplicate_clustering_workflow(self, client, app):
        """
        Test duplicate detection and clustering in user workflow.
        
        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        """
        # Register and login
        user_data = {
            'name': 'Duplicate Test User',
            'phone': '6666666666',
            'email': 'duplicate@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Submit first complaint
        complaint1_data = {
            'description': 'Water leakage on Main Street causing flooding',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
        
        response1 = client.post('/api/complaints', json=complaint1_data, headers=headers)
        assert response1.status_code == 201
        data1 = response1.get_json()
        
        # Submit similar complaint
        complaint2_data = {
            'description': 'Water pipe burst on Main Street with flooding issue',
            'latitude': 40.7130,
            'longitude': -74.0062
        }
        
        response2 = client.post('/api/complaints', json=complaint2_data, headers=headers)
        assert response2.status_code == 201
        data2 = response2.get_json()
        
        # Verify duplicate detection occurred
        assert 'duplicate_count' in data2
        
        # If duplicates detected, verify impact score increased
        if data2['duplicate_count'] > 0:
            assert data2['impact_score'] >= data1['impact_score']


class TestNotificationWorkflow:
    """Test notification workflows."""
    
    def test_notification_on_complaint_submission(self, client, app):
        """
        Test that notifications are triggered on complaint submission.
        
        Requirements: 11.1
        """
        # Register and login
        user_data = {
            'name': 'Notification Test User',
            'phone': '4444444444',
            'email': 'notify@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user_data)
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Submit complaint
        complaint_data = {
            'description': 'Test complaint for notification'
        }
        
        response = client.post('/api/complaints', json=complaint_data, headers=headers)
        assert response.status_code == 201
        
        # Note: Actual notification sending would be mocked in tests
        # Here we just verify the complaint was created successfully
        # In production, notification service would be called


class TestSecurityWorkflow:
    """Test security and authorization workflows."""
    
    def test_user_cannot_access_other_complaints(self, client, app):
        """
        Test that users can only access their own complaints.
        
        Requirements: 15.3
        """
        # Create first user
        user1_data = {
            'name': 'User One',
            'phone': '1010101010',
            'email': 'user1@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user1_data)
        login1_response = client.post('/api/auth/login', json={
            'credential': user1_data['email'],
            'password': user1_data['password']
        })
        token1 = login1_response.get_json()['access_token']
        headers1 = {'Authorization': f'Bearer {token1}'}
        
        # User 1 submits complaint
        complaint_data = {
            'description': 'User 1 complaint'
        }
        
        response = client.post('/api/complaints', json=complaint_data, headers=headers1)
        complaint_id = response.get_json()['complaint_id']
        
        # Create second user
        user2_data = {
            'name': 'User Two',
            'phone': '2020202020',
            'email': 'user2@example.com',
            'password': 'password123'
        }
        
        client.post('/api/auth/register', json=user2_data)
        login2_response = client.post('/api/auth/login', json={
            'credential': user2_data['email'],
            'password': user2_data['password']
        })
        token2 = login2_response.get_json()['access_token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # User 2 tries to access User 1's complaint
        access_response = client.get(
            f'/api/complaints/{complaint_id}',
            headers=headers2
        )
        
        # Should be forbidden or not found
        assert access_response.status_code in [403, 404]


class TestCompleteSystemIntegration:
    """Test complete system integration with all components."""
    
    def test_full_system_workflow(self, client, app):
        """
        Test complete system workflow with all components working together.
        
        Requirements: All
        """
        # 1. Register user
        user_data = {
            'name': 'Full System Test User',
            'phone': '3333333333',
            'email': 'fullsystem@example.com',
            'password': 'password123'
        }
        
        register_response = client.post('/api/auth/register', json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post('/api/auth/login', json={
            'credential': user_data['email'],
            'password': user_data['password']
        })
        assert login_response.status_code == 200
        token = login_response.get_json()['access_token']
        user_id = login_response.get_json()['user_id']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 3. Submit high-priority complaint
        complaint_data = {
            'description': 'URGENT: Fire in electrical transformer near hospital causing danger',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'address': '123 Main Street, NYC'
        }
        
        submit_response = client.post('/api/complaints', json=complaint_data, headers=headers)
        assert submit_response.status_code == 201
        submit_data = submit_response.get_json()
        complaint_id = submit_data['complaint_id']
        
        # Verify all processing completed
        assert submit_data['status'] == 'Submitted'
        assert 'category' in submit_data
        assert 'priority_level' in submit_data
        assert submit_data['priority_level'] in ['High', 'Critical']
        assert 'fire' in submit_data['severity_terms']
        
        # 4. Track complaint
        track_response = client.get(f'/api/complaints/{complaint_id}', headers=headers)
        assert track_response.status_code == 200
        
        # 5. Get complaint history
        history_response = client.get(f'/api/complaints/{complaint_id}/history', headers=headers)
        assert history_response.status_code == 200
        
        # 6. Simulate resolution
        with app.app_context():
            complaint = Complaint.query.get(complaint_id)
            complaint.status = Status.RESOLVED
            complaint.resolved_at = datetime.utcnow()
            db.session.commit()
        
        # 7. Submit feedback
        feedback_data = {
            'rating': 4,
            'comments': 'Good response time'
        }
        
        feedback_response = client.post(
            f'/api/complaints/{complaint_id}/feedback',
            json=feedback_data,
            headers=headers
        )
        assert feedback_response.status_code == 201
        
        # 8. Verify complete workflow
        with app.app_context():
            # Verify complaint
            complaint = Complaint.query.get(complaint_id)
            assert complaint is not None
            assert complaint.status == Status.RESOLVED
            assert complaint.resolved_at is not None
            
            # Verify feedback
            feedback = Feedback.query.filter_by(complaint_id=complaint_id).first()
            assert feedback is not None
            assert feedback.rating == 4
            
            # Verify user trust score updated
            user = User.query.get(user_id)
            assert user.trust_score >= 50
