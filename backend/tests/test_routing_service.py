"""
Unit tests for Routing Service.

Tests the functionality of department mapping, officer assignment,
and complaint routing.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import pytest
from services.routing_service import RoutingService, get_routing_service
from models import db
from models.complaint import Complaint, Category, Status, PriorityLevel, Location
from models.officer import Officer, Department
from datetime import datetime
import uuid


class TestRoutingService:
    """Test suite for Routing Service."""
    
    @pytest.fixture
    def service(self):
        """Create a routing service instance."""
        return RoutingService()
    
    def test_map_category_to_department_water(self, service):
        """Test mapping water supply category to water department."""
        department = service.map_category_to_department(Category.WATER_SUPPLY)
        assert department == Department.WATER_DEPT
    
    def test_map_category_to_department_electricity(self, service):
        """Test mapping electricity category to electricity department."""
        department = service.map_category_to_department(Category.ELECTRICITY)
        assert department == Department.ELECTRICITY_DEPT
    
    def test_map_category_to_department_roads(self, service):
        """Test mapping roads category to roads department."""
        department = service.map_category_to_department(Category.ROADS_INFRASTRUCTURE)
        assert department == Department.ROADS_DEPT
    
    def test_map_category_to_department_healthcare(self, service):
        """Test mapping healthcare category to health department."""
        department = service.map_category_to_department(Category.HEALTHCARE)
        assert department == Department.HEALTH_DEPT
    
    def test_map_category_to_department_public_safety(self, service):
        """Test mapping public safety category to safety department."""
        department = service.map_category_to_department(Category.PUBLIC_SAFETY)
        assert department == Department.SAFETY_DEPT
    
    def test_map_category_to_department_sanitation(self, service):
        """Test mapping sanitation category to sanitation department."""
        department = service.map_category_to_department(Category.SANITATION)
        assert department == Department.SANITATION_DEPT
    
    def test_calculate_distance_same_location(self, service):
        """Test distance calculation for same location."""
        lat, lon = 40.7128, -74.0060
        distance = service.calculate_distance(lat, lon, lat, lon)
        assert distance == 0.0
    
    def test_calculate_distance_different_locations(self, service):
        """Test distance calculation between New York and Los Angeles."""
        # New York City coordinates
        lat1, lon1 = 40.7128, -74.0060
        # Los Angeles coordinates
        lat2, lon2 = 34.0522, -118.2437
        
        distance = service.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Distance should be approximately 3944 km
        assert 3900 < distance < 4000
    
    def test_calculate_distance_nearby(self, service):
        """Test distance calculation for nearby locations."""
        # Two locations approximately 5km apart
        lat1, lon1 = 40.7128, -74.0060
        lat2, lon2 = 40.7578, -73.9855
        
        distance = service.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Distance should be around 5-6 km
        assert 4 < distance < 7

    
    def test_find_nearest_officer_single_officer(self, service, app):
        """Test finding nearest officer when only one officer exists."""
        with app.app_context():
            # Create an officer
            officer = Officer(
                name="John Doe",
                department=Department.WATER_DEPT,
                phone="1234567890",
                email="john@example.com",
                location_latitude=40.7128,
                location_longitude=-74.0060,
                assigned_cases=0
            )
            db.session.add(officer)
            db.session.commit()
            
            # Find nearest officer (same location)
            found_officer = service.find_nearest_officer(
                40.7128, -74.0060, Department.WATER_DEPT
            )
            
            assert found_officer is not None
            assert found_officer.officer_id == officer.officer_id
            
            # Cleanup
            db.session.delete(officer)
            db.session.commit()
    
    def test_find_nearest_officer_workload_balancing(self, service, app):
        """Test that officer with lower workload is selected."""
        with app.app_context():
            # Create two officers at same location with different workloads
            officer1 = Officer(
                name="Officer 1",
                department=Department.WATER_DEPT,
                phone="1111111111",
                email="officer1@example.com",
                location_latitude=40.7128,
                location_longitude=-74.0060,
                assigned_cases=5
            )
            
            officer2 = Officer(
                name="Officer 2",
                department=Department.WATER_DEPT,
                phone="2222222222",
                email="officer2@example.com",
                location_latitude=40.7128,
                location_longitude=-74.0060,
                assigned_cases=2  # Lower workload
            )
            
            db.session.add_all([officer1, officer2])
            db.session.commit()
            
            # Find nearest officer
            found_officer = service.find_nearest_officer(
                40.7128, -74.0060, Department.WATER_DEPT
            )
            
            # Should select officer2 (lower workload)
            assert found_officer is not None
            assert found_officer.officer_id == officer2.officer_id
            
            # Cleanup
            db.session.delete(officer1)
            db.session.delete(officer2)
            db.session.commit()
    
    def test_find_nearest_officer_no_officers(self, service, app):
        """Test finding officer when no officers exist in department."""
        with app.app_context():
            # Try to find officer in empty department
            found_officer = service.find_nearest_officer(
                40.7128, -74.0060, Department.WATER_DEPT
            )
            
            assert found_officer is None
    
    def test_find_nearest_officer_too_far(self, service, app):
        """Test that officers beyond max distance are not selected."""
        with app.app_context():
            # Create officer far away (Los Angeles)
            officer = Officer(
                name="Far Officer",
                department=Department.WATER_DEPT,
                phone="1234567890",
                email="far@example.com",
                location_latitude=34.0522,  # Los Angeles
                location_longitude=-118.2437,
                assigned_cases=0
            )
            db.session.add(officer)
            db.session.commit()
            
            # Try to find officer from New York
            found_officer = service.find_nearest_officer(
                40.7128, -74.0060, Department.WATER_DEPT
            )
            
            # Should not find officer (too far)
            assert found_officer is None
            
            # Cleanup
            db.session.delete(officer)
            db.session.commit()
    
    def test_assign_complaint_success(self, service, app):
        """Test successful complaint assignment."""
        with app.app_context():
            # Create officer
            officer = Officer(
                name="Test Officer",
                department=Department.WATER_DEPT,
                phone="1234567890",
                email="test@example.com",
                location_latitude=40.7128,
                location_longitude=-74.0060,
                assigned_cases=0
            )
            
            # Create complaint
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED
            )
            
            db.session.add_all([officer, complaint])
            db.session.commit()
            
            initial_cases = officer.assigned_cases
            
            # Assign complaint
            success, error = service.assign_complaint(
                complaint.complaint_id, officer.officer_id
            )
            
            assert success is True
            assert error is None
            
            # Verify complaint updated
            db.session.refresh(complaint)
            assert complaint.assigned_officer_id == officer.officer_id
            assert complaint.status == Status.ASSIGNED
            assert complaint.assigned_at is not None
            
            # Verify officer workload increased
            db.session.refresh(officer)
            assert officer.assigned_cases == initial_cases + 1
            
            # Cleanup
            db.session.delete(officer)
            db.session.delete(complaint)
            db.session.commit()
    
    def test_assign_complaint_invalid_complaint(self, service, app):
        """Test assignment with invalid complaint ID."""
        with app.app_context():
            # Try to assign non-existent complaint
            success, error = service.assign_complaint(
                "invalid-complaint-id", "invalid-officer-id"
            )
            
            assert success is False
            assert error is not None
            assert "not found" in error.lower()
    
    def test_assign_complaint_invalid_officer(self, service, app):
        """Test assignment with invalid officer ID."""
        with app.app_context():
            # Create complaint
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED
            )
            db.session.add(complaint)
            db.session.commit()
            
            # Try to assign to non-existent officer
            success, error = service.assign_complaint(
                complaint.complaint_id, "invalid-officer-id"
            )
            
            assert success is False
            assert error is not None
            assert "not found" in error.lower()
            
            # Cleanup
            db.session.delete(complaint)
            db.session.commit()
    
    def test_route_complaint_success(self, service, app):
        """Test complete routing workflow."""
        with app.app_context():
            # Create officer
            officer = Officer(
                name="Route Officer",
                department=Department.WATER_DEPT,
                phone="1234567890",
                email="route@example.com",
                location_latitude=40.7128,
                location_longitude=-74.0060,
                assigned_cases=0
            )
            
            # Create complaint with location
            location = Location(
                latitude=40.7128,
                longitude=-74.0060,
                address="Test Street"
            )
            
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak on Test Street",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=location
            )
            
            db.session.add_all([officer, location, complaint])
            db.session.commit()
            
            # Route complaint
            success, error = service.route_complaint(complaint.complaint_id)
            
            assert success is True
            assert error is None
            
            # Verify complaint was assigned
            db.session.refresh(complaint)
            assert complaint.assigned_officer_id == officer.officer_id
            assert complaint.status == Status.ASSIGNED
            
            # Cleanup
            db.session.delete(complaint)
            db.session.delete(location)
            db.session.delete(officer)
            db.session.commit()
    
    def test_route_complaint_no_location(self, service, app):
        """Test routing fails when complaint has no location."""
        with app.app_context():
            # Create complaint without location
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED
            )
            db.session.add(complaint)
            db.session.commit()
            
            # Try to route complaint
            success, error = service.route_complaint(complaint.complaint_id)
            
            assert success is False
            assert error is not None
            assert "no location" in error.lower()
            
            # Cleanup
            db.session.delete(complaint)
            db.session.commit()
    
    def test_route_complaint_no_available_officers(self, service, app):
        """Test routing fails when no officers are available."""
        with app.app_context():
            # Create complaint with location but no officers
            location = Location(
                latitude=40.7128,
                longitude=-74.0060,
                address="Test Street"
            )
            
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=location
            )
            
            db.session.add_all([location, complaint])
            db.session.commit()
            
            # Try to route complaint
            success, error = service.route_complaint(complaint.complaint_id)
            
            assert success is False
            assert error is not None
            assert "no available officers" in error.lower()
            
            # Cleanup
            db.session.delete(complaint)
            db.session.delete(location)
            db.session.commit()
    
    def test_singleton_instance(self):
        """Test that get_routing_service returns singleton."""
        service1 = get_routing_service()
        service2 = get_routing_service()
        
        # Should be the same instance
        assert service1 is service2
    
    def test_balance_workload_equal_workload(self, service):
        """Test workload balancing when officers have equal workload."""
        # Create officers with same workload but different distances
        officer1 = Officer(
            name="Officer 1",
            department=Department.WATER_DEPT,
            phone="1111111111",
            email="officer1@example.com",
            location_latitude=40.7128,
            location_longitude=-74.0060,
            assigned_cases=3
        )
        
        officer2 = Officer(
            name="Officer 2",
            department=Department.WATER_DEPT,
            phone="2222222222",
            email="officer2@example.com",
            location_latitude=40.7200,
            location_longitude=-74.0100,
            assigned_cases=3
        )
        
        officers_with_distance = [
            (officer1, 5.0),  # Closer
            (officer2, 8.0)   # Farther
        ]
        
        selected = service.balance_workload(officers_with_distance)
        
        # Should select closer officer when workload is equal
        assert selected.name == "Officer 1"
    
    def test_balance_workload_different_workload(self, service):
        """Test workload balancing prioritizes lower workload."""
        # Create officers with different workloads
        officer1 = Officer(
            name="Officer 1",
            department=Department.WATER_DEPT,
            phone="1111111111",
            email="officer1@example.com",
            location_latitude=40.7128,
            location_longitude=-74.0060,
            assigned_cases=5
        )
        
        officer2 = Officer(
            name="Officer 2",
            department=Department.WATER_DEPT,
            phone="2222222222",
            email="officer2@example.com",
            location_latitude=40.7200,
            location_longitude=-74.0100,
            assigned_cases=2  # Lower workload
        )
        
        officers_with_distance = [
            (officer1, 3.0),  # Closer but more workload
            (officer2, 8.0)   # Farther but less workload
        ]
        
        selected = service.balance_workload(officers_with_distance)
        
        # Should select officer with lower workload
        assert selected.name == "Officer 2"


# Fixture for Flask app context
@pytest.fixture
def app():
    """Create Flask app for testing."""
    from flask import Flask
    from config import Config
    
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Create a minimal Flask app
    flask_app = Flask(__name__)
    flask_app.config.from_object(TestConfig)
    
    # Initialize database
    db.init_app(flask_app)
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
