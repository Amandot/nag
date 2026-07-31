"""
Tests for the Monitoring and Escalation Service.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""
import pytest
from datetime import datetime, timedelta
from app import create_app
from config import TestingConfig
from models import db
from models.complaint import Complaint, Status, PriorityLevel, Category, Location
from models.user import User
from models.officer import Officer, Department
from services.monitoring_service import get_monitoring_service


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
def monitoring_service(app):
    """Get monitoring service instance."""
    with app.app_context():
        return get_monitoring_service()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            name="Test User",
            phone="+1234567890",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_officer(app):
    """Create a test officer."""
    with app.app_context():
        officer = Officer(
            name="Test Officer",
            department=Department.WATER_DEPT,
            phone="+1234567891",
            email="officer@example.com",
            location_latitude=40.7128,
            location_longitude=-74.0060,
            assigned_cases=0
        )
        db.session.add(officer)
        db.session.commit()
        yield officer
        db.session.delete(officer)
        db.session.commit()


def test_calculate_sla_deadline_critical(monitoring_service):
    """
    Test SLA deadline calculation for CRITICAL priority.
    
    Requirements: 10.1
    """
    assigned_time = datetime(2024, 1, 1, 12, 0, 0)
    deadline = monitoring_service.calculate_sla_deadline('CRITICAL', assigned_time)
    
    # CRITICAL should have 4 hour SLA
    expected_deadline = assigned_time + timedelta(hours=4)
    assert deadline == expected_deadline


def test_calculate_sla_deadline_high(monitoring_service):
    """
    Test SLA deadline calculation for HIGH priority.
    
    Requirements: 10.1
    """
    assigned_time = datetime(2024, 1, 1, 12, 0, 0)
    deadline = monitoring_service.calculate_sla_deadline('HIGH', assigned_time)
    
    # HIGH should have 24 hour SLA
    expected_deadline = assigned_time + timedelta(hours=24)
    assert deadline == expected_deadline


def test_calculate_sla_deadline_medium(monitoring_service):
    """
    Test SLA deadline calculation for MEDIUM priority.
    
    Requirements: 10.1
    """
    assigned_time = datetime(2024, 1, 1, 12, 0, 0)
    deadline = monitoring_service.calculate_sla_deadline('MEDIUM', assigned_time)
    
    # MEDIUM should have 72 hour SLA
    expected_deadline = assigned_time + timedelta(hours=72)
    assert deadline == expected_deadline


def test_calculate_sla_deadline_low(monitoring_service):
    """
    Test SLA deadline calculation for LOW priority.
    
    Requirements: 10.1
    """
    assigned_time = datetime(2024, 1, 1, 12, 0, 0)
    deadline = monitoring_service.calculate_sla_deadline('LOW', assigned_time)
    
    # LOW should have 168 hour (7 days) SLA
    expected_deadline = assigned_time + timedelta(hours=168)
    assert deadline == expected_deadline


def test_get_resolution_time_resolved(app, test_user, test_officer):
    """
    Test resolution time calculation for resolved complaint.
    
    Requirements: 10.5
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create a complaint
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.RESOLVED,
            priority_level=PriorityLevel.HIGH,
            assigned_at=datetime.utcnow() - timedelta(hours=5),
            resolved_at=datetime.utcnow()
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Get resolution time
        resolution_time = monitoring_service.get_resolution_time(complaint)
        
        # Should be approximately 5 hours
        assert resolution_time is not None
        assert 4.9 <= resolution_time.total_seconds() / 3600 <= 5.1
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()


def test_get_resolution_time_not_resolved(app, test_user):
    """
    Test resolution time calculation for unresolved complaint.
    
    Requirements: 10.5
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create an unresolved complaint
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.ASSIGNED,
            priority_level=PriorityLevel.HIGH,
            assigned_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Get resolution time
        resolution_time = monitoring_service.get_resolution_time(complaint)
        
        # Should be None for unresolved complaints
        assert resolution_time is None
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()


def test_check_sla_violations_no_violations(app, test_user, test_officer):
    """
    Test SLA violation checker with no violations.
    
    Requirements: 10.2
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create a complaint well within SLA
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.ASSIGNED,
            priority_level=PriorityLevel.HIGH,
            assigned_officer_id=test_officer.officer_id,
            assigned_at=datetime.utcnow() - timedelta(hours=1),
            sla_deadline=datetime.utcnow() + timedelta(hours=23)
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Check violations
        results = monitoring_service.check_sla_violations()
        
        # Should have no warnings or violations
        assert len(results['warnings']) == 0
        assert len(results['violations']) == 0
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()


def test_check_sla_violations_warning(app, test_user, test_officer):
    """
    Test SLA violation checker with warning (75% threshold).
    
    Requirements: 10.2, 10.3
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create a complaint at 80% of SLA (should trigger warning)
        assigned_at = datetime.utcnow() - timedelta(hours=19.2)  # 80% of 24 hours
        sla_deadline = assigned_at + timedelta(hours=24)
        
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.ASSIGNED,
            priority_level=PriorityLevel.HIGH,
            assigned_officer_id=test_officer.officer_id,
            assigned_at=assigned_at,
            sla_deadline=sla_deadline
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Check violations
        results = monitoring_service.check_sla_violations()
        
        # Should have one warning
        assert len(results['warnings']) == 1
        assert results['warnings'][0].complaint_id == complaint.complaint_id
        assert len(results['violations']) == 0
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()


def test_check_sla_violations_exceeded(app, test_user, test_officer):
    """
    Test SLA violation checker with exceeded deadline.
    
    Requirements: 10.2, 10.4
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create a complaint that exceeded SLA
        assigned_at = datetime.utcnow() - timedelta(hours=25)
        sla_deadline = assigned_at + timedelta(hours=24)
        
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.ASSIGNED,
            priority_level=PriorityLevel.HIGH,
            assigned_officer_id=test_officer.officer_id,
            assigned_at=assigned_at,
            sla_deadline=sla_deadline
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Check violations
        results = monitoring_service.check_sla_violations()
        
        # Should have one violation
        assert len(results['violations']) == 1
        assert results['violations'][0].complaint_id == complaint.complaint_id
        assert len(results['warnings']) == 0
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()


def test_escalate_complaint(app, test_user, test_officer):
    """
    Test complaint escalation.
    
    Requirements: 10.3, 10.4
    """
    with app.app_context():
        monitoring_service = get_monitoring_service()
        
        # Create a complaint that exceeded SLA
        assigned_at = datetime.utcnow() - timedelta(hours=25)
        sla_deadline = assigned_at + timedelta(hours=24)
        
        complaint = Complaint(
            user_id=test_user.user_id,
            category=Category.WATER_SUPPLY,
            description="Test complaint",
            status=Status.ASSIGNED,
            priority_level=PriorityLevel.HIGH,
            assigned_officer_id=test_officer.officer_id,
            assigned_at=assigned_at,
            sla_deadline=sla_deadline
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Escalate complaint
        success = monitoring_service.escalate_complaint(complaint)
        
        # Should succeed
        assert success is True
        
        # Verify status changed to ESCALATED
        db.session.refresh(complaint)
        assert complaint.status == Status.ESCALATED
        
        # Cleanup
        db.session.delete(complaint)
        db.session.commit()
