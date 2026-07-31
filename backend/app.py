"""
Main Flask application entry point for the Grievance Prioritization System.
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

def create_app(config_class=Config):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for frontend - configured for Render frontend
    # Allow requests from your React frontend hosted on Render
    frontend_url = os.getenv('FRONTEND_URL', 'https://nagriksathi-frontend.onrender.com')
    CORS(app, resources={
        r"/api/*": {
            "origins": [frontend_url, "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure HTTPS enforcement and security headers
    # Requirements: 15.2
    from utils.https_config import force_https, add_security_headers
    force_https(app)
    add_security_headers(app)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Configure JWT error handlers
    # Requirements: 15.1
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired', 'message': 'Please log in again'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token', 'message': 'Please provide a valid authentication token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization required', 'message': 'Please provide an authentication token'}, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has been revoked', 'message': 'Please log in again'}, 401
    
    # Initialize logging
    setup_logging(app)
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Initialize notification service
    from services.notification_service import notification_service
    with app.app_context():
        notification_service.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.complaints import complaints_bp
    from routes.admin import admin_bp
    from routes.admin_complaints import admin_complaints_bp
    from routes.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(complaints_bp, url_prefix='/api/complaints')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_complaints_bp, url_prefix='/api/admin')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Initialize background scheduler for SLA monitoring
    # Requirements: 10.2, 10.3, 10.4
    if not app.config.get('TESTING', False):
        scheduler = BackgroundScheduler()
        
        # Schedule SLA violation checker to run every 30 minutes
        scheduler.add_job(
            func=lambda: check_sla_violations_job(app),
            trigger=IntervalTrigger(minutes=30),
            id='sla_violation_checker',
            name='Check SLA violations and send notifications',
            replace_existing=True
        )
        
        scheduler.start()
        app.logger.info("Background scheduler started for SLA monitoring")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
    
    return app

def check_sla_violations_job(app):
    """
    Background job to check for SLA violations.
    
    This function runs periodically to check all active complaints
    for SLA violations and take appropriate action.
    
    Requirements: 10.2, 10.3, 10.4
    """
    with app.app_context():
        try:
            from services.monitoring_service import get_monitoring_service
            
            monitoring_service = get_monitoring_service()
            results = monitoring_service.process_sla_violations()
            
            app.logger.info(
                f"SLA violation check completed: "
                f"{results['warnings_sent']}/{results['total_warnings']} warnings sent, "
                f"{results['escalations_done']}/{results['total_violations']} escalations done"
            )
        except Exception as e:
            app.logger.error(f"Error in SLA violation check job: {e}", exc_info=True)

def setup_logging(app):
    """Configure application logging."""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    app.logger.setLevel(logging.INFO)

# Create app instance for Gunicorn (production)
app = create_app()

if __name__ == '__main__':
    # Default port for local development.  React frontend assumes backend
    # is available at http://localhost:5000/api unless REACT_APP_API_URL is
    # overridden, so we default to 5000 here.
    #
    # When running on Hugging Face Spaces the platform requires 7860, so
    # callers should set the PORT environment variable in that case (e.g.
    # `export PORT=7860` or via the container config).  In production we
    # expect a proper WSGI server to set the port as needed.
    port = int(os.getenv('PORT', 5000))
    
    # Determine if we're in development mode
    # Check for FLASK_ENV or default to development for local runs
    is_development = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Configure SSL/TLS if certificates are available (local dev only)
    # Requirements: 15.2
    from utils.https_config import configure_ssl_context
    ssl_context = configure_ssl_context(app)
    
    # Run with or without SSL based on configuration
    # Enable debug mode for local development to disable HTTPS enforcement
    if ssl_context:
        app.run(debug=is_development, host='0.0.0.0', port=port, ssl_context=ssl_context)
    else:
        app.run(debug=is_development, host='0.0.0.0', port=port)
