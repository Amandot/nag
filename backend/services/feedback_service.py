"""
Feedback service for collecting and processing citizen feedback.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""
from models import db
from models.feedback import Feedback
from models.user import User
from models.complaint import Complaint, Status
import logging

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Service for managing feedback submission and processing.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    
    def submit_feedback(self, complaint_id, user_id, rating, comments=None):
        """
        Submit feedback for a resolved complaint.
        
        Requirements: 13.1, 13.2
        
        Args:
            complaint_id: ID of the complaint
            user_id: ID of the user submitting feedback
            rating: Rating from 1-5
            comments: Optional feedback comments
            
        Returns:
            tuple: (feedback object, error message)
        """
        try:
            # Validate rating
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return None, "Rating must be an integer between 1 and 5"
            
            # Verify complaint exists
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                return None, "Complaint not found"
            
            # Verify user owns this complaint
            if complaint.user_id != user_id:
                return None, "Access denied: You can only provide feedback for your own complaints"
            
            # Verify complaint is resolved
            if complaint.status != Status.RESOLVED:
                return None, "Feedback can only be submitted for resolved complaints"
            
            # Check if feedback already exists for this complaint
            existing_feedback = Feedback.query.filter_by(
                complaint_id=complaint_id,
                user_id=user_id
            ).first()
            
            if existing_feedback:
                return None, "Feedback has already been submitted for this complaint"
            
            # Create feedback
            feedback = Feedback(
                complaint_id=complaint_id,
                user_id=user_id,
                rating=rating,
                comments=comments
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            logger.info(
                f"Feedback submitted for complaint {complaint_id} by user {user_id}: "
                f"rating={rating}"
            )
            
            return feedback, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting feedback: {e}", exc_info=True)
            return None, "Failed to submit feedback"
    
    def update_trust_score(self, user_id, feedback):
        """
        Update user trust score based on feedback.
        
        Trust score update rules:
        - Positive feedback (rating >= 4): +2 points
        - Neutral feedback (rating = 3): +1 point
        - Negative feedback (rating < 3): -1 point
        - Range: 0-100
        
        Requirements: 13.3, 13.5
        
        Args:
            user_id: ID of the user
            feedback: Feedback object
            
        Returns:
            tuple: (updated trust score, error message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            old_trust_score = user.trust_score
            
            # Calculate trust score adjustment based on rating
            if feedback.rating >= 4:
                adjustment = 2
            elif feedback.rating == 3:
                adjustment = 1
            else:
                adjustment = -1
            
            # Update trust score (ensure it stays within 0-100 range)
            new_trust_score = max(0, min(100, user.trust_score + adjustment))
            user.trust_score = new_trust_score
            
            db.session.commit()
            
            logger.info(
                f"Trust score updated for user {user_id}: "
                f"{old_trust_score} -> {new_trust_score} (adjustment: {adjustment})"
            )
            
            return new_trust_score, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating trust score: {e}", exc_info=True)
            return None, "Failed to update trust score"
    
    def flag_dissatisfaction(self, complaint_id, feedback):
        """
        Flag complaints with low satisfaction ratings for review.
        
        Requirements: 13.3, 13.5
        
        Args:
            complaint_id: ID of the complaint
            feedback: Feedback object
            
        Returns:
            bool: True if flagged, False otherwise
        """
        try:
            # Flag if rating is below 3
            if feedback.rating < 3:
                logger.warning(
                    f"Dissatisfaction flagged for complaint {complaint_id}: "
                    f"rating={feedback.rating}, comments={feedback.comments}"
                )
                
                # In a production system, this would:
                # - Create a review ticket
                # - Notify supervisors
                # - Add to admin dashboard alerts
                # For now, we just log it
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error flagging dissatisfaction: {e}", exc_info=True)
            return False
    
    def collect_training_data(self):
        """
        Export feedback data for ML model retraining.
        
        Collects all feedback with associated complaint data for use in
        improving the ML classifier and priority prediction models.
        
        Requirements: 13.4
        
        Returns:
            list: List of dictionaries containing complaint and feedback data
        """
        try:
            # Query all feedback with associated complaints
            feedbacks = db.session.query(Feedback, Complaint).join(
                Complaint,
                Feedback.complaint_id == Complaint.complaint_id
            ).all()
            
            training_data = []
            
            for feedback, complaint in feedbacks:
                data_point = {
                    'complaint_id': complaint.complaint_id,
                    'description': complaint.description,
                    'category': complaint.category.value,
                    'keywords': complaint.get_keywords(),
                    'severity_terms': complaint.get_severity_terms(),
                    'priority_level': complaint.priority_level.value,
                    'impact_score': complaint.impact_score,
                    'rating': feedback.rating,
                    'comments': feedback.comments,
                    'resolution_time_hours': None
                }
                
                # Calculate resolution time if available
                if complaint.resolved_at and complaint.assigned_at:
                    resolution_time = complaint.resolved_at - complaint.assigned_at
                    data_point['resolution_time_hours'] = resolution_time.total_seconds() / 3600
                elif complaint.resolved_at and complaint.created_at:
                    resolution_time = complaint.resolved_at - complaint.created_at
                    data_point['resolution_time_hours'] = resolution_time.total_seconds() / 3600
                
                training_data.append(data_point)
            
            logger.info(f"Collected {len(training_data)} training data points from feedback")
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}", exc_info=True)
            return []


# Singleton instance
_feedback_service = None


def get_feedback_service():
    """Get the singleton feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
