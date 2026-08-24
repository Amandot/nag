"""
Configuration settings for the Grievance Prioritization System.
"""
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(BACKEND_DIR / '.env')

class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///grievance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = str(BACKEND_DIR / 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}
    
    # External API keys
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY', '')
    
    # Notification settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@grievance.gov')
    
    # ML Model settings
    ML_MODEL_PATH = str(BACKEND_DIR / 'ml_models' / 'classifier.pkl')
    VECTORIZER_PATH = str(BACKEND_DIR / 'ml_models' / 'vectorizer.pkl')
    
    # Priority scoring settings
    SEVERITY_TERMS = [
        'fire', 'electric shock', 'accident', 'flooding', 
        'leakage', 'collapse', 'injury', 'death', 'explosion',
        'gas leak', 'electrocution', 'drowning'
    ]
    
    # SLA deadlines (in hours)
    SLA_DEADLINES = {
        'CRITICAL': 4,
        'HIGH': 24,
        'MEDIUM': 72,
        'LOW': 168
    }
    
    # Duplicate detection settings
    SIMILARITY_THRESHOLD = 0.8
    LOCATION_RADIUS_KM = 5
    
    # Sensitive locations
    SENSITIVE_LOCATIONS = ['hospital', 'school', 'highway', 'airport', 'railway station']
    
    # SSL/TLS settings (Requirements: 15.2)
    SSL_CERT_FILE = os.environ.get('SSL_CERT_FILE', '')
    SSL_KEY_FILE = os.environ.get('SSL_KEY_FILE', '')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/grievance'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Inherit ML model paths from parent Config class
