"""
DuplicateCluster model for grouping similar complaints.
"""
from models import db
from models.complaint import Category
from datetime import datetime
import uuid
import json


class DuplicateCluster(db.Model):
    """
    DuplicateCluster model for grouping similar complaints about the same issue.
    
    Requirements: 13.1, 14.4
    """
    __tablename__ = 'duplicate_clusters'
    
    # Primary key
    cluster_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cluster details
    category = db.Column(db.Enum(Category), nullable=False, index=True)
    representative_description = db.Column(db.Text, nullable=False)
    
    # Location information (centroid of cluster)
    location_latitude = db.Column(db.Float, nullable=True)
    location_longitude = db.Column(db.Float, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaints = db.relationship('Complaint', backref='cluster', lazy='dynamic')
    
    def __repr__(self):
        return f'<DuplicateCluster {self.cluster_id} - {self.category.value}>'
    
    def to_dict(self):
        """Convert duplicate cluster to dictionary."""
        complaint_ids = [c.complaint_id for c in self.complaints]
        return {
            'cluster_id': self.cluster_id,
            'complaint_ids': complaint_ids,
            'category': self.category.value,
            'representative_description': self.representative_description,
            'location': {
                'latitude': self.location_latitude,
                'longitude': self.location_longitude
            } if self.location_latitude and self.location_longitude else None,
            'created_at': self.created_at.isoformat(),
            'complaint_count': len(complaint_ids)
        }
