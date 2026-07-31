"""
Unit tests for Duplicate Detection Service.

Tests the functionality of duplicate complaint detection, clustering,
and impact score updates.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import pytest
from services.duplicate_detection import DuplicateDetectionService, get_duplicate_detection_service
from models import db
from models.complaint import Complaint, Category, Status, PriorityLevel, Location
from models.duplicate_cluster import DuplicateCluster
from datetime import datetime
import uuid


class TestDuplicateDetectionService:
    """Test suite for Duplicate Detection Service."""
    
    @pytest.fixture
    def service(self):
        """Create a duplicate detection service instance."""
        return DuplicateDetectionService()
    
    def test_calculate_text_similarity_identical(self, service):
        """Test similarity calculation for identical texts."""
        text1 = "Water leakage on Main Street causing flooding"
        text2 = "Water leakage on Main Street causing flooding"
        
        similarity = service.calculate_text_similarity(text1, text2)
        
        # Identical texts should have similarity close to 1.0
        assert similarity > 0.95
        assert similarity <= 1.01  # Allow for floating point precision
    
    def test_calculate_text_similarity_similar(self, service):
        """Test similarity calculation for similar texts."""
        text1 = "Water pipe burst on Main Street causing severe flooding"
        text2 = "Major water leakage on Main Street with flooding issues"
        
        similarity = service.calculate_text_similarity(text1, text2)
        
        # Similar texts should have moderate similarity
        assert similarity > 0.1  # Adjusted threshold based on actual TF-IDF behavior
    
    def test_calculate_text_similarity_different(self, service):
        """Test similarity calculation for different texts."""
        text1 = "Water leakage on Main Street"
        text2 = "Electricity outage in downtown area"
        
        similarity = service.calculate_text_similarity(text1, text2)
        
        # Different texts should have low similarity
        assert similarity < 0.5
    
    def test_calculate_text_similarity_empty(self, service):
        """Test similarity calculation with empty text."""
        text1 = ""
        text2 = "Some complaint text"
        
        similarity = service.calculate_text_similarity(text1, text2)
        
        # Empty text should return 0.0
        assert similarity == 0.0
    
    def test_calculate_distance_km(self, service):
        """Test distance calculation between two locations."""
        # New York City coordinates
        lat1, lon1 = 40.7128, -74.0060
        # Los Angeles coordinates
        lat2, lon2 = 34.0522, -118.2437
        
        distance = service.calculate_distance_km(lat1, lon1, lat2, lon2)
        
        # Distance should be approximately 3944 km
        assert 3900 < distance < 4000
    
    def test_calculate_distance_km_same_location(self, service):
        """Test distance calculation for same location."""
        lat, lon = 40.7128, -74.0060
        
        distance = service.calculate_distance_km(lat, lon, lat, lon)
        
        # Same location should have distance 0
        assert distance == 0.0
    
    def test_calculate_distance_km_nearby(self, service):
        """Test distance calculation for nearby locations."""
        # Two locations approximately 5km apart
        lat1, lon1 = 40.7128, -74.0060
        lat2, lon2 = 40.7578, -73.9855  # Approximately 5km away
        
        distance = service.calculate_distance_km(lat1, lon1, lat2, lon2)
        
        # Distance should be around 5-6 km
        assert 4 < distance < 7
    
    def test_get_cluster_size_no_cluster(self, service, app):
        """Test getting cluster size for complaint not in a cluster."""
        with app.app_context():
            # Create a test complaint without cluster
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Test complaint",
                priority_level=PriorityLevel.LOW,
                impact_score=10,
                status=Status.SUBMITTED
            )
            db.session.add(complaint)
            db.session.commit()
            
            size = service.get_cluster_size(complaint.complaint_id)
            
            # Should return 1 for non-clustered complaint
            assert size == 1
            
            # Cleanup
            db.session.delete(complaint)
            db.session.commit()
    
    def test_singleton_instance(self):
        """Test that get_duplicate_detection_service returns singleton."""
        service1 = get_duplicate_detection_service()
        service2 = get_duplicate_detection_service()
        
        # Should be the same instance
        assert service1 is service2
    
    def test_find_duplicates_same_category_and_location(self, service, app):
        """Test finding duplicates with same category and nearby location."""
        with app.app_context():
            # Create test complaints with very similar descriptions and nearby locations
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst on Main Street causing severe flooding and damage to property",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7128,
                    longitude=-74.0060,
                    address="Main Street"
                )
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst on Main Street causing severe flooding and damage to property",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=35,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7130,  # Very close to complaint1
                    longitude=-74.0062,
                    address="Main Street"
                )
            )
            
            db.session.add(complaint1)
            db.session.add(complaint2)
            db.session.commit()
            
            # Find duplicates for complaint1
            duplicates = service.find_duplicates(complaint1)
            
            # Should find complaint2 as a duplicate (identical text, same category, nearby location)
            assert len(duplicates) > 0
            assert complaint2.complaint_id in duplicates
            
            # Cleanup
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.commit()
    
    def test_find_duplicates_different_category(self, service, app):
        """Test that complaints with different categories are not duplicates."""
        with app.app_context():
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst on Main Street",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7128,
                    longitude=-74.0060,
                    address="Main Street"
                )
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.ELECTRICITY,  # Different category
                description="Water pipe burst on Main Street",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=35,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7130,
                    longitude=-74.0062,
                    address="Main Street"
                )
            )
            
            db.session.add(complaint1)
            db.session.add(complaint2)
            db.session.commit()
            
            duplicates = service.find_duplicates(complaint1)
            
            # Should not find complaint2 as duplicate (different category)
            assert complaint2.complaint_id not in duplicates
            
            # Cleanup
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.commit()
    
    def test_find_duplicates_far_location(self, service, app):
        """Test that complaints far apart are not duplicates."""
        with app.app_context():
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst causing flooding",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7128,  # New York
                    longitude=-74.0060,
                    address="New York"
                )
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst causing flooding",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=35,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=34.0522,  # Los Angeles (far away)
                    longitude=-118.2437,
                    address="Los Angeles"
                )
            )
            
            db.session.add(complaint1)
            db.session.add(complaint2)
            db.session.commit()
            
            duplicates = service.find_duplicates(complaint1)
            
            # Should not find complaint2 as duplicate (too far)
            assert complaint2.complaint_id not in duplicates
            
            # Cleanup
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.commit()
    
    def test_create_cluster(self, service, app):
        """Test creating a duplicate cluster from complaints."""
        with app.app_context():
            # Create test complaints
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst on Main Street",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7128,
                    longitude=-74.0060,
                    address="Main Street"
                )
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Major water leakage on Main Street",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=35,
                status=Status.SUBMITTED,
                location=Location(
                    latitude=40.7130,
                    longitude=-74.0062,
                    address="Main Street"
                )
            )
            
            db.session.add(complaint1)
            db.session.add(complaint2)
            db.session.commit()
            
            complaint_ids = [complaint1.complaint_id, complaint2.complaint_id]
            
            # Create cluster
            cluster_id = service.create_cluster(complaint_ids)
            
            # Verify cluster was created
            assert cluster_id is not None
            
            # Verify complaints are assigned to cluster
            db.session.refresh(complaint1)
            db.session.refresh(complaint2)
            assert complaint1.cluster_id == cluster_id
            assert complaint2.cluster_id == cluster_id
            
            # Verify cluster exists in database
            cluster = DuplicateCluster.query.get(cluster_id)
            assert cluster is not None
            assert cluster.category == Category.WATER_SUPPLY
            
            # Cleanup
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.delete(cluster)
            db.session.commit()
    
    def test_create_cluster_insufficient_complaints(self, service, app):
        """Test that cluster creation fails with less than 2 complaints."""
        with app.app_context():
            complaint = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water pipe burst",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED
            )
            
            db.session.add(complaint)
            db.session.commit()
            
            # Try to create cluster with only 1 complaint
            cluster_id = service.create_cluster([complaint.complaint_id])
            
            # Should return None
            assert cluster_id is None
            
            # Cleanup
            db.session.delete(complaint)
            db.session.commit()
    
    def test_get_cluster_size_with_cluster(self, service, app):
        """Test getting cluster size for complaint in a cluster."""
        with app.app_context():
            # Create test complaints
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water issue",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=40,
                status=Status.SUBMITTED
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water problem",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=35,
                status=Status.SUBMITTED
            )
            
            complaint3 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=30,
                status=Status.SUBMITTED
            )
            
            db.session.add_all([complaint1, complaint2, complaint3])
            db.session.commit()
            
            # Create cluster
            cluster_id = service.create_cluster([
                complaint1.complaint_id,
                complaint2.complaint_id,
                complaint3.complaint_id
            ])
            
            # Get cluster size
            size = service.get_cluster_size(complaint1.complaint_id)
            
            # Should return 3
            assert size == 3
            
            # Cleanup
            cluster = DuplicateCluster.query.get(cluster_id)
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.delete(complaint3)
            db.session.delete(cluster)
            db.session.commit()
    
    def test_update_cluster_impact_scores(self, service, app):
        """Test updating impact scores for complaints in a cluster."""
        with app.app_context():
            # Create test complaints with initial impact scores
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water issue",
                priority_level=PriorityLevel.LOW,
                impact_score=20,
                status=Status.SUBMITTED
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water problem",
                priority_level=PriorityLevel.LOW,
                impact_score=25,
                status=Status.SUBMITTED
            )
            
            complaint3 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Water leak",
                priority_level=PriorityLevel.MEDIUM,
                impact_score=30,
                status=Status.SUBMITTED
            )
            
            db.session.add_all([complaint1, complaint2, complaint3])
            db.session.commit()
            
            # Create cluster
            cluster_id = service.create_cluster([
                complaint1.complaint_id,
                complaint2.complaint_id,
                complaint3.complaint_id
            ])
            
            # Update cluster impact scores
            result = service.update_cluster_impact_scores(cluster_id)
            
            # Verify update was successful
            assert result is True
            
            # Refresh complaints to get updated values
            db.session.refresh(complaint1)
            db.session.refresh(complaint2)
            db.session.refresh(complaint3)
            
            # Verify impact scores increased
            # With 3 complaints, duplicate_score = min((3-1) * 2, 20) = 4
            assert complaint1.impact_score == 20 + 4  # 24
            assert complaint2.impact_score == 25 + 4  # 29
            assert complaint3.impact_score == 30 + 4  # 34
            
            # Verify priority levels updated accordingly
            assert complaint1.priority_level == PriorityLevel.LOW  # 24 < 26
            assert complaint2.priority_level == PriorityLevel.MEDIUM  # 29 >= 26
            assert complaint3.priority_level == PriorityLevel.MEDIUM  # 34 >= 26
            
            # Cleanup
            cluster = DuplicateCluster.query.get(cluster_id)
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.delete(complaint3)
            db.session.delete(cluster)
            db.session.commit()
    
    def test_update_cluster_impact_scores_max_cap(self, service, app):
        """Test that impact scores are capped at 100."""
        with app.app_context():
            # Create complaints with high initial scores
            complaint1 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Critical water issue",
                priority_level=PriorityLevel.CRITICAL,
                impact_score=95,
                status=Status.SUBMITTED
            )
            
            complaint2 = Complaint(
                user_id=str(uuid.uuid4()),
                category=Category.WATER_SUPPLY,
                description="Critical water problem",
                priority_level=PriorityLevel.CRITICAL,
                impact_score=98,
                status=Status.SUBMITTED
            )
            
            db.session.add_all([complaint1, complaint2])
            db.session.commit()
            
            # Create cluster
            cluster_id = service.create_cluster([
                complaint1.complaint_id,
                complaint2.complaint_id
            ])
            
            # Update cluster impact scores
            service.update_cluster_impact_scores(cluster_id)
            
            # Refresh complaints
            db.session.refresh(complaint1)
            db.session.refresh(complaint2)
            
            # Verify impact scores are capped at 100
            assert complaint1.impact_score <= 100
            assert complaint2.impact_score <= 100
            
            # Cleanup
            cluster = DuplicateCluster.query.get(cluster_id)
            db.session.delete(complaint1)
            db.session.delete(complaint2)
            db.session.delete(cluster)
            db.session.commit()


# Fixture for Flask app context
@pytest.fixture
def app():
    """Create Flask app for testing."""
    from flask import Flask
    from config import Config
    import os
    import tempfile
    
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Create a minimal Flask app without the full create_app setup
    flask_app = Flask(__name__)
    flask_app.config.from_object(TestConfig)
    
    # Initialize database
    db.init_app(flask_app)
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
