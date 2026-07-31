"""
Notification Service for the Grievance Prioritization System.
Handles SMS, email, and push notifications for various events.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels."""
    
    def __init__(self, app=None):
        """Initialize notification service with optional Flask app."""
        self.twilio_client = None
        self.sendgrid_client = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app configuration."""
        # Initialize Twilio client
        twilio_sid = app.config.get('TWILIO_ACCOUNT_SID')
        twilio_token = app.config.get('TWILIO_AUTH_TOKEN')
        
        if twilio_sid and twilio_token:
            try:
                self.twilio_client = Client(twilio_sid, twilio_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not configured")
        
        # Initialize SendGrid client
        sendgrid_key = app.config.get('SENDGRID_API_KEY')
        
        if sendgrid_key:
            try:
                self.sendgrid_client = SendGridAPIClient(sendgrid_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
        else:
            logger.warning("SendGrid API key not configured")
    
    def send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS notification.
        
        Args:
            phone: Recipient phone number (E.164 format)
            message: SMS message content
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.warning("Twilio client not initialized, skipping SMS")
            return False
        
        try:
            twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            if not twilio_phone:
                logger.error("Twilio phone number not configured")
                return False
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone
            )
            
            logger.info(f"SMS sent successfully to {phone}, SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False
    
    def send_email(self, email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email notification.
        
        Args:
            email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.warning("SendGrid client not initialized, skipping email")
            return False
        
        try:
            sender_email = current_app.config.get('SENDER_EMAIL', 'noreply@grievance.gov')
            
            message = Mail(
                from_email=sender_email,
                to_emails=email,
                subject=subject,
                plain_text_content=body,
                html_content=html_body or body
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {email}")
                return True
            else:
                logger.error(f"Failed to send email to {email}, status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False
    
    def send_push_notification(self, user_id: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send push notification (placeholder for mobile app integration).
        
        Args:
            user_id: User ID to send notification to
            message: Notification message
            data: Optional additional data payload
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Placeholder for future mobile app integration (Firebase Cloud Messaging, etc.)
        logger.info(f"Push notification placeholder called for user {user_id}: {message}")
        
        # In production, this would integrate with FCM, APNs, or similar service
        # For now, we just log the notification
        return True


# Notification templates
class NotificationTemplates:
    """Templates for various notification types."""
    
    @staticmethod
    def complaint_submitted(complaint_id: str, priority: str, tracking_url: str) -> Dict[str, str]:
        """Template for complaint submission confirmation."""
        return {
            'sms': f"Your complaint #{complaint_id} has been received. Priority: {priority}. Track status at {tracking_url}",
            'email_subject': f"Complaint #{complaint_id} Received",
            'email_body': f"""Dear Citizen,

Your complaint has been successfully submitted and registered in our system.

Complaint ID: {complaint_id}
Priority Level: {priority}
Tracking URL: {tracking_url}

You will receive updates as your complaint progresses through our resolution process.

Thank you for using the Public Grievance System.

