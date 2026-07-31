"""
Feedback model for citizen feedback on complaint resolution.
"""
from models import db
from datetime import datetime
import uuid


class Feedback(db.Model):
    """
    Feedback model for collecting citizen satisfaction ratings.
    
    Requirements: 13.1, 14.4
    """
    __tablename__ = 'feedbacks'
    
    # Primary key
    feedback_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.complaint_id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False, index=True)
    
    # Feedback details
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comments = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Feedback {self.feedback_id} - Rating: {self.rating}>'
    
    def to_dict(self):
        """Convert feedback to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.isoformat()
        }
