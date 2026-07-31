"""
Routing Service for complaint assignment to departments and officers.

This module provides functionality to:
- Map complaint categories to appropriate departments
- Find nearest available officers by location
- Balance workload across officers
- Assign complaints to officers

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from models import db, Category, Status
from models.officer import Officer, Department
from models.complaint import Complaint
from models.user import User

logger = logging.getLogger(__name__)


class RoutingService:
    """
    Routing service for assigning complaints to departments and officers.
    
    The service handles:
    - Category-to-department mapping
    - Officer selection based on location and workload
    - Complaint assignment and status updates
    
    Requirements: 8.1, 8.2, 8.3, 8.4
    """
    
    # Category to Department mapping
    CATEGORY_DEPARTMENT_MAP = {
        Category.WATER_SUPPLY: Department.WATER_DEPT,
        Category.ELECTRICITY: Department.ELECTRICITY_DEPT,
        Category.ROADS_INFRASTRUCTURE: Department.ROADS_DEPT,
        Category.HEALTHCARE: Department.HEALTH_DEPT,
        Category.PUBLIC_SAFETY: Department.SAFETY_DEPT,
        Category.SANITATION: Department.SANITATION_DEPT
    }
    
    # Maximum distance for officer assignment (in kilometers)
    MAX_ASSIGNMENT_DISTANCE_KM = 10.0
    
    def __init__(self):
        """Initialize the Routing Service."""
        logger.info("Routing Service initialized")
    
    def map_category_to_department(self, category: Category) -> Department:
        """
        Map a complaint category to the responsible department.
        
        Args:
            category: Complaint category enum
            
        Returns:
            Department enum value
            
        Raises:
            ValueError: If category is not recognized
            
        Requirements: 8.1
        """
        if category not in self.CATEGORY_DEPARTMENT_MAP:
            logger.error(f"Unknown category: {category}")
            raise ValueError(f"Unknown category: {category}")
        
        department = self.CATEGORY_DEPARTMENT_MAP[category]
        logger.debug(f"Mapped category {category.value} to department {department.value}")
        return department

    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Uses the Haversine formula to calculate distance in kilometers.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        
        return c * r
    
    def find_nearest_officer(
        self,
        latitude: float,
        longitude: float,
        department: Department
    ) -> Optional[Officer]:
        """
        Find the nearest available officer in a department.
        
        Searches for officers in the specified department within the maximum
        assignment distance, then selects the one with the lowest workload.
        
        Args:
            latitude: Complaint location latitude
            longitude: Complaint location longitude
            department: Target department
            
        Returns:
            Officer object if found, None otherwise
            
        Requirements: 8.2, 8.3
        """
        # Query all officers in the department
        officers = Officer.query.filter_by(department=department).all()
        
        if not officers:
            logger.warning(f"No officers found in department {department.value}")
            return None
        
        # Filter officers by distance and calculate distances
        nearby_officers = []
        for officer in officers:
            if officer.location_latitude is None or officer.location_longitude is None:
                logger.debug(f"Officer {officer.officer_id} has no location data, skipping")
                continue
            
            distance = self.calculate_distance(
                latitude, longitude,
                officer.location_latitude, officer.location_longitude
            )
            
            if distance <= self.MAX_ASSIGNMENT_DISTANCE_KM:
                nearby_officers.append((officer, distance))
                logger.debug(
                    f"Officer {officer.name} ({officer.officer_id}) is {distance:.2f}km away "
                    f"with {officer.assigned_cases} assigned cases"
                )
        
        if not nearby_officers:
            logger.warning(
                f"No officers found within {self.MAX_ASSIGNMENT_DISTANCE_KM}km "
                f"of location ({latitude}, {longitude})"
            )
            return None
        
        # Balance workload: select officer with lowest assigned_cases
        # If multiple officers have same workload, select the nearest one
        selected_officer = self.balance_workload(nearby_officers)
        
        logger.info(
            f"Selected officer {selected_officer.name} ({selected_officer.officer_id}) "
            f"with {selected_officer.assigned_cases} assigned cases"
        )
        
        return selected_officer
    
    def balance_workload(self, officers_with_distance: List[Tuple[Officer, float]]) -> Officer:
        """
        Select officer with the best balance of workload and proximity.
        
        Prioritizes officers with lower workload. If multiple officers have
        the same workload, selects the nearest one.
        
        Args:
            officers_with_distance: List of (Officer, distance) tuples
            
        Returns:
            Selected Officer object
            
        Requirements: 8.3
        """
        # Sort by assigned_cases (ascending), then by distance (ascending)
        sorted_officers = sorted(
            officers_with_distance,
            key=lambda x: (x[0].assigned_cases, x[1])
        )
        
        selected_officer = sorted_officers[0][0]
        selected_distance = sorted_officers[0][1]
        
        logger.debug(
            f"Workload balancing selected officer {selected_officer.name} "
            f"({selected_distance:.2f}km away, {selected_officer.assigned_cases} cases)"
        )
        
        return selected_officer

    
    def assign_complaint(
        self,
        complaint_id: str,
        officer_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign a complaint to an officer.
        
        Updates the complaint with the assigned officer, changes status to "Assigned",
        records the assignment timestamp, calculates SLA deadline, and increments 
        the officer's workload. Sends notifications to the officer and user.
        
        Args:
            complaint_id: ID of the complaint to assign
            officer_id: ID of the officer to assign to
            
        Returns:
            Tuple of (success, error_message)
            - success: True if assignment succeeded, False otherwise
            - error_message: Error description if failed, None if succeeded
            
        Requirements: 8.4, 10.1, 11.2, 11.3
        """
        try:
            # Fetch complaint
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                error_msg = f"Complaint {complaint_id} not found"
                logger.error(error_msg)
                return False, error_msg
            
            # Fetch officer
            officer = Officer.query.get(officer_id)
            if not officer:
                error_msg = f"Officer {officer_id} not found"
                logger.error(error_msg)
                return False, error_msg
            
            # Fetch user for notifications
            user = User.query.get(complaint.user_id)
            
            # Store old status for notification
            old_status = complaint.status.value
            
            # Update complaint
            complaint.assigned_officer_id = officer_id
            complaint.status = Status.ASSIGNED
            complaint.assigned_at = datetime.utcnow()
            
            # Calculate and store SLA deadline
            # Requirements: 10.1
            from services.monitoring_service import get_monitoring_service
            monitoring_service = get_monitoring_service()
            complaint.sla_deadline = monitoring_service.calculate_sla_deadline(
                complaint.priority_level.value,
                complaint.assigned_at
            )
            
            # Increment officer's workload
            officer.assigned_cases += 1
            
            # Commit changes
            db.session.commit()
            
            logger.info(
                f"Successfully assigned complaint {complaint_id} to officer "
                f"{officer.name} ({officer_id}). Officer now has {officer.assigned_cases} cases."
            )
            
            # Send notifications
            # Requirements: 11.2, 11.3
            try:
                from services.notification_service import notification_service
                
                # Notify officer about assignment
                location_str = complaint.location.address if complaint.location else "Unknown location"
                notification_service.notify_officer_assignment(
                    officer_phone=officer.phone,
                    officer_email=officer.email,
                    complaint_id=complaint.complaint_id,
                    priority=complaint.priority_level.value,
                    location=location_str,
                    category=complaint.category.value
                )
                
                # Notify user about status change
                if user:
                    notification_service.notify_status_change(
                        user_phone=user.phone,
                        user_email=user.email,
                        complaint_id=complaint.complaint_id,
                        old_status=old_status,
                        new_status=complaint.status.value
                    )
                
                logger.info(f"Assignment notifications sent for complaint {complaint_id}")
            except Exception as e:
                # Don't fail the assignment if notification fails
                logger.error(f"Failed to send assignment notifications: {e}", exc_info=True)
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to assign complaint: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def route_complaint(self, complaint_id: str) -> Tuple[bool, Optional[str]]:
        """
        Complete routing workflow for a complaint.
        
        This is the main method that:
        1. Maps the complaint category to a department
        2. Finds the nearest available officer
        3. Assigns the complaint to the officer
        
        Args:
            complaint_id: ID of the complaint to route
            
        Returns:
            Tuple of (success, error_message)
            - success: True if routing succeeded, False otherwise
            - error_message: Error description if failed, None if succeeded
            
        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        try:
            # Fetch complaint
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                error_msg = f"Complaint {complaint_id} not found"
                logger.error(error_msg)
                return False, error_msg
            
            # Check if complaint has location
            if not complaint.location:
                error_msg = f"Complaint {complaint_id} has no location data"
                logger.error(error_msg)
                return False, error_msg
            
            # Map category to department
            try:
                department = self.map_category_to_department(complaint.category)
            except ValueError as e:
                return False, str(e)
            
            # Find nearest officer
            officer = self.find_nearest_officer(
                complaint.location.latitude,
                complaint.location.longitude,
                department
            )
            
            if not officer:
                error_msg = (
                    f"No available officers found in {department.value} "
                    f"for complaint {complaint_id}"
                )
                logger.warning(error_msg)
                return False, error_msg
            
            # Assign complaint to officer
            success, error = self.assign_complaint(complaint_id, officer.officer_id)
            
            if success:
                logger.info(
                    f"Successfully routed complaint {complaint_id} "
                    f"(category: {complaint.category.value}) to officer "
                    f"{officer.name} in {department.value}"
                )
            
            return success, error
            
        except Exception as e:
            error_msg = f"Failed to route complaint: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg


# Singleton instance
_routing_service = None


def get_routing_service() -> RoutingService:
    """
    Get or create the singleton Routing Service instance.
    
    Returns:
        RoutingService instance
    """
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
