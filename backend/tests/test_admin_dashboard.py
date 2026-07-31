"""
Unit tests for admin dashboard endpoints.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""
import pytest
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Category, PriorityLevel, Status, Location
from models.officer import Officer, Department
from config import TestingConfig
from datetime import datetime, timedelta


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
def auth_token(client):
    """Create a user and return authentication token."""
    # Register user
    user_data = {
        'name': 'Admin User',
        'phone': '1234567890',
        'email': 'admin@example.com',
        'password': 'adminpass123'
    }
    client.post('/api/auth/register', json=user_data)
    
    # Login
    login_response = client.post('/api/auth/login', json={
        'credential': user_data['email'],
        'password': user_data['password']
    })
    
    return login_response.get_json()['access_token']


@pytest.fixture
def sample_complaints(app):
    """Create sample complaints for testing."""
    with app.app_context():
        # Create user
        user = User(
            name='Test User',
            phone='9876543210',
            email='test@example.com',
            password_hash='hashed'
        )
        db.session.add(user)
        db.session.flush()
        
        # Create locations
        location1 = Location(
            latitude=40.7128,
            longitude=-74.0060,
            address='New York, NY'
        )
        location2 = Location(
            latitude=34.0522,
            longitude=-118.2437,
            address='Los Angeles, CA'
        )
        db.session.add(location1)
        db.session.add(location2)
        db.session.flush()
        
        # Create complaints with different categories and priorities
        complaints = [
            Complaint(
                user_id=user.user_id,
                category=Category.WATER_SUPPLY,
                description='Water leak',
                priority_level=PriorityLevel.CRITICAL,
                impact_score=85,
                status=Status.SUBMITTED,
                location_id=location1.location_id,
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Complaint(
                user_id=user.user_id,
                category=Category.ELECTRICITY,
                description='Power outage',
                priority_level=PriorityLevel.HIGH,
                impact_score=70,
                status=Status.ASSIGNED,
                location_id=location2.location_id,
                created_at=datetime.utcnow() - timedelta(days=2),
                assigned_at=datetime.utcnow() - timedelta(days=1),
                sla_deadline=datetime.utcnow() + timedelta(hours=2)
            ),
            Complaint(
                user_id=user.user_id,
                category=Category.ROADS_INFRASTRUCTURE,
                description='Pothole',
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.RESOLVED,
                location_id=location1.location_id,
                created_at=datetime.utcnow() - timedelta(days=5),
                resolved_at=datetime.utcnow() - timedelta(days=1)
            ),
            Complaint(
                user_id=user.user_id,
                category=Category.PUBLIC_SAFETY,
                description='Street light broken',
                priority_level=PriorityLevel.LOW,
                impact_score=20,
                status=Status.ESCALATED,
                location_id=location2.location_id,
                created_at=datetime.utcnow() - timedelta(days=10)
            )
        ]
        
        for complaint in complaints:
            db.session.add(complaint)
        
        # Create officers
        officer = Officer(
            name='Officer Smith',
            department=Department.WATER_DEPT,
            phone='5551234567',
            email='officer@example.com',
            location_latitude=40.7128,
            location_longitude=-74.0060,
            assigned_cases=2
        )
        db.session.add(officer)
        
        db.session.commit()


class TestHeatmapEndpoint:
    """Test complaint heatmap endpoint."""
    
    def test_get_heatmap_data(self, client, auth_token, sample_complaints):
        """Test retrieving heatmap data.
        
        Requirements: 12.1
        """
        response = client.get('/api/admin/heatmap', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'heatmap_data' in data
        assert 'total_locations' in data
        assert data['total_locations'] > 0
        
        # Check heatmap data structure
        if data['heatmap_data']:
            first_location = data['heatmap_data'][0]
            assert 'location' in first_location
            assert 'complaint_count' in first_location
            assert 'avg_impact_score' in first_location
            assert 'priority_distribution' in first_location
    
    def test_heatmap_with_filters(self, client, auth_token, sample_complaints):
        """Test heatmap with status filter.
        
        Requirements: 12.1
        """
        response = client.get('/api/admin/heatmap?status=Submitted&days=7', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'filters_applied' in data
        assert data['filters_applied']['status'] == 'Submitted'
    
    def test_heatmap_unauthorized(self, client, sample_complaints):
        """Test heatmap without authentication.
        
        Requirements: 12.1
        """
        response = client.get('/api/admin/heatmap')
        assert response.status_code == 401


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_get_category_trends(self, client, auth_token, sample_complaints):
        """Test category trends endpoint.
        
        Requirements: 12.2
        """
        response = client.get('/api/admin/analytics/trends?days=30', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'trends' in data
        assert 'totals' in data
        assert 'period' in data
        
        # Check that all categories are present
        for category in Category:
            assert category.value in data['trends']
    
    def test_get_department_performance(self, client, auth_token, sample_complaints):
        """Test department performance endpoint.
        
        Requirements: 12.3
        """
        response = client.get('/api/admin/analytics/departments?days=30', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'departments' in data
        assert len(data['departments']) > 0
        
        # Check department metrics structure
        first_dept = data['departments'][0]
        assert 'department' in first_dept
        assert 'total_complaints' in first_dept
        assert 'pending_complaints' in first_dept
        assert 'resolved_complaints' in first_dept
        assert 'avg_resolution_time_hours' in first_dept
        assert 'sla_compliance_rate' in first_dept
    
    def test_get_resolution_times(self, client, auth_token, sample_complaints):
        """Test resolution times analytics endpoint.
        
        Requirements: 12.4
        """
        response = client.get('/api/admin/analytics/resolution-times?days=30', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'overall' in data
        assert 'by_category' in data
        assert 'by_priority' in data
        
        # Check overall stats
        assert 'total_resolved' in data['overall']
        assert 'avg_hours' in data['overall']


class TestCriticalAlertsEndpoint:
    """Test critical alerts endpoint."""
    
    def test_get_critical_alerts(self, client, auth_token, sample_complaints):
        """Test retrieving critical alerts.
        
        Requirements: 12.5
        """
        response = client.get('/api/admin/alerts', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'alerts' in data
        assert 'total_alerts' in data
        assert 'summary' in data
        
        # Check summary structure
        assert 'critical_priority' in data['summary']
        assert 'escalated' in data['summary']
        assert 'approaching_sla' in data['summary']
    
    def test_alerts_with_limit(self, client, auth_token, sample_complaints):
        """Test alerts with limit parameter.
        
        Requirements: 12.5
        """
        response = client.get('/api/admin/alerts?limit=2', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'alerts' in data
    
    def test_alerts_include_high_priority(self, client, auth_token, sample_complaints):
        """Test alerts including high priority complaints.
        
        Requirements: 12.5
        """
        response = client.get('/api/admin/alerts?include_high=true', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'alerts' in data
        
        # Should include both critical and high priority
        if data['alerts']:
            priorities = [alert['complaint']['priority_level'] for alert in data['alerts'] 
                         if alert['alert_type'] == 'CRITICAL_PRIORITY']
            # May contain both Critical and High
            assert any(p in ['Critical', 'High'] for p in priorities) or len(priorities) == 0
