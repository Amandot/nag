"""
Database models for the Grievance Prioritization System.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models
from models.user import User
from models.complaint import Complaint, Location, Category, PriorityLevel, Status
from models.officer import Officer, Department
from models.feedback import Feedback
from models.duplicate_cluster import DuplicateCluster
from models.status_history import StatusHistory

__all__ = [
    'db',
    'User',
    'Complaint',
    'Location',
    'Category',
    'PriorityLevel',
    'Status',
    'Officer',
    'Department',
    'Feedback',
    'DuplicateCluster',
    'StatusHistory'
]
