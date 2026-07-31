"""
Admin complaint management routes for full oversight and control.

Provides comprehensive admin functionality for:
- Viewing all complaints with advanced filtering
- Updating complaint status with notes
- Viewing detailed timeline of complaint progress
- Generating detailed reports on complaint resolution
- Real-time status tracking

Requirements: Admin oversight, transparency, and reporting
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db
from models.complaint import Complaint, Category, Status, PriorityLevel
from models.status_history import StatusHistory
from models.user import User
from models.officer import Officer
from utils.authorization import require_admin
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta
import logging
import csv
import io
from flask import make_response

logger = logging.getLogger(__name__)

admin_complaints_bp = Blueprint('admin_complaints', __name__)


@admin_complaints_bp.route('/complaints', methods=['GET'])
@jwt_required()
@require_admin
def get_all_complaints():
    """
    Get all complaints with advanced filtering and pagination.
    
    Provides comprehensive complaint list with filtering by:
    - Status (active, pending, resolved, escalated)
    - Department/Category
    - Priority level
    - Date range
    - Search by complaint ID or description
    
    Authorization: Admin only
    
    Query Parameters:
        - status: Filter by status (comma-separated for multiple)
        - category: Filter by category
        - priority: Filter by priority level
        - start_date: Filter complaints from this date (ISO format)
        - end_date: Filter complaints until this date (ISO format)
        - search: Search in complaint ID or description
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)
        - sort_by: Sort field (created_at, priority_level, status)
        - sort_order: asc or desc (default: desc)
    
    Returns:
        200: List of complaints with pagination info
        400: Invalid parameters
        401: Unauthorized
        403: Forbidden (not admin)
        500: Server error
    """
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build base query
        query = Complaint.query
        
        # Apply status filter
        status_filter = request.args.get('status')
        if status_filter:
            status_values = [s.strip() for s in status_filter.split(',')]
            status_enums = []
            for status_str in status_values:
                try:
                    status_enum = Status[status_str.upper().replace(' ', '_')]
                    status_enums.append(status_enum)
                except KeyError:
                    return jsonify({'error': f'Invalid status: {status_str}'}), 400
            
            if status_enums:
                query = query.filter(Complaint.status.in_(status_enums))
        
        # Apply category filter
        category_filter = request.args.get('category')
        if category_filter:
            try:
                category_enum = Category[category_filter.upper().replace(' ', '_').replace('&', '')]
                query = query.filter(Complaint.category == category_enum)
            except KeyError:
                return jsonify({'error': f'Invalid category: {category_filter}'}), 400
        
        # Apply priority filter
        priority_filter = request.args.get('priority')
        if priority_filter:
            try:
                priority_enum = PriorityLevel[priority_filter.upper()]
                query = query.filter(Complaint.priority_level == priority_enum)
            except KeyError:
                return jsonify({'error': f'Invalid priority: {priority_filter}'}), 400
        
        # Apply date range filter
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Complaint.created_at >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format'}), 400
        
        end_date = request.args.get('end_date')
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Complaint.created_at <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format'}), 400
        
        # Apply search filter
        search = request.args.get('search')
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Complaint.complaint_id.like(search_term),
                    Complaint.description.like(search_term)
                )
            )
        
        # Apply sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc').lower()
        
        if sort_by not in ['created_at', 'priority_level', 'status', 'impact_score']:
            return jsonify({'error': f'Invalid sort_by field: {sort_by}'}), 400
        
        if sort_order not in ['asc', 'desc']:
            return jsonify({'error': 'Invalid sort_order. Use asc or desc'}), 400
        
        sort_column = getattr(Complaint, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Execute paginated query
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format complaints with additional info
        complaints_data = []
        for complaint in pagination.items:
            complaint_dict = complaint.to_dict()
            
            # Add user info
            user = User.query.get(complaint.user_id)
            if user:
                complaint_dict['user'] = {
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone
                }
            
            # Add assigned officer info
            if complaint.assigned_officer_id:
                officer = Officer.query.get(complaint.assigned_officer_id)
                if officer:
                    complaint_dict['assigned_officer'] = {
                        'name': officer.name,
                        'department': officer.department.value
                    }
            
            # Add latest status update
            latest_history = StatusHistory.query.filter_by(
                complaint_id=complaint.complaint_id
            ).order_by(StatusHistory.changed_at.desc()).first()
            
            if latest_history:
                complaint_dict['latest_update'] = {
                    'changed_at': latest_history.changed_at.isoformat(),
                    'notes': latest_history.notes
                }
            
            complaints_data.append(complaint_dict)
        
        logger.info(
            f"Admin retrieved {len(complaints_data)} complaints "
            f"(page {page}/{pagination.pages})"
        )
        
        return jsonify({
            'complaints': complaints_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'filters_applied': {
                'status': status_filter,
                'category': category_filter,
                'priority': priority_filter,
                'start_date': start_date,
                'end_date': end_date,
                'search': search
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error retrieving complaints: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve complaints'}), 500


@admin_complaints_bp.route('/complaints/<complaint_id>/timeline', methods=['GET'])
@jwt_required()
@require_admin
def get_complaint_timeline(complaint_id):
    """
    Get detailed timeline view of complaint progress.
    
    Returns complete history showing:
    - Submission
    - Assignment to officer
    - Status changes (in-progress, escalated, etc.)
    - Resolution
    - Time spent in each status
    
    Authorization: Admin only
    
    Returns:
        200: Timeline data with time analysis
        401: Unauthorized
        403: Forbidden (not admin)
        404: Complaint not found
        500: Server error
    """
    try:
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Get all status history entries
        history_entries = StatusHistory.query.filter_by(
            complaint_id=complaint_id
        ).order_by(StatusHistory.changed_at.asc()).all()
        
        # Build timeline with time analysis
        timeline = []
        time_in_status = {}
        
        for i, entry in enumerate(history_entries):
            # Get user who made the change
            changed_by_user = None
            if entry.changed_by:
                user = User.query.get(entry.changed_by)
                if user:
                    changed_by_user = {
                        'user_id': user.user_id,
                        'name': user.name,
                        'role': user.role.value
                    }
            
            # Calculate time in previous status
            time_spent = None
            if i > 0:
                previous_entry = history_entries[i - 1]
                time_diff = entry.changed_at - previous_entry.changed_at
                time_spent = {
                    'seconds': time_diff.total_seconds(),
                    'hours': round(time_diff.total_seconds() / 3600, 2),
                    'days': round(time_diff.total_seconds() / 86400, 2),
                    'formatted': str(time_diff)
                }
                
                # Track time in each status
                status_key = previous_entry.new_status
                if status_key not in time_in_status:
                    time_in_status[status_key] = 0
                time_in_status[status_key] += time_diff.total_seconds()
            
            timeline.append({
                'history_id': entry.history_id,
                'old_status': entry.old_status,
                'new_status': entry.new_status,
                'changed_at': entry.changed_at.isoformat(),
                'changed_by': changed_by_user,
                'notes': entry.notes,
                'time_in_previous_status': time_spent
            })
        
        # Calculate time in current status
        if history_entries:
            last_entry = history_entries[-1]
            current_time_diff = datetime.utcnow() - last_entry.changed_at
            current_status_time = {
                'seconds': current_time_diff.total_seconds(),
                'hours': round(current_time_diff.total_seconds() / 3600, 2),
                'days': round(current_time_diff.total_seconds() / 86400, 2),
                'formatted': str(current_time_diff)
            }
            
            # Add to time tracking
            status_key = last_entry.new_status
            if status_key not in time_in_status:
                time_in_status[status_key] = 0
            time_in_status[status_key] += current_time_diff.total_seconds()
        else:
            current_status_time = None
        
        # Format time in status summary
        time_summary = {}
        for status, seconds in time_in_status.items():
            time_summary[status] = {
                'seconds': seconds,
                'hours': round(seconds / 3600, 2),
                'days': round(seconds / 86400, 2),
                'formatted': str(timedelta(seconds=seconds))
            }
        
        # Calculate overall resolution time
        overall_time = None
        if complaint.resolved_at:
            total_time = complaint.resolved_at - complaint.created_at
            overall_time = {
                'seconds': total_time.total_seconds(),
                'hours': round(total_time.total_seconds() / 3600, 2),
                'days': round(total_time.total_seconds() / 86400, 2),
                'formatted': str(total_time)
            }
        
        logger.info(f"Timeline retrieved for complaint {complaint_id}")
        
        return jsonify({
            'complaint_id': complaint_id,
            'complaint': complaint.to_dict(),
            'timeline': timeline,
            'time_in_current_status': current_status_time,
            'time_in_each_status': time_summary,
            'overall_resolution_time': overall_time,
            'total_status_changes': len(timeline)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving timeline: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve timeline'}), 500


@admin_complaints_bp.route('/complaints/<complaint_id>/status', methods=['PUT'])
@jwt_required()
@require_admin
def admin_update_status(complaint_id):
    """
    Admin endpoint to manually update complaint status with notes.
    
    Allows admins to:
    - Change complaint status
    - Add detailed notes about the change
    - Assign to officers
    - Track all changes in timeline
    
    Authorization: Admin only
    
    Request Body:
        - status (required): New status value
        - notes (optional): Notes about the status change
        - assigned_officer_id (optional): Officer to assign complaint to
    
    Returns:
        200: Status updated successfully
        400: Invalid request
        401: Unauthorized
        403: Forbidden (not admin)
        404: Complaint not found
        500: Server error
    """
    try:
        from flask_jwt_extended import get_jwt_identity
        admin_user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status_str = data['status']
        notes = data.get('notes', '')
        assigned_officer_id = data.get('assigned_officer_id')
        
        # Validate status
        try:
            new_status = Status[new_status_str.upper().replace(' ', '_')]
        except KeyError:
            return jsonify({'error': f'Invalid status: {new_status_str}'}), 400
        
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Store old status
        old_status = complaint.status
        
        # Update status
        complaint.status = new_status
        
        # Handle assignment
        if assigned_officer_id:
            officer = Officer.query.get(assigned_officer_id)
            if not officer:
                return jsonify({'error': 'Officer not found'}), 404
            
            complaint.assigned_officer_id = assigned_officer_id
            if not complaint.assigned_at:
                complaint.assigned_at = datetime.utcnow()
        
        # Handle resolution
        if new_status == Status.RESOLVED and not complaint.resolved_at:
            complaint.resolved_at = datetime.utcnow()
        
        # Record status change in history
        status_history = StatusHistory(
            complaint_id=complaint_id,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=admin_user_id,
            notes=notes
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        logger.info(
            f"Admin {admin_user_id} updated complaint {complaint_id} "
            f"from {old_status.value} to {new_status.value}"
        )
        
        # Send notification to user
        try:
            from services.notification_service import notification_service
            user = User.query.get(complaint.user_id)
            
            if user:
                notification_service.notify_status_change(
                    user_phone=user.phone,
                    user_email=user.email,
                    complaint_id=complaint.complaint_id,
                    old_status=old_status.value,
                    new_status=new_status.value
                )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
        
        return jsonify({
            'message': 'Status updated successfully',
            'complaint_id': complaint_id,
            'old_status': old_status.value,
            'new_status': new_status.value,
            'updated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating status: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update status'}), 500


@admin_complaints_bp.route('/complaints/<complaint_id>/notes', methods=['POST'])
@jwt_required()
@require_admin
def add_complaint_note(complaint_id):
    """
    Add a note to complaint without changing status.
    
    Allows admins to add progress updates and notes to complaints
    for internal tracking and transparency.
    
    Authorization: Admin only
    
    Request Body:
        - notes (required): Note text
    
    Returns:
        201: Note added successfully
        400: Invalid request
        401: Unauthorized
        403: Forbidden (not admin)
        404: Complaint not found
        500: Server error
    """
    try:
        from flask_jwt_extended import get_jwt_identity
        admin_user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data or 'notes' not in data:
            return jsonify({'error': 'Notes are required'}), 400
        
        notes = data['notes'].strip()
        if not notes:
            return jsonify({'error': 'Notes cannot be empty'}), 400
        
        # Fetch complaint
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Add note as status history entry (same status)
        status_history = StatusHistory(
            complaint_id=complaint_id,
            old_status=complaint.status.value,
            new_status=complaint.status.value,
            changed_by=admin_user_id,
            notes=notes
        )
        db.session.add(status_history)
        db.session.commit()
        
        logger.info(f"Admin {admin_user_id} added note to complaint {complaint_id}")
        
        return jsonify({
            'message': 'Note added successfully',
            'complaint_id': complaint_id,
            'note': status_history.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding note: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add note'}), 500


@admin_complaints_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
@require_admin
def get_dashboard_summary():
    """
    Get summary statistics for admin dashboard.
    
    Returns counts of:
    - Active complaints (submitted, assigned, in-progress)
    - Pending complaints (submitted, not yet assigned)
    - Resolved complaints
    - Escalated complaints
    - By priority level
    - By category
    
    Authorization: Admin only
    
    Returns:
        200: Dashboard summary data
        401: Unauthorized
        403: Forbidden (not admin)
        500: Server error
    """
    try:
        # Count by status
        active_statuses = [Status.SUBMITTED, Status.ASSIGNED, Status.IN_PROGRESS]
        active_count = Complaint.query.filter(
            Complaint.status.in_(active_statuses)
        ).count()
        
        pending_count = Complaint.query.filter_by(status=Status.SUBMITTED).count()
        resolved_count = Complaint.query.filter_by(status=Status.RESOLVED).count()
        escalated_count = Complaint.query.filter_by(status=Status.ESCALATED).count()
        
        # Count by priority
        priority_counts = {}
        for priority in PriorityLevel:
            count = Complaint.query.filter_by(priority_level=priority).count()
            priority_counts[priority.value] = count
        
        # Count by category
        category_counts = {}
        for category in Category:
            count = Complaint.query.filter_by(category=category).count()
            category_counts[category.value] = count
        
        # Count by status (all statuses)
        status_counts = {}
        for status in Status:
            count = Complaint.query.filter_by(status=status).count()
            status_counts[status.value] = count
        
        # Recent activity (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_submissions = Complaint.query.filter(
            Complaint.created_at >= last_24h
        ).count()
        
        recent_resolutions = Complaint.query.filter(
            Complaint.resolved_at >= last_24h
        ).count()
        
        # Average resolution time (last 30 days)
        last_30d = datetime.utcnow() - timedelta(days=30)
        recent_resolved = Complaint.query.filter(
            Complaint.status == Status.RESOLVED,
            Complaint.resolved_at >= last_30d,
            Complaint.resolved_at.isnot(None)
        ).all()
        
        if recent_resolved:
            resolution_times = [
                (c.resolved_at - c.created_at).total_seconds() / 3600
                for c in recent_resolved
            ]
            avg_resolution_hours = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_hours = 0
        
        logger.info("Dashboard summary retrieved")
        
        return jsonify({
            'summary': {
                'active_complaints': active_count,
                'pending_complaints': pending_count,
                'resolved_complaints': resolved_count,
                'escalated_complaints': escalated_count,
                'total_complaints': Complaint.query.count()
            },
            'by_priority': priority_counts,
            'by_category': category_counts,
            'by_status': status_counts,
            'recent_activity': {
                'submissions_last_24h': recent_submissions,
                'resolutions_last_24h': recent_resolutions,
                'avg_resolution_time_hours': round(avg_resolution_hours, 2)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard summary: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve dashboard summary'}), 500


@admin_complaints_bp.route('/reports/resolution-times', methods=['GET'])
@jwt_required()
@require_admin
def generate_resolution_report():
    """
    Generate detailed report on complaint resolution times.
    
    Provides comprehensive analysis including:
    - Time spent in each status
    - Overall resolution time
    - Breakdown by category and priority
    - Export as JSON or CSV
    
    Authorization: Admin only
    
    Query Parameters:
        - start_date: Start date for report (ISO format)
        - end_date: End date for report (ISO format)
        - format: 'json' or 'csv' (default: json)
        - category: Filter by category
        - priority: Filter by priority
    
    Returns:
        200: Report data
        400: Invalid parameters
        401: Unauthorized
        403: Forbidden (not admin)
        500: Server error
    """
    try:
        # Get parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        export_format = request.args.get('format', 'json').lower()
        category_filter = request.args.get('category')
        priority_filter = request.args.get('priority')
        
        # Build query for resolved complaints
        query = Complaint.query.filter(
            Complaint.status == Status.RESOLVED,
            Complaint.resolved_at.isnot(None)
        )
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Complaint.created_at >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Complaint.created_at <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Apply category filter
        if category_filter:
            try:
                category_enum = Category[category_filter.upper().replace(' ', '_').replace('&', '')]
                query = query.filter(Complaint.category == category_enum)
            except KeyError:
                return jsonify({'error': f'Invalid category: {category_filter}'}), 400
        
        # Apply priority filter
        if priority_filter:
            try:
                priority_enum = PriorityLevel[priority_filter.upper()]
                query = query.filter(Complaint.priority_level == priority_enum)
            except KeyError:
                return jsonify({'error': f'Invalid priority: {priority_filter}'}), 400
        
        # Get complaints
        complaints = query.all()
        
        # Generate report data
        report_data = []
        for complaint in complaints:
            # Get status history
            history = StatusHistory.query.filter_by(
                complaint_id=complaint.complaint_id
            ).order_by(StatusHistory.changed_at.asc()).all()
            
            # Calculate time in each status
            time_in_status = {}
            for i in range(len(history)):
                if i < len(history) - 1:
                    time_diff = history[i + 1].changed_at - history[i].changed_at
                else:
                    # Last status until resolution
                    time_diff = complaint.resolved_at - history[i].changed_at
                
                status_key = history[i].new_status
                if status_key not in time_in_status:
                    time_in_status[status_key] = 0
                time_in_status[status_key] += time_diff.total_seconds() / 3600  # hours
            
            # Overall resolution time
            resolution_time = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600
            
            report_data.append({
                'complaint_id': complaint.complaint_id,
                'category': complaint.category.value,
                'priority': complaint.priority_level.value,
                'created_at': complaint.created_at.isoformat(),
                'resolved_at': complaint.resolved_at.isoformat(),
                'resolution_time_hours': round(resolution_time, 2),
                'time_in_submitted': round(time_in_status.get('Submitted', 0), 2),
                'time_in_assigned': round(time_in_status.get('Assigned', 0), 2),
                'time_in_progress': round(time_in_status.get('In Progress', 0), 2),
                'time_in_escalated': round(time_in_status.get('Escalated', 0), 2),
                'total_status_changes': len(history)
            })
        
        logger.info(f"Resolution report generated with {len(report_data)} complaints")
        
        # Export as CSV if requested
        if export_format == 'csv':
            if not report_data:
                return jsonify({'message': 'No data available for report'}), 200
            
            output = io.StringIO()
            fieldnames = list(report_data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=resolution_report.csv'
            
            return response
        
        # Return as JSON
        return jsonify({
            'report': report_data,
            'summary': {
                'total_complaints': len(report_data),
                'avg_resolution_time_hours': round(
                    sum(r['resolution_time_hours'] for r in report_data) / len(report_data), 2
                ) if report_data else 0
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'category': category_filter,
                'priority': priority_filter
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate report'}), 500
