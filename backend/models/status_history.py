"""
Status history model for tracking complaint status transitions.

Requirements: 9.3
"""
from models import db
from datetime import datetime
import uuid


class StatusHistory(db.Model):
    """
    Status history model for tracking complaint status changes.
    
    Requirements: 9.3
    """
    __tablename__ = 'status_history'
    
    # Primary key
    history_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.complaint_id'), nullable=False, index=True)
    
    # Status transition details
    old_status = db.Column(db.String(50), nullable=True)  # Null for initial submission
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(db.String(36), nullable=True)  # User ID who made the change
    notes = db.Column(db.Text, nullable=True)  # Optional notes about the change
    
    # Timestamp
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<StatusHistory {self.complaint_id}: {self.old_status} -> {self.new_status}>'
    
    def to_dict(self):
        """Convert status history to dictionary."""
        return {
            'history_id': self.history_id,
            'complaint_id': self.complaint_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'notes': self.notes,
            'changed_at': self.changed_at.isoformat()
        }
