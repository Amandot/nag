"""
Admin routes for administrative functions.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 13.4, 15.3, 15.5
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.feedback_service import get_feedback_service
from models import db
from models.complaint import Complaint, Category, PriorityLevel, Status
from models.officer import Officer, Department
from utils.authorization import require_admin
from utils.anonymization import anonymize_heatmap_data, remove_pii_from_analytics
from sqlalchemy import func, case
from datetime import datetime, timedelta
import logging
import csv
import io
from flask import make_response

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/heatmap', methods=['GET'])
@jwt_required()
@require_admin
def get_complaint_heatmap():
    """
    Get complaint locations with counts for heatmap visualization.
    
    Returns complaint data grouped by location with counts and priority information
    for displaying on a geographic heatmap.
    
    Authorization: Admin only.
    
    Requirements: 12.1, 15.3
    
    Query Parameters:
        - status (optional): Filter by status (e.g., 'Submitted', 'Assigned', 'In Progress')
        - priority (optional): Filter by priority level (e.g., 'Critical', 'High')
        - category (optional): Filter by category (e.g., 'Water Supply', 'Electricity')
        - days (optional): Filter complaints from last N days (default: 30)
    
    Returns:
        200: Heatmap data with complaint locations and counts
        401: Unauthorized
        500: Server error
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        category_filter = request.args.get('category')
        days = int(request.args.get('days', 30))
        
        # Build query
        query = db.session.query(
            Complaint.location_id,
            func.count(Complaint.complaint_id).label('count'),
            func.avg(Complaint.impact_score).label('avg_impact_score')
        ).join(
            Complaint.location
        ).filter(
            Complaint.location_id.isnot(None)
        )
        
        # Apply filters
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Complaint.created_at >= cutoff_date)
        
        if status_filter:
            try:
                status_enum = Status[status_filter.upper().replace(' ', '_')]
                query = query.filter(Complaint.status == status_enum)
            except KeyError:
                return jsonify({'error': f'Invalid status: {status_filter}'}), 400
        
        if priority_filter:
            try:
                priority_enum = PriorityLevel[priority_filter.upper()]
                query = query.filter(Complaint.priority_level == priority_enum)
            except KeyError:
                return jsonify({'error': f'Invalid priority: {priority_filter}'}), 400
        
        if category_filter:
            try:
                category_enum = Category[category_filter.upper().replace(' ', '_').replace('&', '')]
                query = query.filter(Complaint.category == category_enum)
            except KeyError:
                return jsonify({'error': f'Invalid category: {category_filter}'}), 400
        
        # Group by location
        query = query.group_by(Complaint.location_id)
        
        # Execute query
        results = query.all()
        
        # Build heatmap data
        heatmap_data = []
        for location_id, count, avg_impact_score in results:
            # Get location details
            from models.complaint import Location
            location = Location.query.get(location_id)
            
            if location:
                # Get priority distribution for this location
                priority_dist = db.session.query(
                    Complaint.priority_level,
                    func.count(Complaint.complaint_id).label('count')
                ).filter(
                    Complaint.location_id == location_id
                ).group_by(
                    Complaint.priority_level
                ).all()
                
                priority_counts = {
                    'CRITICAL': 0,
                    'HIGH': 0,
                    'MEDIUM': 0,
                    'LOW': 0
                }
                
                for priority, priority_count in priority_dist:
                    priority_counts[priority.name] = priority_count
                
                heatmap_data.append({
                    'location': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'address': location.address
                    },
                    'complaint_count': count,
                    'avg_impact_score': round(avg_impact_score, 2) if avg_impact_score else 0,
                    'priority_distribution': priority_counts
                })
        
        logger.info(f"Heatmap data retrieved: {len(heatmap_data)} locations")
        
        # Anonymize location data for privacy (Requirements: 15.5)
        anonymized_heatmap = anonymize_heatmap_data(heatmap_data)
        
        return jsonify({
            'total_locations': len(anonymized_heatmap),
            'heatmap_data': anonymized_heatmap,
            'filters_applied': {
                'status': status_filter,
                'priority': priority_filter,
                'category': category_filter,
                'days': days
            },
            'privacy_note': 'Location data has been anonymized to ~1km precision for privacy protection'
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter in heatmap request: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate heatmap data'}), 500


@admin_bp.route('/analytics/trends', methods=['GET'])
@jwt_required()
@require_admin
def get_category_trends():
    """
    Get category-wise complaint trends over time.
    
    Returns time-series data showing complaint counts by category,
    useful for identifying patterns and trends.
    
    Authorization: Admin only.
    
    Requirements: 12.2, 15.3
    
    Query Parameters:
        - days (optional): Number of days to analyze (default: 30)
        - interval (optional): Grouping interval - 'day', 'week', 'month' (default: 'day')
    
    Returns:
        200: Category trends data
        401: Unauthorized
        500: Server error
    """
    try:
        # Get query parameters
        days = int(request.args.get('days', 30))
        interval = request.args.get('interval', 'day').lower()
        
        if interval not in ['day', 'week', 'month']:
            return jsonify({'error': 'Invalid interval. Use: day, week, or month'}), 400
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query complaints within date range
        complaints = Complaint.query.filter(
            Complaint.created_at >= start_date,
            Complaint.created_at <= end_date
        ).all()
        
        # Group by category and time interval
        trends = {}
        for category in Category:
            trends[category.value] = []
        
        # Create time buckets
        current_date = start_date
        time_buckets = []
        
        if interval == 'day':
            delta = timedelta(days=1)
        elif interval == 'week':
            delta = timedelta(weeks=1)
        else:  # month
            delta = timedelta(days=30)
        
        while current_date < end_date:
            bucket_end = min(current_date + delta, end_date)
            time_buckets.append({
                'start': current_date,
                'end': bucket_end,
                'label': current_date.strftime('%Y-%m-%d')
            })
            current_date = bucket_end
        
        # Count complaints per category per bucket
        for bucket in time_buckets:
            bucket_counts = {category.value: 0 for category in Category}
            
            for complaint in complaints:
                if bucket['start'] <= complaint.created_at < bucket['end']:
                    bucket_counts[complaint.category.value] += 1
            
            for category in Category:
                trends[category.value].append({
                    'date': bucket['label'],
                    'count': bucket_counts[category.value]
                })
        
        # Calculate summary statistics
        total_by_category = {}
        for category in Category:
            category_complaints = [c for c in complaints if c.category == category]
            total_by_category[category.value] = len(category_complaints)
        
        logger.info(f"Category trends retrieved for {days} days with {interval} interval")
        
        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
                'interval': interval
            },
            'trends': trends,
            'totals': total_by_category
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter in trends request: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error generating category trends: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate category trends'}), 500


@admin_bp.route('/analytics/departments', methods=['GET'])
@jwt_required()
@require_admin
def get_department_performance():
    """
    Get department performance metrics.
    
    Returns performance data for each department including pending cases,
    resolved cases, average resolution time, and workload distribution.
    
    Authorization: Admin only.
    
    Requirements: 12.3, 15.3
    
    Query Parameters:
        - days (optional): Analyze data from last N days (default: 30)
    
    Returns:
        200: Department performance metrics
        401: Unauthorized
        500: Server error
    """
    try:
        # Get query parameters
        days = int(request.args.get('days', 30))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Map categories to departments
        category_to_dept = {
            Category.WATER_SUPPLY: Department.WATER_DEPT,
            Category.ELECTRICITY: Department.ELECTRICITY_DEPT,
            Category.ROADS_INFRASTRUCTURE: Department.ROADS_DEPT,
            Category.HEALTHCARE: Department.HEALTH_DEPT,
            Category.PUBLIC_SAFETY: Department.SAFETY_DEPT,
            Category.SANITATION: Department.SANITATION_DEPT
        }
        
        department_metrics = []
        
        for category, department in category_to_dept.items():
            # Get complaints for this category
            all_complaints = Complaint.query.filter(
                Complaint.category == category,
                Complaint.created_at >= cutoff_date
            ).all()
            
            pending_complaints = [c for c in all_complaints if c.status != Status.RESOLVED]
            resolved_complaints = [c for c in all_complaints if c.status == Status.RESOLVED]
            
            # Calculate average resolution time
            resolution_times = []
            for complaint in resolved_complaints:
                if complaint.created_at and complaint.resolved_at:
                    resolution_time = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600  # hours
                    resolution_times.append(resolution_time)
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            # Get officers in this department
            officers = Officer.query.filter(Officer.department == department).all()
            total_officers = len(officers)
            total_workload = sum(officer.assigned_cases for officer in officers)
            
            # Calculate SLA compliance
            sla_violations = len([c for c in all_complaints if c.status == Status.ESCALATED])
            sla_compliance_rate = ((len(all_complaints) - sla_violations) / len(all_complaints) * 100) if all_complaints else 100
            
            department_metrics.append({
                'department': department.value,
                'category': category.value,
                'total_complaints': len(all_complaints),
                'pending_complaints': len(pending_complaints),
                'resolved_complaints': len(resolved_complaints),
                'avg_resolution_time_hours': round(avg_resolution_time, 2),
                'total_officers': total_officers,
                'total_workload': total_workload,
                'avg_workload_per_officer': round(total_workload / total_officers, 2) if total_officers > 0 else 0,
                'sla_violations': sla_violations,
                'sla_compliance_rate': round(sla_compliance_rate, 2)
            })
        
        logger.info(f"Department performance metrics retrieved for {days} days")
        
        return jsonify({
            'period_days': days,
            'departments': department_metrics
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter in department performance request: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error generating department performance: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate department performance metrics'}), 500


@admin_bp.route('/analytics/resolution-times', methods=['GET'])
@jwt_required()
@require_admin
def get_resolution_times():
    """
    Get resolution time analytics.
    
    Returns detailed analytics about complaint resolution times broken down
    by category and priority level.
    
    Authorization: Admin only.
    
    Requirements: 12.4, 15.3
    
    Query Parameters:
        - days (optional): Analyze data from last N days (default: 30)
    
    Returns:
        200: Resolution time analytics
        401: Unauthorized
        500: Server error
    """
    try:
        # Get query parameters
        days = int(request.args.get('days', 30))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get resolved complaints
        resolved_complaints = Complaint.query.filter(
            Complaint.status == Status.RESOLVED,
            Complaint.created_at >= cutoff_date,
            Complaint.resolved_at.isnot(None)
        ).all()
        
        # Calculate resolution times by category
        by_category = {}
        for category in Category:
            category_complaints = [c for c in resolved_complaints if c.category == category]
            
            if category_complaints:
                resolution_times = []
                for complaint in category_complaints:
                    resolution_time = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600  # hours
                    resolution_times.append(resolution_time)
                
                by_category[category.value] = {
                    'count': len(category_complaints),
                    'avg_hours': round(sum(resolution_times) / len(resolution_times), 2),
                    'min_hours': round(min(resolution_times), 2),
                    'max_hours': round(max(resolution_times), 2)
                }
            else:
                by_category[category.value] = {
                    'count': 0,
                    'avg_hours': 0,
                    'min_hours': 0,
                    'max_hours': 0
                }
        
        # Calculate resolution times by priority
        by_priority = {}
        for priority in PriorityLevel:
            priority_complaints = [c for c in resolved_complaints if c.priority_level == priority]
            
            if priority_complaints:
                resolution_times = []
                for complaint in priority_complaints:
                    resolution_time = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600  # hours
                    resolution_times.append(resolution_time)
                
                by_priority[priority.value] = {
                    'count': len(priority_complaints),
                    'avg_hours': round(sum(resolution_times) / len(resolution_times), 2),
                    'min_hours': round(min(resolution_times), 2),
                    'max_hours': round(max(resolution_times), 2)
                }
            else:
                by_priority[priority.value] = {
                    'count': 0,
                    'avg_hours': 0,
                    'min_hours': 0,
                    'max_hours': 0
                }
        
        # Calculate overall statistics
        if resolved_complaints:
            all_resolution_times = [
                (c.resolved_at - c.created_at).total_seconds() / 3600
                for c in resolved_complaints
            ]
            overall_stats = {
                'total_resolved': len(resolved_complaints),
                'avg_hours': round(sum(all_resolution_times) / len(all_resolution_times), 2),
                'min_hours': round(min(all_resolution_times), 2),
                'max_hours': round(max(all_resolution_times), 2)
            }
        else:
            overall_stats = {
                'total_resolved': 0,
                'avg_hours': 0,
                'min_hours': 0,
                'max_hours': 0
            }
        
        logger.info(f"Resolution time analytics retrieved for {days} days")
        
        return jsonify({
            'period_days': days,
            'overall': overall_stats,
            'by_category': by_category,
            'by_priority': by_priority
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter in resolution times request: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error generating resolution time analytics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate resolution time analytics'}), 500


@admin_bp.route('/alerts', methods=['GET'])
@jwt_required()
@require_admin
def get_critical_alerts():
    """
    Get critical and escalated complaints for admin dashboard alerts.
    
    Returns complaints that require immediate attention, including critical
    priority complaints and escalated cases that exceeded SLA deadlines.
    
    Authorization: Admin only.
    
    Requirements: 12.5, 15.3
    
    Query Parameters:
        - limit (optional): Maximum number of alerts to return (default: 50)
        - include_high (optional): Include HIGH priority complaints (default: false)
    
    Returns:
        200: Critical alerts data
        401: Unauthorized
        500: Server error
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        include_high = request.args.get('include_high', 'false').lower() == 'true'
        
        # Build query for critical alerts
        query = Complaint.query.filter(
            Complaint.status != Status.RESOLVED
        )
        
        # Filter by priority
        if include_high:
            query = query.filter(
                Complaint.priority_level.in_([PriorityLevel.CRITICAL, PriorityLevel.HIGH])
            )
        else:
            query = query.filter(
                Complaint.priority_level == PriorityLevel.CRITICAL
            )
        
        # Get critical priority complaints
        critical_complaints = query.order_by(
            Complaint.impact_score.desc(),
            Complaint.created_at.asc()
        ).limit(limit).all()
        
        # Get escalated complaints
        escalated_complaints = Complaint.query.filter(
            Complaint.status == Status.ESCALATED
        ).order_by(
            Complaint.created_at.asc()
        ).limit(limit).all()
        
        # Get complaints approaching SLA deadline (within 25% of deadline)
        approaching_sla = []
        assigned_complaints = Complaint.query.filter(
            Complaint.status.in_([Status.ASSIGNED, Status.IN_PROGRESS]),
            Complaint.sla_deadline.isnot(None)
        ).all()
        
        current_time = datetime.utcnow()
        for complaint in assigned_complaints:
            if complaint.sla_deadline and complaint.assigned_at:
                time_remaining = (complaint.sla_deadline - current_time).total_seconds() / 3600  # hours
                total_sla_time = (complaint.sla_deadline - complaint.assigned_at).total_seconds() / 3600
                
                # Alert if less than 25% time remaining
                if 0 < time_remaining < (total_sla_time * 0.25):
                    approaching_sla.append(complaint)
        
        # Sort by time remaining
        approaching_sla.sort(key=lambda c: c.sla_deadline)
        approaching_sla = approaching_sla[:limit]
        
        # Format alerts
        def format_alert(complaint, alert_type, additional_info=None):
            alert = {
                'alert_type': alert_type,
                'complaint': complaint.to_dict(),
                'time_since_creation': str(datetime.utcnow() - complaint.created_at),
            }
            
            if additional_info:
                alert.update(additional_info)
            
            return alert
        
        alerts = []
        
        # Add critical priority alerts
        for complaint in critical_complaints:
            alerts.append(format_alert(
                complaint,
                'CRITICAL_PRIORITY',
                {'reason': f'Critical priority complaint with impact score {complaint.impact_score}'}
            ))
        
        # Add escalated alerts
        for complaint in escalated_complaints:
            alerts.append(format_alert(
                complaint,
                'ESCALATED',
                {'reason': 'Complaint exceeded SLA deadline and was escalated'}
            ))
        
        # Add approaching SLA alerts
        for complaint in approaching_sla:
            time_remaining = (complaint.sla_deadline - current_time).total_seconds() / 3600
            alerts.append(format_alert(
                complaint,
                'APPROACHING_SLA',
                {
                    'reason': f'SLA deadline approaching in {round(time_remaining, 1)} hours',
                    'sla_deadline': complaint.sla_deadline.isoformat(),
                    'hours_remaining': round(time_remaining, 2)
                }
            ))
        
        # Sort all alerts by urgency (escalated first, then critical, then approaching SLA)
        alert_priority = {'ESCALATED': 0, 'CRITICAL_PRIORITY': 1, 'APPROACHING_SLA': 2}
        alerts.sort(key=lambda a: (
            alert_priority[a['alert_type']],
            -a['complaint']['impact_score']
        ))
        
        logger.info(f"Critical alerts retrieved: {len(alerts)} total alerts")
        
        return jsonify({
            'total_alerts': len(alerts),
            'alerts': alerts,
            'summary': {
                'critical_priority': len(critical_complaints),
                'escalated': len(escalated_complaints),
                'approaching_sla': len(approaching_sla)
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Invalid parameter in alerts request: {e}")
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        logger.error(f"Error generating critical alerts: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate critical alerts'}), 500


@admin_bp.route('/feedback/training-data', methods=['GET'])
@jwt_required()
@require_admin
def export_training_data():
    """
    Export feedback data for ML model retraining.
    
    Collects all feedback with associated complaint data for use in
    improving the ML classifier and priority prediction models.
    
    Authorization: Admin only.
    
    Requirements: 13.4, 15.3
    
    Query Parameters:
        - format (optional): 'json' or 'csv' (default: 'json')
    
    Returns:
        200: Training data exported successfully
        401: Unauthorized
        500: Server error
    """
    try:
        from flask import request
        
        # Get format parameter (default to json)
        export_format = request.args.get('format', 'json').lower()
        
        # Collect training data
        feedback_service = get_feedback_service()
        training_data = feedback_service.collect_training_data()
        
        # Remove PII from training data (Requirements: 15.5)
        anonymized_training_data = remove_pii_from_analytics(training_data)
        
        logger.info(f"Exporting {len(anonymized_training_data)} training data points in {export_format} format")
        
        if export_format == 'csv':
            # Export as CSV
            if not anonymized_training_data:
                return jsonify({'message': 'No training data available'}), 200
            
            # Create CSV in memory
            output = io.StringIO()
            
            # Get field names from first data point
            fieldnames = list(anonymized_training_data[0].keys())
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for data_point in anonymized_training_data:
                # Convert lists to strings for CSV
                row = {}
                for key, value in data_point.items():
                    if isinstance(value, list):
                        row[key] = ','.join(str(v) for v in value)
                    else:
                        row[key] = value
                writer.writerow(row)
            
            # Create response with CSV content
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=training_data.csv'
            
            return response
        else:
            # Export as JSON (default)
            return jsonify({
                'total_records': len(anonymized_training_data),
                'training_data': anonymized_training_data,
                'privacy_note': 'PII has been removed from training data for privacy protection'
            }), 200
        
    except Exception as e:
        logger.error(f"Error exporting training data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to export training data'}), 500
