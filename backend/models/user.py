"""
User model for authentication and user management.
"""
from models import db
from datetime import datetime
import uuid
import enum


class UserRole(enum.Enum):
    """User roles for authorization."""
    CITIZEN = "citizen"
    OFFICER = "officer"
    ADMIN = "admin"


class User(db.Model):
    """
    User model representing citizens who submit grievances.
    
    Requirements: 1.1, 14.1
    """
    __tablename__ = 'users'
    
    # Primary key
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User information
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # Authentication
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Authorization (Requirements: 15.3)
    role = db.Column(db.Enum(UserRole), default=UserRole.CITIZEN, nullable=False)
    
    # Trust score (0-100, default 50)
    trust_score = db.Column(db.Integer, default=50, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaints = db.relationship('Complaint', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'
    
    def to_dict(self):
        """Convert user to dictionary (excluding password_hash)."""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'role': self.role.value,
            'trust_score': self.trust_score,
            'created_at': self.created_at.isoformat()
        }
