"""
Complaint model and related enums for grievance management.
"""
from models import db
from datetime import datetime
import uuid
import enum
import json


class Category(enum.Enum):
    """Complaint categories mapping to government departments."""
    WATER_SUPPLY = "Water Supply"
    ELECTRICITY = "Electricity"
    ROADS_INFRASTRUCTURE = "Roads & Infrastructure"
    HEALTHCARE = "Healthcare"
    PUBLIC_SAFETY = "Public Safety"
    SANITATION = "Sanitation"
    OTHER = "Other"


class PriorityLevel(enum.Enum):
    """Priority levels for complaints."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Status(enum.Enum):
    """Complaint status values."""
    SUBMITTED = "Submitted"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"


class Location(db.Model):
    """
    Location model for storing geographic information.
    """
    __tablename__ = 'locations'
    
    location_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500), nullable=True)
    nearby_sensitive_locations = db.Column(db.Text, nullable=True)  # JSON array stored as text
    
    # Relationship
    complaints = db.relationship('Complaint', backref='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<Location ({self.latitude}, {self.longitude})>'
    
    def to_dict(self):
        """Convert location to dictionary."""
        return {
            'location_id': self.location_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'nearby_sensitive_locations': json.loads(self.nearby_sensitive_locations) if self.nearby_sensitive_locations else []
        }
    
    def set_nearby_sensitive_locations(self, locations_list):
        """Set nearby sensitive locations from a list."""
        self.nearby_sensitive_locations = json.dumps(locations_list)
    
    def get_nearby_sensitive_locations(self):
        """Get nearby sensitive locations as a list."""
        return json.loads(self.nearby_sensitive_locations) if self.nearby_sensitive_locations else []


class Complaint(db.Model):
    """
    Complaint model representing citizen grievances.
    
    Requirements: 2.1, 14.2
    """
    __tablename__ = 'complaints'
    
    # Primary key
    complaint_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False, index=True)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.location_id'), nullable=True)
    assigned_officer_id = db.Column(db.String(36), db.ForeignKey('officers.officer_id'), nullable=True)
    cluster_id = db.Column(db.String(36), db.ForeignKey('duplicate_clusters.cluster_id'), nullable=True)
    
    # Complaint details
    category = db.Column(db.Enum(Category), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # JSON array stored as text
    severity_terms = db.Column(db.Text, nullable=True)  # JSON array stored as text
    media_urls = db.Column(db.Text, nullable=True)  # JSON array stored as text
    
    # Priority and scoring
    priority_level = db.Column(db.Enum(PriorityLevel), nullable=False, default=PriorityLevel.LOW, index=True)
    impact_score = db.Column(db.Integer, default=0, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    
    # Image Analysis (CNN)
    image_category = db.Column(db.String(100), nullable=True)
    image_issue = db.Column(db.String(100), nullable=True)
    image_severity = db.Column(db.String(50), nullable=True)
    image_severity_score = db.Column(db.Integer, nullable=True)
    image_confidence = db.Column(db.Float, nullable=True)
    final_priority_score = db.Column(db.Integer, nullable=True)

    
    # Status tracking
    status = db.Column(db.Enum(Status), nullable=False, default=Status.SUBMITTED, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    feedbacks = db.relationship('Feedback', backref='complaint', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Complaint {self.complaint_id} - {self.category.value} - {self.priority_level.value}>'
    
    def to_dict(self):
        """Convert complaint to dictionary."""
        return {
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'category': self.category.value,
            'description': self.description,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'severity_terms': json.loads(self.severity_terms) if self.severity_terms else [],
            'location': self.location.to_dict() if self.location else None,
            'media_urls': json.loads(self.media_urls) if self.media_urls else [],
            'priority_level': self.priority_level.value,
            'impact_score': self.impact_score,
            'explanation': self.explanation,
            'image_analysis': {
                'category': self.image_category,
                'issue': self.image_issue,
                'severity': self.image_severity,
                'severity_score': self.image_severity_score,
                'confidence': self.image_confidence
            } if self.image_category or self.image_issue else None,
            'final_priority_score': self.final_priority_score,
            'status': self.status.value,
            'assigned_officer_id': self.assigned_officer_id,
            'cluster_id': self.cluster_id,
            'created_at': self.created_at.isoformat(),
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'sla_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None
        }
    
    def set_keywords(self, keywords_list):
        """Set keywords from a list."""
        self.keywords = json.dumps(keywords_list)
    
    def get_keywords(self):
        """Get keywords as a list."""
        return json.loads(self.keywords) if self.keywords else []
    
    def set_severity_terms(self, terms_list):
        """Set severity terms from a list."""
        self.severity_terms = json.dumps(terms_list)
    
    def get_severity_terms(self):
        """Get severity terms as a list."""
        return json.loads(self.severity_terms) if self.severity_terms else []
    
    def set_media_urls(self, urls_list):
        """Set media URLs from a list."""
        self.media_urls = json.dumps(urls_list)
    
    def get_media_urls(self):
        """Get media URLs as a list."""
        return json.loads(self.media_urls) if self.media_urls else []
