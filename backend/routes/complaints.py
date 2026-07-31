"""
Complaint routes for grievance submission and management.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 15.3
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.complaint import Complaint, Location, Category, Status, PriorityLevel
from models.user import User
from models.status_history import StatusHistory
from models.feedback import Feedback
from services.nlp_engine import get_nlp_engine
from services.ml_classifier import get_ml_classifier
from services.priority_scoring import get_priority_scoring_engine
from services.duplicate_detection import get_duplicate_detection_service
from services.notification_service import notification_service
from services.feedback_service import get_feedback_service
from utils.authorization import require_complaint_ownership, require_self_or_admin
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

complaints_bp = Blueprint('complaints', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    from flask import current_app
    ALLOWED_EXTENSIONS = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@complaints_bp.route('', methods=['POST'])
@jwt_required()
def submit_complaint():
    """
    Submit a new complaint.
    
    Accepts text, voice (transcribed), images, videos, and location data.
    Validates required fields and stores the raw complaint in the database.
    Processes complaint text using NLP engine, ML classifier, priority scoring, and duplicate detection.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5
    
    Request Body (JSON or multipart/form-data):
        - description (required): Text description of the complaint
        - latitude (optional): GPS latitude
        - longitude (optional): GPS longitude
        - address (optional): Human-readable address
        - files (optional): Media files (images/videos)
    
    Returns:
        201: Complaint created successfully
        400: Invalid request data
        401: Unauthorized
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            files = []
        else:
            data = request.form.to_dict()
            files = request.files.getlist('files')
        
        # Validate required fields
        description = data.get('description', '').strip()
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        
        # User-selected category (optional; if not provided, ML will predict)
        category_mapping_request = {
            'Water Supply': Category.WATER_SUPPLY,
            'Electricity': Category.ELECTRICITY,
            'Roads & Infrastructure': Category.ROADS_INFRASTRUCTURE,
            'Healthcare': Category.HEALTHCARE,
            'Public Safety': Category.PUBLIC_SAFETY,
            'Sanitation': Category.SANITATION,
            'Other': Category.OTHER,
        }
        user_category_str = (data.get('category') or '').strip()
        user_selected_category = category_mapping_request.get(user_category_str) if user_category_str else None
        
        # Create location if coordinates provided
        # Support both flat (form/legacy) and nested 'location' (frontend JSON)
        location_obj = data.get('location')
        if location_obj and isinstance(location_obj, dict):
            latitude = location_obj.get('latitude')
            longitude = location_obj.get('longitude')
            address = location_obj.get('address', '') or data.get('address', '')
        else:
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            address = data.get('address', '')
        
        location = None
        if latitude is not None and longitude is not None:
            try:
                lat = float(latitude)
                lon = float(longitude)
                
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=address
                )
                db.session.add(location)
                db.session.flush()  # Get location_id
                
                logger.info(f"Location created: ({lat}, {lon})")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid coordinates provided: {e}")
                # Continue without location
        
        # Handle file uploads
        media_urls = []
        if files:
            from flask import current_app
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            
            # Ensure upload folder exists
            os.makedirs(upload_folder, exist_ok=True)
            
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid collisions
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(upload_folder, filename)
                    
                    file.save(filepath)
                    media_urls.append(filepath)
                    logger.info(f"File uploaded: {filepath}")
        
        # Process complaint text with NLP engine
        # Requirements: 3.1, 3.2, 3.3, 3.4
        nlp_engine = get_nlp_engine()
        nlp_result = nlp_engine.process_complaint(description)
        
        cleaned_text = nlp_result['cleaned_text']
        keywords = nlp_result['keywords']
        severity_terms = nlp_result['severity_terms']
        
        logger.info(
            f"NLP processing complete: {len(keywords)} keywords, "
            f"{len(severity_terms)} severity terms"
        )
        
        # Use user-selected category if provided; otherwise classify using ML
        confidence = None
        needs_review = False
        classification_result = {}
        if user_selected_category:
            complaint_category = user_selected_category
            confidence = 1.0  # User-selected, no ML uncertainty
            logger.info(f"Using user-selected category: {complaint_category.value}")
        else:
            # Classify complaint using ML classifier
            # Requirements: 4.1, 4.2, 4.3
            ml_classifier = get_ml_classifier()
            classification_result = ml_classifier.classify_with_review_flag(
                cleaned_text,
                keywords
            )
            
            predicted_category = classification_result['category']
            confidence = classification_result['confidence']
            needs_review = classification_result['needs_review']
            
            logger.info(
                f"ML classification complete: {predicted_category} "
                f"(confidence: {confidence:.2f}, needs_review: {needs_review})"
            )
            
            # Map predicted category string to Category enum
            category_mapping = {
                'Water Supply': Category.WATER_SUPPLY,
                'Electricity': Category.ELECTRICITY,
                'Roads & Infrastructure': Category.ROADS_INFRASTRUCTURE,
                'Healthcare': Category.HEALTHCARE,
                'Public Safety': Category.PUBLIC_SAFETY,
                'Sanitation': Category.SANITATION,
                'Other': Category.OTHER,
            }
            
            complaint_category = category_mapping.get(
                predicted_category,
                Category.OTHER  # Default fallback when ML doesn't match
            )
        
        # Create complaint with initial status (needed for priority scoring and duplicate detection)
        complaint = Complaint(
            user_id=user_id,
            description=cleaned_text,  # Store cleaned text
            category=complaint_category,
            status=Status.SUBMITTED,
            priority_level=PriorityLevel.LOW,  # Will be updated by priority scoring
            location_id=location.location_id if location else None,
            created_at=datetime.utcnow()
        )
        
        # Set NLP-extracted data
        complaint.set_keywords(keywords)
        complaint.set_severity_terms(severity_terms)
        
        # Set media URLs if any
        if media_urls:
            complaint.set_media_urls(media_urls)
        
        # Add to session so it can be queried by duplicate detection
        db.session.add(complaint)
        db.session.flush()  # Get complaint_id
        
        # Detect duplicates
        # Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        duplicate_service = get_duplicate_detection_service()
        duplicate_ids = duplicate_service.find_duplicates(complaint)
        
        duplicate_count = len(duplicate_ids)
        cluster_id = None
        
        if duplicate_count > 0:
            logger.info(f"Found {duplicate_count} duplicates for complaint {complaint.complaint_id}")
            
            # Create or update cluster
            all_complaint_ids = [complaint.complaint_id] + duplicate_ids
            cluster_id = duplicate_service.create_cluster(all_complaint_ids)
            
            if cluster_id:
                complaint.cluster_id = cluster_id
                logger.info(f"Complaint {complaint.complaint_id} added to cluster {cluster_id}")
        
        # Calculate priority score with duplicate count
        # Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        priority_engine = get_priority_scoring_engine()
        
        # Get nearby sensitive locations if location exists
        nearby_sensitive_locations = []
        if location:
            nearby_sensitive_locations = location.get_nearby_sensitive_locations()
        
        # Calculate priority with duplicate count
        impact_score, priority_level, explanation = priority_engine.calculate_priority(
            severity_terms=severity_terms,
            nearby_sensitive_locations=nearby_sensitive_locations,
            category=complaint_category,
            duplicate_count=duplicate_count,
            created_at=complaint.created_at
        )
        
        # Update complaint with priority data
        complaint.impact_score = impact_score
        complaint.priority_level = priority_level
        complaint.explanation = explanation
        
        logger.info(
            f"Priority scoring complete: Score={impact_score}, "
            f"Level={priority_level.value}, Duplicates={duplicate_count}"
        )
        
        # If complaint is part of a cluster, update all cluster impact scores
        if cluster_id:
            duplicate_service.update_cluster_impact_scores(cluster_id)
            logger.info(f"Updated impact scores for cluster {cluster_id}")
        
        # Record initial status in history
        # Requirements: 9.3
        status_history = StatusHistory(
            complaint_id=complaint.complaint_id,
            old_status=None,  # Initial submission has no old status
            new_status=Status.SUBMITTED.value,
            changed_by=user_id,
            notes="Complaint submitted"
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        logger.info(f"Complaint {complaint.complaint_id} submitted by user {user_id}")
        
        # Send notification to user about complaint submission
        # Requirements: 11.1
        try:
            tracking_url = f"/complaints/{complaint.complaint_id}"  # Adjust based on frontend URL
            notification_service.notify_complaint_submitted(
                user_phone=user.phone,
                user_email=user.email,
                complaint_id=complaint.complaint_id,
                priority=complaint.priority_level.value,
                tracking_url=tracking_url
            )
            logger.info(f"Submission notifications sent for complaint {complaint.complaint_id}")
        except Exception as e:
            # Don't fail the request if notification fails
            logger.error(f"Failed to send submission notifications: {e}", exc_info=True)
        
        response_data = {
            'message': 'Complaint submitted successfully',
            'complaint_id': complaint.complaint_id,
            'status': complaint.status.value,
            'category': complaint.category.value,
            'confidence': confidence,
            'priority_level': complaint.priority_level.value,
            'impact_score': complaint.impact_score,
            'explanation': complaint.explanation,
            'keywords': keywords,
            'severity_terms': severity_terms,
            'duplicate_count': duplicate_count
        }
        
        if cluster_id:
            response_data['cluster_id'] = cluster_id
        
        if needs_review:
            response_data['needs_review'] = True
            response_data['review_reason'] = classification_result['review_reason']
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting complaint: {e}", exc_info=True)
        return jsonify({'error': 'Failed to submit complaint'}), 500


@complaints_bp.route('/<complaint_id>', methods=['GET'])
@jwt_required()
@require_complaint_ownership(allow_admin=True)
def get_complaint(complaint_id, complaint=None):
    """
    Retrieve complaint details with current status.
    
    Returns complaint details including current status, priority explanation,
    and all associated information.
    
    Authorization: User must own the complaint or be an admin.
    
    Requirements: 9.1, 9.2, 7.3, 15.3
    
    Returns:
        200: Complaint details retrieved successfully
        401: Unauthorized
        403: Forbidden (user doesn't own this complaint)
        404: Complaint not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Complaint is already verified by decorator
        # If complaint is None, fetch it (shouldn't happen with decorator)
        if complaint is None:
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                return jsonify({'error': 'Complaint not found'}), 404
        
        # Get duplicate count if part of a cluster
        duplicate_count = 0
        if complaint.cluster_id:
            from models.duplicate_cluster import DuplicateCluster
            cluster = DuplicateCluster.query.get(complaint.cluster_id)
            if cluster:
                # Use relationship count; exclude the current complaint
                duplicate_count = cluster.complaints.count() - 1
        
        # Build response with all complaint details
        response_data = complaint.to_dict()
        response_data['duplicate_count'] = duplicate_count
        
        logger.info(f"Complaint {complaint_id} retrieved by user {user_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error retrieving complaint: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve complaint'}), 500


@complaints_bp.route('/<complaint_id>/history', methods=['GET'])
@jwt_required()
@require_complaint_ownership(allow_admin=True)
def get_complaint_history(complaint_id, complaint=None):
    """
    Retrieve complaint status history.
    
    Returns all status transitions with timestamps for a complaint.
    
    Authorization: User must own the complaint or be an admin.
    
    Requirements: 9.3, 15.3
    
    Returns:
        200: History retrieved successfully
        401: Unauthorized
        403: Forbidden (user doesn't own this complaint)
        404: Complaint not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Complaint is already verified by decorator
        if complaint is None:
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                return jsonify({'error': 'Complaint not found'}), 404
        
        # Fetch all status history entries for this complaint, ordered by timestamp
        history_entries = StatusHistory.query.filter_by(
            complaint_id=complaint_id
        ).order_by(StatusHistory.changed_at.asc()).all()
        
        # Convert to list of dictionaries
        history_data = [entry.to_dict() for entry in history_entries]
        
        logger.info(f"Complaint history for {complaint_id} retrieved by user {user_id}")
        
        return jsonify({
            'complaint_id': complaint_id,
            'history': history_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving complaint history: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve complaint history'}), 500


@complaints_bp.route('/user/<user_id>', methods=['GET'])
@jwt_required()
@require_self_or_admin
def get_user_complaints(user_id):
    """
    Retrieve all complaints for a specific user.
    
    Returns a list of all complaints submitted by the user.
    
    Authorization: User can only access their own complaints unless they are an admin.
    
    Requirements: 9.1, 15.3
    
    Returns:
        200: Complaints retrieved successfully
        401: Unauthorized
        403: Forbidden (user can only access their own complaints)
        404: User not found
        500: Server error
    """
    try:
        # Authorization is already verified by decorator
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Fetch all complaints for this user, ordered by creation date (newest first)
        complaints = Complaint.query.filter_by(
            user_id=user_id
        ).order_by(Complaint.created_at.desc()).all()
        
        # Convert to list of dictionaries
        complaints_data = []
        for complaint in complaints:
            complaint_dict = complaint.to_dict()
            
            # Add duplicate count if part of a cluster
            duplicate_count = 0
            if complaint.cluster_id:
                from models.duplicate_cluster import DuplicateCluster
                cluster = DuplicateCluster.query.get(complaint.cluster_id)
                if cluster:
                    duplicate_count = cluster.complaints.count() - 1
            
            complaint_dict['duplicate_count'] = duplicate_count
            complaints_data.append(complaint_dict)
        
        logger.info(f"Retrieved {len(complaints_data)} complaints for user {user_id}")
        
        return jsonify({
            'user_id': user_id,
            'total_complaints': len(complaints_data),
            'complaints': complaints_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving user complaints: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve user complaints'}), 500


@complaints_bp.route('/<complaint_id>/status', methods=['PATCH'])
@jwt_required()
def update_complaint_status(complaint_id):
    """
    Update complaint status.
    
    Allows officers to update complaint status (e.g., mark as resolved).
    Sends appropriate notifications based on status change.
    
    Requirements: 9.2, 11.2, 11.5
    
    Request Body (JSON):
        - status (required): New status value
    
    Returns:
        200: Status updated successfully
        400: Invalid request data
        401: Unauthorized
        404: Complaint not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status_str = data['status']
        
        # Validate status
        try:
            new_status = Status[new_status_str.upper().replace(' ', '_')]
        except KeyError:
            return jsonify({'error': f'Invalid status: {new_status_str}'}), 400
        
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Store old status for notification
        old_status = complaint.status.value
        
        # Update status
        complaint.status = new_status
        
        # Record status change in history
        # Requirements: 9.3
        status_history = StatusHistory(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status.value,
            changed_by=user_id,
            notes=data.get('notes', '')  # Optional notes from request
        )
        db.session.add(status_history)
        
        # If marking as resolved, record resolution time
        if new_status == Status.RESOLVED:
            complaint.resolved_at = datetime.utcnow()
            logger.info(f"Complaint {complaint_id} marked as resolved")
        
        db.session.commit()
        
        # Send notifications
        # Requirements: 11.2, 11.5
        try:
            user = User.query.get(complaint.user_id)
            
            if user:
                if new_status == Status.RESOLVED:
                    # Send resolution notification with feedback request
                    from services.monitoring_service import get_monitoring_service
                    monitoring_service = get_monitoring_service()
                    
                    resolution_time = monitoring_service.get_resolution_time(complaint)
                    resolution_time_str = str(resolution_time) if resolution_time else "N/A"
                    
                    feedback_url = f"/complaints/{complaint_id}/feedback"
                    
                    notification_service.notify_resolution(
                        user_phone=user.phone,
                        user_email=user.email,
                        complaint_id=complaint.complaint_id,
                        resolution_time=resolution_time_str,
                        feedback_url=feedback_url
                    )
                else:
                    # Send general status change notification
                    notification_service.notify_status_change(
                        user_phone=user.phone,
                        user_email=user.email,
                        complaint_id=complaint.complaint_id,
                        old_status=old_status,
                        new_status=new_status.value
                    )
                
                logger.info(f"Status change notifications sent for complaint {complaint_id}")
        except Exception as e:
            # Don't fail the request if notification fails
            logger.error(f"Failed to send status change notifications: {e}", exc_info=True)
        
        return jsonify({
            'message': 'Status updated successfully',
            'complaint_id': complaint_id,
            'old_status': old_status,
            'new_status': new_status.value
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating complaint status: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update status'}), 500


@complaints_bp.route('/<complaint_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_complaint(complaint_id):
    """
    Mark a complaint as resolved.
    
    This is a dedicated endpoint for resolving complaints that automatically
    calculates and stores the resolution time.
    
    Requirements: 10.5
    
    Request Body (JSON):
        - notes (optional): Resolution notes
    
    Returns:
        200: Complaint resolved successfully
        400: Invalid request data
        401: Unauthorized
        404: Complaint not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Check if already resolved
        if complaint.status == Status.RESOLVED:
            return jsonify({'error': 'Complaint is already resolved'}), 400
        
        # Store old status for notification
        old_status = complaint.status.value
        
        # Update status to resolved
        complaint.status = Status.RESOLVED
        complaint.resolved_at = datetime.utcnow()
        
        # Record status change in history
        status_history = StatusHistory(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=Status.RESOLVED.value,
            changed_by=user_id,
            notes=notes
        )
        db.session.add(status_history)
        
        # Calculate resolution time
        from services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        resolution_time = monitoring_service.get_resolution_time(complaint)
        
        db.session.commit()
        
        logger.info(
            f"Complaint {complaint_id} marked as resolved by user {user_id}. "
            f"Resolution time: {resolution_time}"
        )
        
        # Send resolution notification with feedback request
        try:
            user = User.query.get(complaint.user_id)
            
            if user:
                resolution_time_str = str(resolution_time) if resolution_time else "N/A"
                feedback_url = f"/complaints/{complaint_id}/feedback"
                
                notification_service.notify_resolution(
                    user_phone=user.phone,
                    user_email=user.email,
                    complaint_id=complaint.complaint_id,
                    resolution_time=resolution_time_str,
                    feedback_url=feedback_url
                )
                
                logger.info(f"Resolution notifications sent for complaint {complaint_id}")
        except Exception as e:
            # Don't fail the request if notification fails
            logger.error(f"Failed to send resolution notifications: {e}", exc_info=True)
        
        return jsonify({
            'message': 'Complaint resolved successfully',
            'complaint_id': complaint_id,
            'resolved_at': complaint.resolved_at.isoformat(),
            'resolution_time': str(resolution_time) if resolution_time else None,
            'resolution_time_hours': resolution_time.total_seconds() / 3600 if resolution_time else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resolving complaint: {e}", exc_info=True)
        return jsonify({'error': 'Failed to resolve complaint'}), 500



@complaints_bp.route('/<complaint_id>/feedback', methods=['POST'])
@jwt_required()
@require_complaint_ownership(allow_admin=False)
def submit_feedback(complaint_id, complaint=None):
    """
    Submit feedback for a resolved complaint.
    
    Allows citizens to provide a rating (1-5 stars) and optional comments
    after their complaint has been resolved. Updates user trust score and
    flags dissatisfaction for review.
    
    Authorization: User must own the complaint (admins cannot submit feedback for others).
    
    Requirements: 13.1, 13.2, 13.3, 13.5, 15.3
    
    Request Body (JSON):
        - rating (required): Integer rating from 1-5
        - comments (optional): Text feedback comments
    
    Returns:
        201: Feedback submitted successfully
        400: Invalid request data
        401: Unauthorized
        403: Forbidden (user doesn't own this complaint)
        404: Complaint not found
        409: Feedback already submitted
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate rating
        rating = data.get('rating')
        if rating is None:
            return jsonify({'error': 'Rating is required'}), 400
        
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return jsonify({'error': 'Rating must be an integer'}), 400
        
        comments = data.get('comments', '').strip() or None
        
        # Submit feedback using feedback service
        feedback_service = get_feedback_service()
        feedback, error = feedback_service.submit_feedback(
            complaint_id=complaint_id,
            user_id=user_id,
            rating=rating,
            comments=comments
        )
        
        if error:
            # Determine appropriate status code based on error message
            if "not found" in error.lower():
                status_code = 404
            elif "access denied" in error.lower():
                status_code = 403
            elif "already been submitted" in error.lower():
                status_code = 409
            elif "rating must be" in error.lower() or "only be submitted" in error.lower():
                status_code = 400
            else:
                status_code = 500
            
            return jsonify({'error': error}), status_code
        
        logger.info(f"Feedback submitted successfully for complaint {complaint_id}")
        
        # Update user trust score based on feedback
        # Requirements: 13.3, 13.5
        new_trust_score, trust_error = feedback_service.update_trust_score(
            user_id=user_id,
            feedback=feedback
        )
        
        if trust_error:
            logger.error(f"Failed to update trust score: {trust_error}")
            # Don't fail the request, feedback was already saved
        else:
            logger.info(f"Trust score updated to {new_trust_score} for user {user_id}")
        
        # Flag dissatisfaction if rating is low
        # Requirements: 13.3, 13.5
        is_flagged = feedback_service.flag_dissatisfaction(
            complaint_id=complaint_id,
            feedback=feedback
        )
        
        response_data = {
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.feedback_id,
            'complaint_id': complaint_id,
            'rating': feedback.rating,
            'comments': feedback.comments,
            'created_at': feedback.created_at.isoformat()
        }
        
        if new_trust_score is not None:
            response_data['new_trust_score'] = new_trust_score
        
        if is_flagged:
            response_data['flagged_for_review'] = True
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        return jsonify({'error': 'Failed to submit feedback'}), 500


@complaints_bp.route('/<complaint_id>/feedback', methods=['GET'])
@jwt_required()
@require_complaint_ownership(allow_admin=True)
def get_feedback(complaint_id, complaint=None):
    """
    Retrieve feedback for a complaint.
    
    Returns feedback details if feedback has been submitted for the complaint.
    
    Authorization: User must own the complaint or be an admin.
    
    Requirements: 13.1, 15.3
    
    Returns:
        200: Feedback retrieved successfully
        401: Unauthorized
        403: Forbidden (user doesn't own this complaint)
        404: Complaint or feedback not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Complaint is already verified by decorator
        if complaint is None:
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                return jsonify({'error': 'Complaint not found'}), 404
        
        # Fetch feedback
        feedback = Feedback.query.filter_by(
            complaint_id=complaint_id,
            user_id=user_id
        ).first()
        
        if not feedback:
            return jsonify({'error': 'Feedback not found'}), 404
        
        logger.info(f"Feedback retrieved for complaint {complaint_id}")
        
        return jsonify(feedback.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve feedback'}), 500


@complaints_bp.route('/<complaint_id>', methods=['DELETE'])
@jwt_required()
@require_complaint_ownership(allow_admin=False)
def delete_complaint(complaint_id, complaint=None):
    """
    Delete a complaint.
    
    Allows users to delete their own complaints. Only the complaint owner can delete.
    Admins cannot delete complaints on behalf of users.
    
    Authorization: User must own the complaint.
    
    Returns:
        200: Complaint deleted successfully
        401: Unauthorized
        403: Forbidden (user doesn't own this complaint)
        404: Complaint not found
        500: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        # Complaint is already verified by decorator
        if complaint is None:
            complaint = Complaint.query.get(complaint_id)
            if not complaint:
                return jsonify({'error': 'Complaint not found'}), 404
        
        # Store complaint info for logging
        complaint_category = complaint.category.value
        
        # Delete the complaint (cascading will handle related records)
        db.session.delete(complaint)
        db.session.commit()
        
        logger.info(f"Complaint {complaint_id} ({complaint_category}) deleted by user {user_id}")
        
        return jsonify({
            'message': 'Complaint deleted successfully',
            'complaint_id': complaint_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting complaint: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete complaint'}), 500
