"""
Duplicate Detection Service for identifying and grouping similar complaints.

This module provides functionality to:
- Calculate text similarity between complaints using TF-IDF and cosine similarity
- Detect duplicate complaints based on similarity threshold
- Create and manage duplicate clusters
- Update impact scores for clustered complaints

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from models import db
from models.complaint import Complaint, Category, PriorityLevel
from models.duplicate_cluster import DuplicateCluster
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """
    Service for detecting and managing duplicate complaints.
    
    Uses TF-IDF vectorization and cosine similarity to identify complaints
    that are likely about the same issue. Groups similar complaints into
    clusters to track widespread issues.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    # Similarity threshold for considering complaints as duplicates
    SIMILARITY_THRESHOLD = 0.8
    
    # Maximum distance in kilometers for location proximity check
    MAX_LOCATION_DISTANCE_KM = 5.0
    
    def __init__(self):
        """Initialize the Duplicate Detection Service."""
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        logger.info("Duplicate Detection Service initialized")
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two text strings using TF-IDF.
        
        This method vectorizes both texts using TF-IDF and computes the
        cosine similarity between the resulting vectors.
        
        Args:
            text1: First complaint text
            text2: Second complaint text
            
        Returns:
            Similarity score between 0.0 and 1.0
            - 0.0: Completely different
            - 1.0: Identical
            
        Requirements: 6.1, 6.2
        """
        if not text1 or not text2:
            logger.warning("Empty text provided for similarity calculation")
            return 0.0
        
        try:
            # Vectorize both texts
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            logger.debug(f"Text similarity calculated: {similarity:.3f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    def calculate_distance_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two geographic coordinates using Haversine formula.
        
        Args:
            lat1: Latitude of first location
            lon1: Longitude of first location
            lat2: Latitude of second location
            lon2: Longitude of second location
            
        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def find_duplicates(self, complaint: Complaint) -> List[str]:
        """
        Find duplicate complaints for a given complaint.
        
        This method filters unresolved complaints by category and location,
        then calculates text similarity to identify duplicates.
        
        Algorithm:
        1. Filter unresolved complaints by same category
        2. Filter by location proximity (within 5km)
        3. Calculate text similarity
        4. Return complaints with similarity > 0.8
        
        Args:
            complaint: The complaint to check for duplicates
            
        Returns:
            List of complaint IDs that are duplicates
            
        Requirements: 6.1, 6.2, 6.3
        """
        if not complaint or not complaint.description:
            logger.warning("Invalid complaint provided for duplicate detection")
            return []
        
        try:
            # Get unresolved complaints in the same category
            candidate_complaints = Complaint.query.filter(
                Complaint.complaint_id != complaint.complaint_id,
                Complaint.category == complaint.category,
                Complaint.status.in_([
                    complaint.status.__class__.SUBMITTED,
                    complaint.status.__class__.ASSIGNED,
                    complaint.status.__class__.IN_PROGRESS
                ])
            ).all()
            
            logger.info(f"Found {len(candidate_complaints)} candidate complaints for duplicate detection")
            
            duplicates = []
            
            for candidate in candidate_complaints:
                # Check location proximity if both have locations
                if complaint.location and candidate.location:
                    distance = self.calculate_distance_km(
                        complaint.location.latitude,
                        complaint.location.longitude,
                        candidate.location.latitude,
                        candidate.location.longitude
                    )
                    
                    # Skip if too far away
                    if distance > self.MAX_LOCATION_DISTANCE_KM:
                        logger.debug(f"Complaint {candidate.complaint_id} too far: {distance:.2f}km")
                        continue
                
                # Calculate text similarity
                similarity = self.calculate_text_similarity(
                    complaint.description,
                    candidate.description
                )
                
                logger.debug(
                    f"Similarity between {complaint.complaint_id} and "
                    f"{candidate.complaint_id}: {similarity:.3f}"
                )
                
                # If similarity exceeds threshold, mark as duplicate
                if similarity >= self.SIMILARITY_THRESHOLD:
                    duplicates.append(candidate.complaint_id)
                    logger.info(
                        f"Duplicate found: {candidate.complaint_id} "
                        f"(similarity: {similarity:.3f})"
                    )
            
            logger.info(f"Found {len(duplicates)} duplicates for complaint {complaint.complaint_id}")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    def create_cluster(self, complaint_ids: List[str]) -> Optional[str]:
        """
        Create a new duplicate cluster from a list of complaint IDs.
        
        This method creates a cluster, assigns all complaints to it,
        and calculates the centroid location.
        
        Args:
            complaint_ids: List of complaint IDs to group into a cluster
            
        Returns:
            Cluster ID if successful, None otherwise
            
        Requirements: 6.4
        """
        if not complaint_ids or len(complaint_ids) < 2:
            logger.warning("Need at least 2 complaints to create a cluster")
            return None
        
        try:
            # Fetch all complaints
            complaints = Complaint.query.filter(
                Complaint.complaint_id.in_(complaint_ids)
            ).all()
            
            if len(complaints) < 2:
                logger.warning("Could not fetch enough complaints for cluster")
                return None
            
            # Use the first complaint's category
            category = complaints[0].category
            
            # Find the most detailed description (longest)
            representative_description = max(
                [c.description for c in complaints],
                key=len
            )
            
            # Calculate centroid location if complaints have locations
            locations_with_coords = [
                c.location for c in complaints 
                if c.location and c.location.latitude and c.location.longitude
            ]
            
            centroid_lat = None
            centroid_lon = None
            
            if locations_with_coords:
                centroid_lat = sum(loc.latitude for loc in locations_with_coords) / len(locations_with_coords)
                centroid_lon = sum(loc.longitude for loc in locations_with_coords) / len(locations_with_coords)
            
            # Create the cluster
            cluster = DuplicateCluster(
                category=category,
                representative_description=representative_description,
                location_latitude=centroid_lat,
                location_longitude=centroid_lon
            )
            
            db.session.add(cluster)
            db.session.flush()  # Get the cluster_id
            
            # Assign all complaints to the cluster
            for complaint in complaints:
                complaint.cluster_id = cluster.cluster_id
            
            db.session.commit()
            
            logger.info(
                f"Created cluster {cluster.cluster_id} with "
                f"{len(complaints)} complaints"
            )
            
            return cluster.cluster_id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating cluster: {e}")
            return None
    
    def get_cluster_size(self, complaint_id: str) -> int:
        """
        Get the number of complaints in the cluster containing the given complaint.
        
        Args:
            complaint_id: ID of the complaint
            
        Returns:
            Number of complaints in the cluster, or 1 if not in a cluster
            
        Requirements: 6.5
        """
        try:
            complaint = Complaint.query.get(complaint_id)
            
            if not complaint or not complaint.cluster_id:
                return 1
            
            # Count complaints in the same cluster
            count = Complaint.query.filter_by(
                cluster_id=complaint.cluster_id
            ).count()
            
            logger.debug(f"Cluster size for complaint {complaint_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error getting cluster size: {e}")
            return 1
    
    def update_cluster_impact_scores(self, cluster_id: str) -> bool:
        """
        Update impact scores for all complaints in a cluster.
        
        This method increases the impact score based on the number of
        duplicates in the cluster (up to 20 points).
        
        Args:
            cluster_id: ID of the cluster
            
        Returns:
            True if successful, False otherwise
            
        Requirements: 6.4
        """
        try:
            # Get all complaints in the cluster
            complaints = Complaint.query.filter_by(
                cluster_id=cluster_id
            ).all()
            
            if not complaints:
                logger.warning(f"No complaints found in cluster {cluster_id}")
                return False
            
            cluster_size = len(complaints)
            
            # Calculate duplicate score (2 points per duplicate, max 20)
            # cluster_size - 1 because we don't count the complaint itself
            duplicate_score = min((cluster_size - 1) * 2, 20)
            
            logger.info(
                f"Updating impact scores for cluster {cluster_id}: "
                f"{cluster_size} complaints, +{duplicate_score} points"
            )
            
            # Update each complaint's impact score
            for complaint in complaints:
                # Add duplicate score to existing impact score
                complaint.impact_score = min(complaint.impact_score + duplicate_score, 100)
                
                # Update priority level based on new impact score
                if complaint.impact_score >= 76:
                    complaint.priority_level = PriorityLevel.CRITICAL
                elif complaint.impact_score >= 51:
                    complaint.priority_level = PriorityLevel.HIGH
                elif complaint.impact_score >= 26:
                    complaint.priority_level = PriorityLevel.MEDIUM
                else:
                    complaint.priority_level = PriorityLevel.LOW
            
            db.session.commit()
            
            logger.info(f"Successfully updated impact scores for cluster {cluster_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating cluster impact scores: {e}")
            return False


# Singleton instance
_duplicate_detection_service = None


def get_duplicate_detection_service() -> DuplicateDetectionService:
    """
    Get or create the singleton Duplicate Detection Service instance.
    
    Returns:
        DuplicateDetectionService instance
    """
    global _duplicate_detection_service
    if _duplicate_detection_service is None:
        _duplicate_detection_service = DuplicateDetectionService()
    return _duplicate_detection_service
