"""
Authentication routes for user registration, login, and session management.
Requirements: 1.1, 1.3, 15.1, 15.3
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db
from models.user import User
import bcrypt
import re
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone format (basic validation)."""
    # Remove spaces and dashes
    phone_clean = phone.replace(' ', '').replace('-', '')
    # Check if it's numeric and has reasonable length
    return phone_clean.isdigit() and 10 <= len(phone_clean) <= 15


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, password_hash):
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Requirements: 1.1, 15.1
    
    Request body:
    {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john@example.com",
        "password": "securepassword"
    }
    
    Returns:
    {
        "user_id": "uuid",
        "message": "User registered successfully"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate presence of required fields
        if not all([name, phone, email, password]):
            return jsonify({'error': 'All fields (name, phone, email, password) are required'}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate phone format
        if not validate_phone(phone):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        # Validate password strength (minimum 6 characters)
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user with same email already exists
        existing_user_email = User.query.filter_by(email=email).first()
        if existing_user_email:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Check if user with same phone already exists
        existing_user_phone = User.query.filter_by(phone=phone).first()
        if existing_user_phone:
            return jsonify({'error': 'Phone number already registered'}), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create new user
        new_user = User(
            name=name,
            phone=phone,
            email=email,
            password_hash=password_hash
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {new_user.user_id} ({email})")
        
        return jsonify({
            'user_id': new_user.user_id,
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and generate JWT token.
    
    Requirements: 1.3
    
    Request body:
    {
        "credential": "john@example.com or 1234567890",
        "password": "securepassword"
    }
    
    Returns:
    {
        "access_token": "jwt_token",
        "user_id": "uuid",
        "name": "John Doe",
        "email": "john@example.com"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        credential = data.get('credential', '').strip()
        password = data.get('password', '')
        
        if not credential or not password:
            return jsonify({'error': 'Credential and password are required'}), 400
        
        # Find user by email or phone
        user = None
        if validate_email(credential):
            user = User.query.filter_by(email=credential).first()
        elif validate_phone(credential):
            user = User.query.filter_by(phone=credential).first()
        else:
            return jsonify({'error': 'Invalid credential format'}), 400
        
        # Check if user exists
        if not user:
            logger.warning(f"Login attempt with non-existent credential: {credential}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {user.user_id}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        access_token = create_access_token(identity=user.user_id)
        
        logger.info(f"User logged in: {user.user_id} ({user.email})")
        
        return jsonify({
            'access_token': access_token,
            'user_id': user.user_id,
            'name': user.name,
            'email': user.email,
            'role': user.role.value
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_session():
    """
    Validate JWT token and return current user information.
    
    Requirements: 1.3, 15.3
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns:
    {
        "user_id": "uuid",
        "name": "John Doe",
        "email": "john@example.com",
        "trust_score": 50
    }
    """
    try:
        # Get user_id from JWT token
        current_user_id = get_jwt_identity()
        
        # Fetch user from database
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def get_current_user():
    """
    Helper function to get current authenticated user.
    Use this in other routes that require authentication.
    
    Requirements: 15.3
    
    Returns:
        User object or None
    """
    try:
        current_user_id = get_jwt_identity()
        return User.query.get(current_user_id)
    except Exception:
        return None
