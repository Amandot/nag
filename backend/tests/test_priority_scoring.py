"""
Unit tests for Priority Scoring Engine.

Tests cover:
- Score calculation with various inputs
- Priority level mapping
- Explanation generation

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

import pytest
from datetime import datetime, timedelta
from services.priority_scoring import PriorityScoringEngine
from models import Category, PriorityLevel


class TestPriorityScoringEngine:
    """Test suite for Priority Scoring Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a Priority Scoring Engine instance for testing."""
        return PriorityScoringEngine()
    
    # Test severity score calculation (Requirement 5.1)
    
    def test_severity_score_critical_terms(self, engine):
        """Test severity scoring with critical terms."""
        severity_terms = ["fire", "death"]
        score, explanation = engine.calculate_severity_score(severity_terms)
        
        assert score == 30
        assert "Critical severity terms detected" in explanation
        assert "fire" in explanation or "death" in explanation
    
    def test_severity_score_high_terms(self, engine):
        """Test severity scoring with high severity terms."""
        severity_terms = ["accident", "injury"]
        score, explanation = engine.calculate_severity_score(severity_terms)
        
        assert score == 20
        assert "High severity terms detected" in explanation
    
    def test_severity_score_medium_terms(self, engine):
        """Test severity scoring with medium severity terms."""
        severity_terms = ["flooding", "leakage"]
        score, explanation = engine.calculate_severity_score(severity_terms)
        
        assert score == 10
        assert "Medium severity terms detected" in explanation
    
    def test_severity_score_no_terms(self, engine):
        """Test severity scoring with no terms."""
        severity_terms = []
        score, explanation = engine.calculate_severity_score(severity_terms)
        
        assert score == 0
        assert "No severity terms detected" in explanation
    
    def test_severity_score_mixed_terms(self, engine):
        """Test severity scoring with mixed severity terms (should use highest)."""
        severity_terms = ["fire", "leakage", "accident"]
        score, explanation = engine.calculate_severity_score(severity_terms)
        
        assert score == 30  # Should use critical term score
        assert "Critical severity terms detected" in explanation
    
    # Test location score calculation (Requirement 5.2)
    
    def test_location_score_hospital(self, engine):
        """Test location scoring near hospital."""
        nearby_locations = ["hospital"]
        score, explanation = engine.calculate_location_score(nearby_locations)
        
        assert score == 25
        assert "hospital" in explanation.lower()
    
    def test_location_score_school(self, engine):
        """Test location scoring near school."""
        nearby_locations = ["school"]
        score, explanation = engine.calculate_location_score(nearby_locations)
        
        assert score == 20
        assert "school" in explanation.lower()
    
    def test_location_score_highway(self, engine):
        """Test location scoring near highway."""
        nearby_locations = ["highway"]
        score, explanation = engine.calculate_location_score(nearby_locations)
        
        assert score == 15
        assert "highway" in explanation.lower()
    
    def test_location_score_no_locations(self, engine):
        """Test location scoring with no nearby sensitive locations."""
        nearby_locations = []
        score, explanation = engine.calculate_location_score(nearby_locations)
        
        assert score == 0
        assert "No sensitive locations nearby" in explanation
    
    def test_location_score_multiple_locations(self, engine):
        """Test location scoring with multiple locations (should use highest)."""
        nearby_locations = ["school", "hospital", "market"]
        score, explanation = engine.calculate_location_score(nearby_locations)
        
        assert score == 25  # Should use hospital score
        assert "hospital" in explanation.lower()
    
    # Test service type score calculation (Requirement 5.3)
    
    def test_service_type_score_essential(self, engine):
        """Test service type scoring for essential services."""
        score, explanation = engine.calculate_service_type_score(Category.ELECTRICITY)
        assert score == 15
        assert "Essential service" in explanation
        
        score, explanation = engine.calculate_service_type_score(Category.WATER_SUPPLY)
        assert score == 15
        
        score, explanation = engine.calculate_service_type_score(Category.HEALTHCARE)
        assert score == 15
    
    def test_service_type_score_important(self, engine):
        """Test service type scoring for important services."""
        score, explanation = engine.calculate_service_type_score(Category.PUBLIC_SAFETY)
        assert score == 10
        assert "Important service" in explanation or "Public Safety" in explanation
    
    def test_service_type_score_standard(self, engine):
        """Test service type scoring for standard services."""
        score, explanation = engine.calculate_service_type_score(Category.SANITATION)
        assert score == 5
        
        score, explanation = engine.calculate_service_type_score(Category.ROADS_INFRASTRUCTURE)
        assert score == 5
    
    # Test duplicate score calculation (Requirement 5.4)
    
    def test_duplicate_score_no_duplicates(self, engine):
        """Test duplicate scoring with no duplicates."""
        score, explanation = engine.calculate_duplicate_score(0)
        
        assert score == 0
        assert "No duplicate complaints found" in explanation
    
    def test_duplicate_score_single_duplicate(self, engine):
        """Test duplicate scoring with one duplicate."""
        score, explanation = engine.calculate_duplicate_score(1)
        
        assert score == 2
        assert "1 similar complaint found" in explanation
    
    def test_duplicate_score_multiple_duplicates(self, engine):
        """Test duplicate scoring with multiple duplicates."""
        score, explanation = engine.calculate_duplicate_score(5)
        
        assert score == 10
        assert "5 similar complaints found" in explanation
        assert "widespread issue" in explanation
    
    def test_duplicate_score_capped_at_20(self, engine):
        """Test duplicate scoring is capped at 20 points."""
        score, explanation = engine.calculate_duplicate_score(15)
        
        assert score == 20  # Should be capped at 20
        assert "15 similar complaints found" in explanation
    
    # Test time decay score calculation (Requirement 5.5)
    
    def test_time_decay_score_recent(self, engine):
        """Test time decay scoring for recent complaints."""
        score, explanation = engine.calculate_time_decay_score(12)  # 12 hours
        
        assert score == 0
        assert "recent" in explanation.lower()
    
    def test_time_decay_score_one_day(self, engine):
        """Test time decay scoring for complaints over 1 day old."""
        score, explanation = engine.calculate_time_decay_score(30)  # 30 hours
        
        assert score == 5
        assert ">1 day" in explanation
    
    def test_time_decay_score_two_days(self, engine):
        """Test time decay scoring for complaints over 2 days old."""
        score, explanation = engine.calculate_time_decay_score(50)  # 50 hours
        
        assert score == 7
        assert ">2 days" in explanation
    
    def test_time_decay_score_three_days(self, engine):
        """Test time decay scoring for complaints over 3 days old."""
        score, explanation = engine.calculate_time_decay_score(80)  # 80 hours
        
        assert score == 10
        assert ">3 days" in explanation
    
    # Test impact score calculation (Requirements 5.1, 5.2, 5.3, 5.4, 5.5)
    
    def test_calculate_impact_score_minimal(self, engine):
        """Test impact score calculation with minimal factors."""
        created_at = datetime.utcnow()
        
        impact_score, factors = engine.calculate_impact_score(
            severity_terms=[],
            nearby_sensitive_locations=[],
            category=Category.SANITATION,
            duplicate_count=0,
            created_at=created_at
        )
        
        assert impact_score >= 0
        assert "severity" in factors
        assert "location" in factors
        assert "service_type" in factors
        assert "duplicates" in factors
        assert "time_decay" in factors