"""
Priority Scoring Engine Service for calculating complaint impact scores.

This module provides functionality to:
- Calculate impact scores based on multiple factors
- Assign priority levels based on impact scores
- Generate human-readable explanations for priority decisions

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.1, 7.2
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from models import Category, PriorityLevel

logger = logging.getLogger(__name__)


class PriorityScoringEngine:
    """
    Priority scoring engine for calculating complaint impact scores and priority levels.
    
    The engine uses a multi-factor scoring algorithm that considers:
    - Severity keywords in the complaint text
    - Location sensitivity (proximity to hospitals, schools, highways)
    - Essential service type (electricity, water, healthcare)
    - Duplicate complaint count
    - Time decay (age of complaint)
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    
    # Severity term scoring (0-30 points)
    CRITICAL_SEVERITY_TERMS = ["fire", "electric shock", "death"]
    HIGH_SEVERITY_TERMS = ["accident", "injury", "collapse"]
    MEDIUM_SEVERITY_TERMS = ["flooding", "leakage"]
    
    # Location sensitivity scoring (0-25 points)
    LOCATION_SCORES = {
        "hospital": 25,
        "school": 20,
        "highway": 15,
        "market": 10,
        "residential": 5
    }
    
    # Essential service categories (0-15 points)
    ESSENTIAL_SERVICES = {
        Category.ELECTRICITY: 15,
        Category.WATER_SUPPLY: 15,
        Category.HEALTHCARE: 15,
        Category.PUBLIC_SAFETY: 10,
        Category.SANITATION: 5,
        Category.ROADS_INFRASTRUCTURE: 5
    }
    
    # Priority level thresholds
    PRIORITY_THRESHOLDS = {
        PriorityLevel.CRITICAL: 76,
        PriorityLevel.HIGH: 51,
        PriorityLevel.MEDIUM: 26,
        PriorityLevel.LOW: 0
    }
    
    def __init__(self):
        """Initialize the Priority Scoring Engine."""
        logger.info("Priority Scoring Engine initialized")
    
    def calculate_severity_score(self, severity_terms: List[str]) -> Tuple[int, str]:
        """
        Calculate score based on severity terms detected in complaint.
        
        Args:
            severity_terms: List of severity terms found in complaint text
            
        Returns:
            Tuple of (score, explanation)
            - score: Points awarded (0-30)
            - explanation: Human-readable reason for the score
            
        Requirements: 5.1
        """
        if not severity_terms:
            return 0, "No severity terms detected"
        
        score = 0
        detected_critical = []
        detected_high = []
        detected_medium = []
        
        for term in severity_terms:
            if term in self.CRITICAL_SEVERITY_TERMS:
                detected_critical.append(term)
            elif term in self.HIGH_SEVERITY_TERMS:
                detected_high.append(term)
            elif term in self.MEDIUM_SEVERITY_TERMS:
                detected_medium.append(term)
        
        # Award points based on highest severity detected
        if detected_critical:
            score = 30
            explanation = f"Critical severity terms detected: {', '.join(detected_critical)}"
        elif detected_high:
            score = 20
            explanation = f"High severity terms detected: {', '.join(detected_high)}"
        elif detected_medium:
            score = 10
            explanation = f"Medium severity terms detected: {', '.join(detected_medium)}"
        else:
            explanation = "Severity terms detected but not categorized"
        
        logger.debug(f"Severity score: {score} - {explanation}")
        return score, explanation

    
    def calculate_location_score(self, nearby_sensitive_locations: List[str]) -> Tuple[int, str]:
        """
        Calculate score based on proximity to sensitive locations.
        
        Args:
            nearby_sensitive_locations: List of nearby sensitive location types
                                       (e.g., ["hospital", "school"])
            
        Returns:
            Tuple of (score, explanation)
            - score: Points awarded (0-25)
            - explanation: Human-readable reason for the score
            
        Requirements: 5.2
        """
        if not nearby_sensitive_locations:
            return 0, "No sensitive locations nearby"
        
        # Get the highest scoring location type
        max_score = 0
        max_location = None
        
        for location_type in nearby_sensitive_locations:
            location_lower = location_type.lower()
            if location_lower in self.LOCATION_SCORES:
                score = self.LOCATION_SCORES[location_lower]
                if score > max_score:
                    max_score = score
                    max_location = location_type
        
        if max_score > 0:
            explanation = f"Near sensitive location: {max_location}"
        else:
            explanation = "Near locations but not highly sensitive"
        
        logger.debug(f"Location score: {max_score} - {explanation}")
        return max_score, explanation
    
    def calculate_service_type_score(self, category: Category) -> Tuple[int, str]:
        """
        Calculate score based on whether the complaint involves essential services.
        
        Args:
            category: Complaint category
            
        Returns:
            Tuple of (score, explanation)
            - score: Points awarded (0-15)
            - explanation: Human-readable reason for the score
            
        Requirements: 5.3
        """
        score = self.ESSENTIAL_SERVICES.get(category, 0)
        
        if score >= 15:
            explanation = f"Essential service: {category.value}"
        elif score >= 5:
            explanation = f"Important service: {category.value}"
        else:
            explanation = f"Standard service: {category.value}"
        
        logger.debug(f"Service type score: {score} - {explanation}")
        return score, explanation
    
    def calculate_duplicate_score(self, duplicate_count: int) -> Tuple[int, str]:
        """
        Calculate score based on number of duplicate complaints.
        
        More duplicates indicate a widespread issue affecting multiple citizens.
        
        Args:
            duplicate_count: Number of similar complaints
            
        Returns:
            Tuple of (score, explanation)
            - score: Points awarded (0-20)
            - explanation: Human-readable reason for the score
            
        Requirements: 5.4
        """
        # Award 2 points per duplicate, capped at 20 points
        score = min(duplicate_count * 2, 20)
        
        if duplicate_count == 0:
            explanation = "No duplicate complaints found"
        elif duplicate_count == 1:
            explanation = "1 similar complaint found"
        else:
            explanation = f"{duplicate_count} similar complaints found (widespread issue)"
        
        logger.debug(f"Duplicate score: {score} - {explanation}")
        return score, explanation
    
    def calculate_time_decay_score(self, age_hours: float) -> Tuple[int, str]:
        """
        Calculate score based on how long the complaint has been unresolved.
        
        Older complaints receive higher scores to ensure they don't get ignored.
        
        Args:
            age_hours: Hours since complaint was created
            
        Returns:
            Tuple of (score, explanation)
            - score: Points awarded (0-10)
            - explanation: Human-readable reason for the score
            
        Requirements: 5.5
        """
        if age_hours > 72:  # More than 3 days
            score = 10
            explanation = f"Complaint is {int(age_hours)} hours old (>3 days)"
        elif age_hours > 48:  # More than 2 days
            score = 7
            explanation = f"Complaint is {int(age_hours)} hours old (>2 days)"
        elif age_hours > 24:  # More than 1 day
            score = 5
            explanation = f"Complaint is {int(age_hours)} hours old (>1 day)"
        else:
            score = 0
            explanation = f"Complaint is {int(age_hours)} hours old (recent)"
        
        logger.debug(f"Time decay score: {score} - {explanation}")
        return score, explanation

    
    def calculate_impact_score(
        self,
        severity_terms: List[str],
        nearby_sensitive_locations: List[str],
        category: Category,
        duplicate_count: int,
        created_at: datetime
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate the overall impact score for a complaint.
        
        This is the main scoring function that combines all factors to produce
        a final impact score between 0 and 100.
        
        Args:
            severity_terms: List of severity terms detected in complaint
            nearby_sensitive_locations: List of nearby sensitive location types
            category: Complaint category
            duplicate_count: Number of similar complaints
            created_at: Timestamp when complaint was created
            
        Returns:
            Tuple of (impact_score, factors_dict)
            - impact_score: Final score (0-100)
            - factors_dict: Dictionary containing individual factor scores and explanations
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        # Calculate age in hours
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        
        # Calculate individual factor scores
        severity_score, severity_explanation = self.calculate_severity_score(severity_terms)
        location_score, location_explanation = self.calculate_location_score(nearby_sensitive_locations)
        service_score, service_explanation = self.calculate_service_type_score(category)
        duplicate_score, duplicate_explanation = self.calculate_duplicate_score(duplicate_count)
        time_score, time_explanation = self.calculate_time_decay_score(age_hours)
        
        # Calculate total impact score (capped at 100)
        base_score = (
            severity_score +
            location_score +
            service_score +
            duplicate_score +
            time_score
        )
        impact_score = min(base_score, 100)
        
        # Build factors dictionary for explanation generation
        factors = {
            'severity': {
                'score': severity_score,
                'explanation': severity_explanation
            },
            'location': {
                'score': location_score,
                'explanation': location_explanation
            },
            'service_type': {
                'score': service_score,
                'explanation': service_explanation
            },
            'duplicates': {
                'score': duplicate_score,
                'explanation': duplicate_explanation
            },
            'time_decay': {
                'score': time_score,
                'explanation': time_explanation
            },
            'total_score': impact_score
        }
        
        logger.info(
            f"Impact score calculated: {impact_score} "
            f"(severity={severity_score}, location={location_score}, "
            f"service={service_score}, duplicates={duplicate_score}, time={time_score})"
        )
        
        return impact_score, factors

    
    def assign_priority_level(self, impact_score: int) -> PriorityLevel:
        """
        Map impact score to priority level.
        
        Priority levels are assigned based on score thresholds:
        - CRITICAL: 76-100
        - HIGH: 51-75
        - MEDIUM: 26-50
        - LOW: 0-25
        
        Args:
            impact_score: Calculated impact score (0-100)
            
        Returns:
            PriorityLevel enum value
            
        Requirements: 5.6
        """
        if impact_score >= self.PRIORITY_THRESHOLDS[PriorityLevel.CRITICAL]:
            priority = PriorityLevel.CRITICAL
        elif impact_score >= self.PRIORITY_THRESHOLDS[PriorityLevel.HIGH]:
            priority = PriorityLevel.HIGH
        elif impact_score >= self.PRIORITY_THRESHOLDS[PriorityLevel.MEDIUM]:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW
        
        logger.info(f"Assigned priority level: {priority.value} (score: {impact_score})")
        return priority

    
    def generate_explanation(self, factors: Dict[str, Any], priority_level: PriorityLevel) -> str:
        """
        Generate a human-readable explanation of priority decision.
        
        The explanation lists all factors that contributed to the priority score,
        making the AI decision transparent and trustworthy.
        
        Args:
            factors: Dictionary containing individual factor scores and explanations
            priority_level: Assigned priority level
            
        Returns:
            Human-readable explanation string
            
        Requirements: 7.1, 7.2
        """
        total_score = factors['total_score']
        
        # Start with priority level and total score
        explanation_parts = [
            f"Priority: {priority_level.value} (Impact Score: {total_score}/100)"
        ]
        
        # Add contributing factors (only those with non-zero scores)
        contributing_factors = []
        
        if factors['severity']['score'] > 0:
            contributing_factors.append(
                f"Severity: {factors['severity']['explanation']} (+{factors['severity']['score']} points)"
            )
        
        if factors['location']['score'] > 0:
            contributing_factors.append(
                f"Location: {factors['location']['explanation']} (+{factors['location']['score']} points)"
            )
        
        if factors['service_type']['score'] > 0:
            contributing_factors.append(
                f"Service Type: {factors['service_type']['explanation']} (+{factors['service_type']['score']} points)"
            )
        
        if factors['duplicates']['score'] > 0:
            contributing_factors.append(
                f"Duplicates: {factors['duplicates']['explanation']} (+{factors['duplicates']['score']} points)"
            )
        
        if factors['time_decay']['score'] > 0:
            contributing_factors.append(
                f"Age: {factors['time_decay']['explanation']} (+{factors['time_decay']['score']} points)"
            )
        
        if contributing_factors:
            explanation_parts.append("\nContributing factors:")
            for factor in contributing_factors:
                explanation_parts.append(f"• {factor}")
        else:
            explanation_parts.append("\nNo significant priority factors detected.")
        
        explanation = "\n".join(explanation_parts)
        logger.debug(f"Generated explanation: {explanation}")
        return explanation
    
    def calculate_priority(
        self,
        severity_terms: List[str],
        nearby_sensitive_locations: List[str],
        category: Category,
        duplicate_count: int,
        created_at: datetime
    ) -> Tuple[int, PriorityLevel, str]:
        """
        Complete priority calculation pipeline.
        
        This is the main method to use for calculating complaint priority.
        It combines impact score calculation, priority level assignment,
        and explanation generation.
        
        Args:
            severity_terms: List of severity terms detected in complaint
            nearby_sensitive_locations: List of nearby sensitive location types
            category: Complaint category
            duplicate_count: Number of similar complaints
            created_at: Timestamp when complaint was created
            
        Returns:
            Tuple of (impact_score, priority_level, explanation)
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.1, 7.2
        """
        # Calculate impact score
        impact_score, factors = self.calculate_impact_score(
            severity_terms=severity_terms,
            nearby_sensitive_locations=nearby_sensitive_locations,
            category=category,
            duplicate_count=duplicate_count,
            created_at=created_at
        )
        
        # Assign priority level
        priority_level = self.assign_priority_level(impact_score)
        
        # Generate explanation
        explanation = self.generate_explanation(factors, priority_level)
        
        logger.info(
            f"Priority calculation complete: Score={impact_score}, "
            f"Level={priority_level.value}"
        )
        
        return impact_score, priority_level, explanation


# Singleton instance
_priority_scoring_engine = None


def get_priority_scoring_engine() -> PriorityScoringEngine:
    """
    Get or create the singleton Priority Scoring Engine instance.
    
    Returns:
        PriorityScoringEngine instance
    """
    global _priority_scoring_engine
    if _priority_scoring_engine is None:
        _priority_scoring_engine = PriorityScoringEngine()
    return _priority_scoring_engine
