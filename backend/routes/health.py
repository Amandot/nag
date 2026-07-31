"""
Health check endpoints for monitoring and deployment.
"""
from flask import Blueprint, jsonify
from models import db
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'NagrikSathi Grievance System'
    }), 200

@health_bp.route('/health/db', methods=['GET'])
def database_health():
    """Check database connection."""
    try:
        # Try to execute a simple query
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@health_bp.route('/health/ml', methods=['GET'])
def ml_models_health():
    """Check if ML models are loaded."""
    from config import Config
    
    classifier_exists = os.path.exists(Config.ML_MODEL_PATH)
    vectorizer_exists = os.path.exists(Config.VECTORIZER_PATH)
    
    if classifier_exists and vectorizer_exists:
        return jsonify({
            'status': 'healthy',
            'ml_models': 'loaded',
            'classifier': 'available',
            'vectorizer': 'available'
        }), 200
    else:
        return jsonify({
            'status': 'degraded',
            'ml_models': 'not loaded',
            'classifier': 'available' if classifier_exists else 'missing',
            'vectorizer': 'available' if vectorizer_exists else 'missing'
        }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Kubernetes-style readiness probe."""
    try:
        # Check database
        db.session.execute('SELECT 1')
        
        # Check ML models
        from config import Config
        models_ready = (os.path.exists(Config.ML_MODEL_PATH) and 
                       os.path.exists(Config.VECTORIZER_PATH))
        
        if models_ready:
            return jsonify({'status': 'ready'}), 200
        else:
            return jsonify({'status': 'not ready', 'reason': 'ML models not loaded'}), 503
            
    except Exception as e:
        return jsonify({'status': 'not ready', 'reason': str(e)}), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Kubernetes-style liveness probe."""
    return jsonify({'status': 'alive'}), 200
