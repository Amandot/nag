"""
Officer model and Department enum for complaint routing.
"""
from models import db
from datetime import datetime
import uuid
import enum


class Department(enum.Enum):
    """Government departments responsible for complaint resolution."""
    WATER_DEPT = "Water Department"
    ELECTRICITY_DEPT = "Electricity Department"
    ROADS_DEPT = "Roads & Infrastructure Department"
    HEALTH_DEPT = "Healthcare Department"
    SAFETY_DEPT = "Public Safety Department"
    SANITATION_DEPT = "Sanitation Department"


class Officer(db.Model):
    """
    Officer model representing field officers assigned to resolve complaints.
    
    Requirements: 8.1, 14.3
    """
    __tablename__ = 'officers'
    
    # Primary key
    officer_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Officer information
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.Enum(Department), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # Location information
    location_latitude = db.Column(db.Float, nullable=True)
    location_longitude = db.Column(db.Float, nullable=True)
    location_address = db.Column(db.String(500), nullable=True)
    
    # Workload tracking
    assigned_cases = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaints = db.relationship('Complaint', backref='assigned_officer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Officer {self.name} - {self.department.value}>'
    
    def to_dict(self):
        """Convert officer to dictionary."""
        return {
            'officer_id': self.officer_id,
            'name': self.name,
            'department': self.department.value,
            'phone': self.phone,
            'email': self.email,
            'location': {
                'latitude': self.location_latitude,
                'longitude': self.location_longitude,
                'address': self.location_address
            } if self.location_latitude and self.location_longitude else None,
            'assigned_cases': self.assigned_cases,
            'created_at': self.created_at.isoformat()
        }
