"""
Monitoring and Escalation Service for the Grievance Prioritization System.
Handles SLA deadline calculation, violation checking, and complaint escalation.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from flask import current_app

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring complaint resolution times and handling escalations."""
    
    def __init__(self, app=None):
        """Initialize monitoring service with optional Flask app."""
        self.sla_deadlines = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app configuration."""
        # Load SLA deadlines from config
        self.sla_deadlines = app.config.get('SLA_DEADLINES', {
            'CRITICAL': 4,
            'HIGH': 24,
            'MEDIUM': 72,
            'LOW': 168
        })
        logger.info(f"Monitoring service initialized with SLA deadlines: {self.sla_deadlines}")
    
    def calculate_sla_deadline(self, priority_level: str, assigned_time: datetime) -> datetime:
        """
        Calculate SLA deadline based on priority level and assignment time.
        
        Requirements: 10.1
        
        Args:
            priority_level: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            assigned_time: Time when complaint was assigned to an officer
            
        Returns:
            Deadline datetime for complaint resolution
        """
        # Get SLA hours for this priority level
        sla_hours = self.sla_deadlines.get(priority_level.upper(), 168)  # Default to LOW (7 days)
        
        # Calculate deadline
        deadline = assigned_time + timedelta(hours=sla_hours)
        
        logger.info(
            f"SLA deadline calculated for priority {priority_level}: "
            f"{sla_hours} hours from {assigned_time} = {deadline}"
        )
        
        return deadline
    
    def get_sla_hours(self, priority_level: str) -> int:
        """
        Get SLA hours for a given priority level.
        
        Args:
            priority_level: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            
        Returns:
            Number of hours for SLA deadline
        """
        return self.sla_deadlines.get(priority_level.upper(), 168)
    
    def get_resolution_time(self, complaint) -> Optional[timedelta]:
        """
        Calculate resolution time for a resolved complaint.
        
        Requirements: 10.5
        
        Args:
            complaint: Complaint object
            
        Returns:
            Time taken to resolve the complaint, or None if not resolved
        """
        if not complaint.resolved_at:
            return None
        
        # Calculate time from assignment to resolution
        if complaint.assigned_at:
            resolution_time = complaint.resolved_at - complaint.assigned_at
        else:
            # If never assigned, calculate from creation time
            resolution_time = complaint.resolved_at - complaint.created_at
        
        logger.info(
            f"Resolution time for complaint {complaint.complaint_id}: {resolution_time}"
        )
        
        return resolution_time
    
    def check_sla_violations(self) -> Dict[str, List[Any]]:
        """
        Check all assigned complaints for SLA violations.
        
        Identifies complaints that:
        - Have exceeded 75% of their SLA deadline (warning threshold)
        - Have exceeded 100% of their SLA deadline (escalation threshold)
        
        Requirements: 10.2, 10.3, 10.4
        
        Returns:
            Dictionary with 'warnings' and 'violations' lists containing complaint objects
        """
        from models.complaint import Complaint, Status
        
        current_time = datetime.utcnow()
        
        # Query all assigned or in-progress complaints with SLA deadlines
        active_complaints = Complaint.query.filter(
            Complaint.status.in_([Status.ASSIGNED, Status.IN_PROGRESS]),
            Complaint.sla_deadline.isnot(None)
        ).all()
        
        warnings = []
        violations = []
        
        for complaint in active_complaints:
            if not complaint.assigned_at or not complaint.sla_deadline:
                continue
            
            # Calculate time elapsed and total SLA time
            time_elapsed = current_time - complaint.assigned_at
            total_sla_time = complaint.sla_deadline - complaint.assigned_at
            
            # Calculate percentage of SLA time used
            if total_sla_time.total_seconds() > 0:
                percentage_used = (time_elapsed.total_seconds() / total_sla_time.total_seconds()) * 100
            else:
                percentage_used = 100
            
            # Check for violations (100% exceeded)
            if current_time >= complaint.sla_deadline:
                violations.append(complaint)
                logger.warning(
                    f"SLA VIOLATION: Complaint {complaint.complaint_id} "
                    f"exceeded deadline {complaint.sla_deadline} "
                    f"(Priority: {complaint.priority_level.value})"
                )
            # Check for warnings (75% exceeded)
            elif percentage_used >= 75:
                warnings.append(complaint)
                logger.info(
                    f"SLA WARNING: Complaint {complaint.complaint_id} "
                    f"at {percentage_used:.1f}% of SLA deadline "
                    f"(Priority: {complaint.priority_level.value})"
                )
        
        logger.info(
            f"SLA check complete: {len(warnings)} warnings, {len(violations)} violations "
            f"out of {len(active_complaints)} active complaints"
        )
        
        return {
            'warnings': warnings,
            'violations': violations
        }
    
    def send_sla_warning(self, complaint) -> bool:
        """
        Send warning notification to assigned officer about approaching SLA deadline.
        
        Requirements: 10.2
        
        Args:
            complaint: Complaint object approaching SLA deadline
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        from models.officer import Officer
        from services.notification_service import notification_service
        
        try:
            # Get assigned officer
            if not complaint.assigned_officer_id:
                logger.warning(
                    f"Cannot send SLA warning for complaint {complaint.complaint_id}: "
                    f"no officer assigned"
                )
                return False
            
            officer = Officer.query.get(complaint.assigned_officer_id)
            if not officer:
                logger.error(
                    f"Cannot send SLA warning for complaint {complaint.complaint_id}: "
                    f"officer {complaint.assigned_officer_id} not found"
                )
                return False
            
            # Calculate time remaining
            current_time = datetime.utcnow()
            time_remaining = complaint.sla_deadline - current_time
            hours_remaining = time_remaining.total_seconds() / 3600
            
            # Create warning message
            message = (
                f"SLA WARNING: Complaint #{complaint.complaint_id} "
                f"(Priority: {complaint.priority_level.value}) "
                f"has {hours_remaining:.1f} hours remaining until SLA deadline. "
                f"Please prioritize resolution."
            )
            
            # Send notifications
            sms_sent = notification_service.send_sms(officer.phone, message)
            email_sent = notification_service.send_email(
                officer.email,
                f"SLA Warning: Complaint #{complaint.complaint_id}",
                message
            )
            
            if sms_sent or email_sent:
                logger.info(
                    f"SLA warning sent to officer {officer.name} for complaint "
                    f"{complaint.complaint_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to send SLA warning for complaint {complaint.complaint_id}"
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Error sending SLA warning for complaint {complaint.complaint_id}: {e}",
                exc_info=True
            )
            return False
    
    def escalate_complaint(self, complaint) -> bool:
        """
        Escalate a complaint that has exceeded its SLA deadline.
        
        Updates complaint status to ESCALATED and sends notifications to
        senior authorities.
        
        Requirements: 10.3, 10.4, 11.4
        
        Args:
            complaint: Complaint object that exceeded SLA deadline
            
        Returns:
            True if escalation successful, False otherwise
        """
        from models import db
        from models.complaint import Status
        from models.status_history import StatusHistory
        from services.notification_service import notification_service
        
        try:
            # Store old status
            old_status = complaint.status.value
            
            # Update complaint status to ESCALATED
            complaint.status = Status.ESCALATED
            
            # Record status change in history
            status_history = StatusHistory(
                complaint_id=complaint.complaint_id,
                old_status=old_status,
                new_status=Status.ESCALATED.value,
                changed_by='system',  # System-initiated escalation
                notes=f"Automatically escalated due to SLA violation. Deadline was {complaint.sla_deadline}"
            )
            db.session.add(status_history)
            db.session.commit()
            
            logger.info(
                f"Complaint {complaint.complaint_id} escalated due to SLA violation "
                f"(deadline: {complaint.sla_deadline})"
            )
            
            # Send escalation notifications
            # For now, send to assigned officer and system admin
            # In production, this would send to senior authorities/supervisors
            try:
                from models.officer import Officer
                
                # Notify assigned officer
                if complaint.assigned_officer_id:
                    officer = Officer.query.get(complaint.assigned_officer_id)
                    if officer:
                        notification_service.notify_escalation(
                            authority_phone=officer.phone,
                            authority_email=officer.email,
                            complaint_id=complaint.complaint_id,
                            priority=complaint.priority_level.value,
                            reason="SLA deadline exceeded",
                            sla_deadline=complaint.sla_deadline.isoformat()
                        )
                
                # TODO: In production, also notify senior authorities/supervisors
                # This would require a separate authorities table or officer hierarchy
                
                logger.info(
                    f"Escalation notifications sent for complaint {complaint.complaint_id}"
                )
            except Exception as e:
                # Don't fail escalation if notification fails
                logger.error(
                    f"Failed to send escalation notifications for complaint "
                    f"{complaint.complaint_id}: {e}",
                    exc_info=True
                )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to escalate complaint {complaint.complaint_id}: {e}",
                exc_info=True
            )
            return False
    
    def process_sla_violations(self) -> Dict[str, int]:
        """
        Process all SLA violations and warnings.
        
        This is the main method that should be called periodically (e.g., every 30 minutes)
        to check for SLA violations and take appropriate action.
        
        Requirements: 10.2, 10.3, 10.4
        
        Returns:
            Dictionary with counts of warnings sent and complaints escalated
        """
        # Check for violations
        results = self.check_sla_violations()
        
        warnings_sent = 0
        escalations_done = 0
        
        # Send warnings for complaints at 75% of SLA
        for complaint in results['warnings']:
            if self.send_sla_warning(complaint):
                warnings_sent += 1
        
        # Escalate complaints that exceeded SLA
        for complaint in results['violations']:
            if self.escalate_complaint(complaint):
                escalations_done += 1
        
        logger.info(
            f"SLA violation processing complete: "
            f"{warnings_sent} warnings sent, {escalations_done} complaints escalated"
        )
        
        return {
            'warnings_sent': warnings_sent,
            'escalations_done': escalations_done,
            'total_warnings': len(results['warnings']),
            'total_violations': len(results['violations'])
        }


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service():
    """Get or create the global monitoring service instance."""
    global _monitoring_service
    
    if _monitoring_service is None:
        from flask import current_app
        _monitoring_service = MonitoringService(current_app)
    
    return _monitoring_service