Best regards,
Grievance Resolution Team""",
            'email_html': f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c3e50;">Complaint Received</h2>
    <p>Dear Citizen,</p>
    <p>Your complaint has been successfully submitted and registered in our system.</p>
    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
        <p><strong>Complaint ID:</strong> {complaint_id}</p>
        <p><strong>Priority Level:</strong> {priority}</p>
        <p><strong>Tracking URL:</strong> <a href="{tracking_url}">{tracking_url}</a></p>
    </div>
    <p>You will receive updates as your complaint progresses through our resolution process.</p>
    <p>Thank you for using the Public Grievance System.</p>
    <p style="margin-top: 30px;">Best regards,<br>Grievance Resolution Team</p>
</body>
</html>"""
        }
    
    @staticmethod
    def status_change(complaint_id: str, old_status: str, new_status: str) -> Dict[str, str]:
        """Template for complaint status change notification."""
        return {
            'sms': f"Complaint #{complaint_id} status updated: {old_status} → {new_status}",
            'email_subject': f"Complaint #{complaint_id} Status Update",
            'email_body': f"""Dear Citizen,

Your complaint status has been updated.

Complaint ID: {complaint_id}
Previous Status: {old_status}
New Status: {new_status}

You can track your complaint progress at any time through our portal.

Best regards,
Grievance Resolution Team""",
            'email_html': f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c3e50;">Complaint Status Update</h2>
    <p>Dear Citizen,</p>
    <p>Your complaint status has been updated.</p>
    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
        <p><strong>Complaint ID:</strong> {complaint_id}</p>
        <p><strong>Previous Status:</strong> {old_status}</p>
        <p><strong>New Status:</strong> {new_status}</p>
    </div>
    <p>You can track your complaint progress at any time through our portal.</p>
    <p style="margin-top: 30px;">Best regards,<br>Grievance Resolution Team</p>
</body>
</html>"""
        }
    
    @staticmethod
    def officer_assignment(complaint_id: str, priority: str, location: str, category: str) -> Dict[str, str]:
        """Template for officer assignment notification."""
        return {
            'sms': f"New complaint #{complaint_id} assigned. Priority: {priority}. Location: {location}. Category: {category}",
            'email_subject': f"New Complaint Assignment #{complaint_id}",
            'email_body': f"""Dear Officer,

A new complaint has been assigned to you.

Complaint ID: {complaint_id}
Priority Level: {priority}
Category: {category}
Location: {location}

Please review the complaint details and take appropriate action.

Best regards,
Grievance Management System""",
            'email_html': f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c3e50;">New Complaint Assignment</h2>
    <p>Dear Officer,</p>
    <p>A new complaint has been assigned to you.</p>
    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <p><strong>Complaint ID:</strong> {complaint_id}</p>
        <p><strong>Priority Level:</strong> <span style="color: #d9534f; font-weight: bold;">{priority}</span></p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Location:</strong> {location}</p>
    </div>
    <p>Please review the complaint details and take appropriate action.</p>
    <p style="margin-top: 30px;">Best regards,<br>Grievance Management System</p>
</body>
</html>"""
        }
    
    @staticmethod
    def escalation(complaint_id: str, priority: str, reason: str, sla_deadline: str) -> Dict[str, str]:
        """Template for complaint escalation notification."""
        return {
            'sms': f"URGENT: Complaint #{complaint_id} exceeded SLA. Priority: {priority}. Immediate action required.",
            'email_subject': f"URGENT: Complaint #{complaint_id} Escalated",
            'email_body': f"""URGENT NOTIFICATION

Complaint #{complaint_id} has been escalated and requires immediate attention.

Priority Level: {priority}
Escalation Reason: {reason}
Original SLA Deadline: {sla_deadline}

This complaint has exceeded the expected resolution timeframe. Please take immediate action.

Best regards,
Grievance Management System""",
            'email_html': f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #d9534f;">⚠️ URGENT: Complaint Escalated</h2>
    <p><strong>URGENT NOTIFICATION</strong></p>
    <p>Complaint #{complaint_id} has been escalated and requires immediate attention.</p>
    <div style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #d9534f; margin: 20px 0;">
        <p><strong>Complaint ID:</strong> {complaint_id}</p>
        <p><strong>Priority Level:</strong> <span style="color: #d9534f; font-weight: bold;">{priority}</span></p>
        <p><strong>Escalation Reason:</strong> {reason}</p>
        <p><strong>Original SLA Deadline:</strong> {sla_deadline}</p>
    </div>
    <p style="color: #d9534f; font-weight: bold;">This complaint has exceeded the expected resolution timeframe. Please take immediate action.</p>
    <p style="margin-top: 30px;">Best regards,<br>Grievance Management System</p>
</body>
</html>"""
        }
    
    @staticmethod
    def resolution(complaint_id: str, resolution_time: str, feedback_url: str) -> Dict[str, str]:
        """Template for complaint resolution notification."""
        return {
            'sms': f"Complaint #{complaint_id} has been resolved. Resolution time: {resolution_time}. Please provide feedback at {feedback_url}",
            'email_subject': f"Complaint #{complaint_id} Resolved",
            'email_body': f"""Dear Citizen,

We are pleased to inform you that your complaint has been resolved.

Complaint ID: {complaint_id}
Resolution Time: {resolution_time}

We value your feedback. Please take a moment to rate our service at: {feedback_url}

Thank you for using the Public Grievance System.

Best regards,
Grievance Resolution Team""",
            'email_html': f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #28a745;">✓ Complaint Resolved</h2>
    <p>Dear Citizen,</p>
    <p>We are pleased to inform you that your complaint has been resolved.</p>
    <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
        <p><strong>Complaint ID:</strong> {complaint_id}</p>
        <p><strong>Resolution Time:</strong> {resolution_time}</p>
    </div>
    <p>We value your feedback. Please take a moment to rate our service:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{feedback_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Provide Feedback</a>
    </p>
    <p>Thank you for using the Public Grievance System.</p>
    <p style="margin-top: 30px;">Best regards,<br>Grievance Resolution Team</p>
</body>
</html>"""
        }


