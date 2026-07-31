"""
Authorization utilities for role-based access control.

Requirements: 15.3
"""
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from functools import wraps
from models.user import User, UserRole
from models.complaint import Complaint
import logging

logger = logging.getLogger(__name__)


def get_current_user():
    """
    Get the current authenticated user from JWT token.
    
    Requirements: 15.3
    
    Returns:
        User object or None if not authenticated
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def require_role(*allowed_roles):
    """
    Decorator to require specific user roles for accessing an endpoint.
    
    Requirements: 15.3
    
    Args:
        *allowed_roles: Variable number of UserRole enum values
    
    Example:
        @app.route('/api/admin/dashboard')
        @jwt_required()
        @require_role(UserRole.ADMIN)
        def admin_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                logger.warning("Authorization check failed: User not found")
                return jsonify({'error': 'User not found'}), 404
            
            if user.role not in allowed_roles:
                logger.warning(
                    f"Authorization check failed: User {user.user_id} "
                    f"with role {user.role.value} attempted to access endpoint "
                    f"requiring roles: {[r.value for r in allowed_roles]}"
                )
                return jsonify({'error': 'Access denied: Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(f):
    """
    Decorator to require admin role for accessing an endpoint.
    
    Shorthand for @require_role(UserRole.ADMIN)
    
    Requirements: 15.3
    
    Example:
        @app.route('/api/admin/users')
        @jwt_required()
        @require_admin
        def list_users():
            ...
    """
    return require_role(UserRole.ADMIN)(f)


def verify_complaint_ownership(complaint_id, user_id=None, allow_admin=True):
    """
    Verify that a user owns a specific complaint or is an admin.
    
    Requirements: 15.3
    
    Args:
        complaint_id: ID of the complaint to check
        user_id: ID of the user (if None, gets from JWT)
        allow_admin: Whether to allow admin users to access any complaint
    
    Returns:
        Tuple of (is_authorized: bool, complaint: Complaint or None, error_response: dict or None)
    """
    try:
        # Get user if not provided
        if user_id is None:
            user = get_current_user()
            if not user:
                return False, None, ({'error': 'User not found'}, 404)
            user_id = user.user_id
        else:
            user = User.query.get(user_id)
            if not user:
                return False, None, ({'error': 'User not found'}, 404)
        
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, None, ({'error': 'Complaint not found'}, 404)
        
        # Check if user is admin (admins can access all complaints)
        if allow_admin and user.role == UserRole.ADMIN:
            logger.info(f"Admin user {user_id} accessing complaint {complaint_id}")
            return True, complaint, None
        
        # Check if user owns the complaint
        if complaint.user_id == user_id:
            return True, complaint, None
        
        # User doesn't own the complaint and is not admin
        logger.warning(
            f"Authorization failed: User {user_id} attempted to access "
            f"complaint {complaint_id} owned by {complaint.user_id}"
        )
        return False, None, ({'error': 'Access denied: You do not have permission to access this complaint'}, 403)
        
    except Exception as e:
        logger.error(f"Error verifying complaint ownership: {e}", exc_info=True)
        return False, None, ({'error': 'Authorization check failed'}, 500)


def require_complaint_ownership(allow_admin=True):
    """
    Decorator to verify complaint ownership for routes with complaint_id parameter.
    
    Requirements: 15.3
    
    Args:
        allow_admin: Whether to allow admin users to access any complaint
    
    Example:
        @app.route('/api/complaints/<complaint_id>')
        @jwt_required()
        @require_complaint_ownership()
        def get_complaint(complaint_id):
            # complaint_id is verified to belong to current user
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            complaint_id = kwargs.get('complaint_id')
            
            if not complaint_id:
                return jsonify({'error': 'Complaint ID required'}), 400
            
            is_authorized, complaint, error_response = verify_complaint_ownership(
                complaint_id,
                allow_admin=allow_admin
            )
            
            if not is_authorized:
                return jsonify(error_response[0]), error_response[1]
            
            # Add complaint to kwargs for use in the route function
            kwargs['complaint'] = complaint
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def verify_user_data_access(target_user_id, allow_admin=True):
    """
    Verify that a user can access another user's data.
    
    Users can only access their own data unless they are admins.
    
    Requirements: 15.3
    
    Args:
        target_user_id: ID of the user whose data is being accessed
        allow_admin: Whether to allow admin users to access any user's data
    
    Returns:
        Tuple of (is_authorized: bool, error_response: dict or None)
    """
    try:
        current_user = get_current_user()
        
        if not current_user:
            return False, ({'error': 'User not found'}, 404)
        
        # Check if user is admin (admins can access all user data)
        if allow_admin and current_user.role == UserRole.ADMIN:
            logger.info(f"Admin user {current_user.user_id} accessing user data for {target_user_id}")
            return True, None
        
        # Check if user is accessing their own data
        if current_user.user_id == target_user_id:
            return True, None
        
        # User is trying to access someone else's data
        logger.warning(
            f"Authorization failed: User {current_user.user_id} attempted to access "
            f"data for user {target_user_id}"
        )
        return False, ({'error': 'Access denied: You can only access your own data'}, 403)
        
    except Exception as e:
        logger.error(f"Error verifying user data access: {e}", exc_info=True)
        return False, ({'error': 'Authorization check failed'}, 500)


def require_self_or_admin(f):
    """
    Decorator to verify user can only access their own data or is an admin.
    
    Expects a 'user_id' parameter in the route.
    
    Requirements: 15.3
    
    Example:
        @app.route('/api/users/<user_id>/complaints')
        @jwt_required()
        @require_self_or_admin
        def get_user_complaints(user_id):
            # user_id is verified to be current user or current user is admin
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        target_user_id = kwargs.get('user_id')
        
        if not target_user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        is_authorized, error_response = verify_user_data_access(target_user_id)
        
        if not is_authorized:
            return jsonify(error_response[0]), error_response[1]
        
        return f(*args, **kwargs)
    
    return decorated_function
