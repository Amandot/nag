"""
HTTPS configuration utilities for enforcing secure connections.

Requirements: 15.2
"""
from flask import request, redirect
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def force_https(app):
    """
    Configure Flask app to enforce HTTPS for all requests.
    
    This middleware redirects all HTTP requests to HTTPS in production.
    In development mode, HTTPS enforcement is disabled.
    
    Requirements: 15.2
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def redirect_to_https():
        """Redirect HTTP requests to HTTPS."""
        # Skip HTTPS enforcement in development and testing
        if app.config.get('DEBUG') or app.config.get('TESTING'):
            return None
        
        # Check if request is already HTTPS
        if request.is_secure:
            return None
        
        # Check for proxy headers (common in production behind load balancers)
        if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
            return None
        
        # Redirect to HTTPS
        url = request.url.replace('http://', 'https://', 1)
        logger.info(f"Redirecting HTTP request to HTTPS: {request.url} -> {url}")
        return redirect(url, code=301)


def require_https(f):
    """
    Decorator to enforce HTTPS for specific routes.
    
    Use this decorator on sensitive routes that must always use HTTPS,
    even in development mode.
    
    Requirements: 15.2
    
    Example:
        @app.route('/api/auth/login', methods=['POST'])
        @require_https
        def login():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip in testing mode
        from flask import current_app
        if current_app.config.get('TESTING'):
            return f(*args, **kwargs)
        
        # Check if request is HTTPS
        if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            logger.warning(f"Non-HTTPS request blocked for sensitive endpoint: {request.url}")
            return {'error': 'HTTPS required for this endpoint'}, 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def configure_ssl_context(app, cert_file=None, key_file=None):
    """
    Configure SSL/TLS certificates for the Flask application.
    
    This function sets up SSL context for running the Flask app with HTTPS.
    In production, certificates should be provided via environment variables
    or configuration files.
    
    Requirements: 15.2
    
    Args:
        app: Flask application instance
        cert_file: Path to SSL certificate file (optional)
        key_file: Path to SSL private key file (optional)
    
    Returns:
        SSL context tuple (cert_file, key_file) or None
    """
    import os
    
    # Get certificate paths from config or parameters
    cert_path = cert_file or app.config.get('SSL_CERT_FILE') or os.environ.get('SSL_CERT_FILE')
    key_path = key_file or app.config.get('SSL_KEY_FILE') or os.environ.get('SSL_KEY_FILE')
    
    # If both certificate and key are provided, return SSL context
    if cert_path and key_path:
        if os.path.exists(cert_path) and os.path.exists(key_path):
            logger.info(f"SSL/TLS configured with cert: {cert_path}")
            return (cert_path, key_path)
        else:
            logger.warning(f"SSL certificate or key file not found: {cert_path}, {key_path}")
            return None
    
    # In development, SSL is optional
    if app.config.get('DEBUG'):
        logger.info("Running in development mode without SSL/TLS")
        return None
    
    # In production, warn if SSL is not configured
    logger.warning("SSL/TLS not configured. Set SSL_CERT_FILE and SSL_KEY_FILE environment variables.")
    return None


def add_security_headers(app):
    """
    Add security headers to all responses.
    
    Implements security best practices by adding headers that protect
    against common web vulnerabilities.
    
    Requirements: 15.2
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def set_security_headers(response):
        """Add security headers to response."""
        # Enforce HTTPS (HSTS)
        if not app.config.get('DEBUG'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