class NotificationService:
    """Service for sending notifications via multiple channels."""
    
    def __init__(self, app=None):
        """Initialize notification service with optional Flask app."""
        self.twilio_client = None
        self.sendgrid_client = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app configuration."""
        # Initialize Twilio client
        twilio_sid = app.config.get('TWILIO_ACCOUNT_SID')
        twilio_token = app.config.get('TWILIO_AUTH_TOKEN')
        
        if twilio_sid and twilio_token:
            try:
                self.twilio_client = Client(twilio_sid, twilio_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not configured")
        
        # Initialize SendGrid client
        sendgrid_key = app.config.get('SENDGRID_API_KEY')
        
        if sendgrid_key:
            try:
                self.sendgrid_client = SendGridAPIClient(sendgrid_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
        else:
            logger.warning("SendGrid API key not configured")
    
    def send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS notification.
        
        Args:
            phone: Recipient phone number (E.164 format)
            message: SMS message content
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.warning("Twilio client not initialized, skipping SMS")
            return False
        
        try:
            twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            if not twilio_phone:
                logger.error("Twilio phone number not configured")
                return False
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone
            )
            
            logger.info(f"SMS sent successfully to {phone}, SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False
    
    def send_email(self, email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email notification.
        
        Args:
            email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.warning("SendGrid client not initialized, skipping email")
            return False
        
        try:
            sender_email = current_app.config.get('SENDER_EMAIL', 'noreply@grievance.gov')
            
            logger.info(f"Attempting to send email to {email} with subject: {subject}")
            
            message = Mail(
                from_email=sender_email,
                to_emails=email,
                subject=subject,
                plain_text_content=body,
                html_content=html_body or body
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {email}, status: {response.status_code}")
                return True
            else:
                logger.error(f"Failed to send email to {email}, status: {response.status_code}, body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}", exc_info=True)
            return False
    
    def send_push_notification(self, user_id: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send push notification (placeholder for mobile app integration).
        
        Args:
            user_id: User ID to send notification to
            message: Notification message
            data: Optional additional data payload
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Placeholder for future mobile app integration (Firebase Cloud Messaging, etc.)
        logger.info(f"Push notification placeholder called for user {user_id}: {message}")
        
        # In production, this would integrate with FCM, APNs, or similar service
        # For now, we just log the notification
        return True
    
    def notify_complaint_submitted(self, user_phone: str, user_email: str, 
                                   complaint_id: str, priority: str, 
                                   tracking_url: str) -> Dict[str, bool]:
        """
        Send notifications when a complaint is submitted.
        
        Args:
            user_phone: User's phone number
            user_email: User's email address
            complaint_id: Complaint ID
            priority: Priority level
            tracking_url: URL to track complaint
            
        Returns:
            Dictionary with success status for each channel
        """
        template = NotificationTemplates.complaint_submitted(complaint_id, priority, tracking_url)
        
        results = {
            'sms': self.send_sms(user_phone, template['sms']),
            'email': self.send_email(user_email, template['email_subject'], 
                                    template['email_body'], template['email_html']),
            'push': self.send_push_notification(user_email, template['sms'])
        }
        
        logger.info(f"Complaint submitted notifications sent for {complaint_id}: {results}")
        return results
    
    def notify_status_change(self, user_phone: str, user_email: str,
                            complaint_id: str, old_status: str, 
                            new_status: str) -> Dict[str, bool]:
        """
        Send notifications when complaint status changes.
        
        Args:
            user_phone: User's phone number
            user_email: User's email address
            complaint_id: Complaint ID
            old_status: Previous status
            new_status: New status
            
        Returns:
            Dictionary with success status for each channel
        """
        template = NotificationTemplates.status_change(complaint_id, old_status, new_status)
        
        results = {
            'sms': self.send_sms(user_phone, template['sms']),
            'email': self.send_email(user_email, template['email_subject'],
                                    template['email_body'], template['email_html']),
            'push': self.send_push_notification(user_email, template['sms'])
        }
        
        logger.info(f"Status change notifications sent for {complaint_id}: {results}")
        return results
    
    def notify_officer_assignment(self, officer_phone: str, officer_email: str,
                                 complaint_id: str, priority: str,
                                 location: str, category: str) -> Dict[str, bool]:
        """
        Send notifications when complaint is assigned to an officer.
        
        Args:
            officer_phone: Officer's phone number
            officer_email: Officer's email address
            complaint_id: Complaint ID
            priority: Priority level
            location: Complaint location
            category: Complaint category
            
        Returns:
            Dictionary with success status for each channel
        """
        template = NotificationTemplates.officer_assignment(complaint_id, priority, 
                                                           location, category)
        
        results = {
            'sms': self.send_sms(officer_phone, template['sms']),
            'email': self.send_email(officer_email, template['email_subject'],
                                    template['email_body'], template['email_html']),
            'push': self.send_push_notification(officer_email, template['sms'])
        }
        
        logger.info(f"Officer assignment notifications sent for {complaint_id}: {results}")
        return results
    
    def notify_escalation(self, authority_phone: str, authority_email: str,
                         complaint_id: str, priority: str,
                         reason: str, sla_deadline: str) -> Dict[str, bool]:
        """
        Send notifications when complaint is escalated.
        
        Args:
            authority_phone: Authority's phone number
            authority_email: Authority's email address
            complaint_id: Complaint ID
            priority: Priority level
            reason: Escalation reason
            sla_deadline: Original SLA deadline
            
        Returns:
            Dictionary with success status for each channel
        """
        template = NotificationTemplates.escalation(complaint_id, priority, 
                                                   reason, sla_deadline)
        
        results = {
            'sms': self.send_sms(authority_phone, template['sms']),
            'email': self.send_email(authority_email, template['email_subject'],
                                    template['email_body'], template['email_html']),
            'push': self.send_push_notification(authority_email, template['sms'])
        }
        
        logger.info(f"Escalation notifications sent for {complaint_id}: {results}")
        return results
    
    def notify_resolution(self, user_phone: str, user_email: str,
                         complaint_id: str, resolution_time: str,
                         feedback_url: str) -> Dict[str, bool]:
        """
        Send notifications when complaint is resolved.
        
        Args:
            user_phone: User's phone number
            user_email: User's email address
            complaint_id: Complaint ID
            resolution_time: Time taken to resolve
            feedback_url: URL to provide feedback
            
        Returns:
            Dictionary with success status for each channel
        """
        logger.info(f"Sending resolution notification for complaint {complaint_id} to {user_email}")
        
        template = NotificationTemplates.resolution(complaint_id, resolution_time, 
                                                   feedback_url)
        
        results = {
            'sms': self.send_sms(user_phone, template['sms']),
            'email': self.send_email(user_email, template['email_subject'],
                                    template['email_body'], template['email_html']),
            'push': self.send_push_notification(user_email, template['sms'])
        }
        
        logger.info(f"Resolution notifications sent for {complaint_id}: {results}")
        return results


# Global notification service instance
notification_service = NotificationService()
