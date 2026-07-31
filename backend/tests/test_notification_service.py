"""
Unit tests for notification service.

Tests notification sending with mocked external services and notification triggers.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.notification_service import NotificationService, NotificationTemplates
from flask import Flask


@pytest.fixture
def app():
    """Create a test Flask app."""
    app = Flask(__name__)
    app.config['TWILIO_ACCOUNT_SID'] = 'test_sid'
    app.config['TWILIO_AUTH_TOKEN'] = 'test_token'
    app.config['TWILIO_PHONE_NUMBER'] = '+1234567890'
    app.config['SENDGRID_API_KEY'] = 'test_sendgrid_key'
    app.config['SENDER_EMAIL'] = 'test@grievance.gov'
    return app


@pytest.fixture
def notification_service(app):
    """Create a notification service instance with mocked clients."""
    service = NotificationService()
    
    # Mock Twilio client
    service.twilio_client = Mock()
    service.twilio_client.messages = Mock()
    
    # Mock SendGrid client
    service.sendgrid_client = Mock()
    
    return service


@pytest.fixture
def notification_templates(app):
    """Create a notification templates instance with mocked NotificationService."""
    templates = NotificationTemplates()
    
    # Mock the notification service
    templates.twilio_client = Mock()
    templates.twilio_client.messages = Mock()
    templates.sendgrid_client = Mock()
    
    # Add the send methods to templates (they're actually on NotificationService)
    templates.send_sms = Mock(return_value=True)
    templates.send_email = Mock(return_value=True)
    templates.send_push_notification = Mock(return_value=True)
    
    return templates


class TestSMSSending:
    """Test SMS notification sending.
    
    Requirements: 11.1
    """
    
    def test_send_sms_success(self, app, notification_service):
        """Test successful SMS sending."""
        with app.app_context():
            # Mock successful message creation
            mock_message = Mock()
            mock_message.sid = 'SM123456'
            notification_service.twilio_client.messages.create.return_value = mock_message
            
            result = notification_service.send_sms('+1234567890', 'Test message')
            
            assert result is True
            notification_service.twilio_client.messages.create.assert_called_once()
            call_args = notification_service.twilio_client.messages.create.call_args
            assert call_args.kwargs['body'] == 'Test message'
            assert call_args.kwargs['to'] == '+1234567890'
    
    def test_send_sms_failure(self, app, notification_service):
        """Test SMS sending failure."""
        with app.app_context():
            # Mock exception during message creation
            notification_service.twilio_client.messages.create.side_effect = Exception('Network error')
            
            result = notification_service.send_sms('+1234567890', 'Test message')
            
            assert result is False
    
    def test_send_sms_without_client(self, app):
        """Test SMS sending when Twilio client is not initialized."""
        with app.app_context():
            service = NotificationService()
            service.twilio_client = None
            
            result = service.send_sms('+1234567890', 'Test message')
            
            assert result is False


class TestEmailSending:
    """Test email notification sending.
    
    Requirements: 11.1
    """
    
    def test_send_email_success(self, app, notification_service):
        """Test successful email sending."""
        with app.app_context():
            # Mock successful email sending
            mock_response = Mock()
            mock_response.status_code = 202
            notification_service.sendgrid_client.send.return_value = mock_response
            
            result = notification_service.send_email(
                'test@example.com',
                'Test Subject',
                'Test body',
                '<html>Test HTML</html>'
            )
            
            assert result is True
            notification_service.sendgrid_client.send.assert_called_once()
    
    def test_send_email_failure(self, app, notification_service):
        """Test email sending failure."""
        with app.app_context():
            # Mock exception during email sending
            notification_service.sendgrid_client.send.side_effect = Exception('API error')
            
            result = notification_service.send_email(
                'test@example.com',
                'Test Subject',
                'Test body'
            )
            
            assert result is False
    
    def test_send_email_without_client(self, app):
        """Test email sending when SendGrid client is not initialized."""
        with app.app_context():
            service = NotificationService()
            service.sendgrid_client = None
            
            result = service.send_email('test@example.com', 'Subject', 'Body')
            
            assert result is False
    
    def test_send_email_with_failed_status_code(self, app, notification_service):
        """Test email sending with failed status code."""
        with app.app_context():
            # Mock failed response
            mock_response = Mock()
            mock_response.status_code = 400
            notification_service.sendgrid_client.send.return_value = mock_response
            
            result = notification_service.send_email(
                'test@example.com',
                'Test Subject',
                'Test body'
            )
            
            assert result is False


class TestPushNotifications:
    """Test push notification sending.
    
    Requirements: 11.1
    """
    
    def test_send_push_notification(self, notification_service):
        """Test push notification (placeholder implementation)."""
        result = notification_service.send_push_notification(
            'user123',
            'Test notification',
            {'key': 'value'}
        )
        
        # Push notifications are placeholder, should always return True
        assert result is True


class TestComplaintSubmittedNotification:
    """Test complaint submission notification trigger.
    
    Requirements: 11.1
    """
    
    def test_notify_complaint_submitted_all_channels(self, app, notification_templates):
        """Test complaint submitted notification sends to all channels."""
        with app.app_context():
            results = notification_templates.notify_complaint_submitted(
                user_phone='+1234567890',
                user_email='user@example.com',
                complaint_id='C123',
                priority='High',
                tracking_url='http://example.com/track/C123'
            )
            
            assert results['sms'] is True
            assert results['email'] is True
            assert results['push'] is True
            
            # Verify methods were called
            notification_templates.send_sms.assert_called_once()
            notification_templates.send_email.assert_called_once()
            notification_templates.send_push_notification.assert_called_once()
    
    def test_notify_complaint_submitted_partial_failure(self, app, notification_templates):
        """Test complaint submitted notification with partial channel failure."""
        with app.app_context():
            # Mock SMS failure, email success
            notification_templates.send_sms.return_value = False
            notification_templates.send_email.return_value = True
            notification_templates.send_push_notification.return_value = True
            
            results = notification_templates.notify_complaint_submitted(
                user_phone='+1234567890',
                user_email='user@example.com',
                complaint_id='C123',
                priority='High',
                tracking_url='http://example.com/track/C123'
            )
            
            assert results['sms'] is False
            assert results['email'] is True
            assert results['push'] is True


class TestStatusChangeNotification:
    """Test status change notification trigger.
    
    Requirements: 11.2
    """
    
    def test_notify_status_change(self, app, notification_templates):
        """Test status change notification sends to all channels."""
        with app.app_context():
            results = notification_templates.notify_status_change(
                user_phone='+1234567890',
                user_email='user@example.com',
                complaint_id='C123',
                old_status='Submitted',
                new_status='Assigned'
            )
            
            assert results['sms'] is True
            assert results['email'] is True
            assert results['push'] is True
            
            # Verify methods were called
            notification_templates.send_sms.assert_called_once()
            notification_templates.send_email.assert_called_once()
            notification_templates.send_push_notification.assert_called_once()


class TestOfficerAssignmentNotification:
    """Test officer assignment notification trigger.
    
    Requirements: 11.3
    """
    
    def test_notify_officer_assignment(self, app, notification_templates):
        """Test officer assignment notification sends to all channels."""
        with app.app_context():
            results = notification_templates.notify_officer_assignment(
                officer_phone='+1234567890',
                officer_email='officer@example.com',
                complaint_id='C123',
                priority='Critical',
                location='123 Main St',
                category='Water Supply'
            )
            
            assert results['sms'] is True
            assert results['email'] is True
            assert results['push'] is True
            
            # Verify methods were called
            notification_templates.send_sms.assert_called_once()
            notification_templates.send_email.assert_called_once()
            notification_templates.send_push_notification.assert_called_once()


class TestEscalationNotification:
    """Test escalation notification trigger.
    
    Requirements: 11.4
    """
    
    def test_notify_escalation(self, app, notification_templates):
        """Test escalation notification sends to all channels."""
        with app.app_context():
            results = notification_templates.notify_escalation(
                authority_phone='+1234567890',
                authority_email='authority@example.com',
                complaint_id='C123',
                priority='Critical',
                reason='SLA exceeded',
                sla_deadline='2024-01-15 10:00:00'
            )
            
            assert results['sms'] is True
            assert results['email'] is True
            assert results['push'] is True
            
            # Verify methods were called
            notification_templates.send_sms.assert_called_once()
            notification_templates.send_email.assert_called_once()
            notification_templates.send_push_notification.assert_called_once()


class TestResolutionNotification:
    """Test resolution notification trigger.
    
    Requirements: 11.5
    """
    
    def test_notify_resolution(self, app, notification_templates):
        """Test resolution notification sends to all channels."""
        with app.app_context():
            results = notification_templates.notify_resolution(
                user_phone='+1234567890',
                user_email='user@example.com',
                complaint_id='C123',
                resolution_time='2 hours',
                feedback_url='http://example.com/feedback/C123'
            )
            
            assert results['sms'] is True
            assert results['email'] is True
            assert results['push'] is True
            
            # Verify methods were called
            notification_templates.send_sms.assert_called_once()
            notification_templates.send_email.assert_called_once()
            notification_templates.send_push_notification.assert_called_once()


class TestNotificationTemplates:
    """Test notification template generation.
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
    """
    
    def test_complaint_submitted_template(self):
        """Test complaint submitted template contains required fields."""
        template = NotificationTemplates.complaint_submitted(
            'C123', 'High', 'http://example.com/track/C123'
        )
        
        assert 'sms' in template
        assert 'email_subject' in template
        assert 'email_body' in template
        assert 'email_html' in template
        
        assert 'C123' in template['sms']
        assert 'High' in template['sms']
        assert 'http://example.com/track/C123' in template['sms']
    
    def test_status_change_template(self):
        """Test status change template contains required fields."""
        template = NotificationTemplates.status_change('C123', 'Submitted', 'Assigned')
        
        assert 'sms' in template
        assert 'email_subject' in template
        assert 'email_body' in template
        assert 'email_html' in template
        
        assert 'C123' in template['sms']
        assert 'Submitted' in template['sms']
        assert 'Assigned' in template['sms']
    
    def test_officer_assignment_template(self):
        """Test officer assignment template contains required fields."""
        template = NotificationTemplates.officer_assignment(
            'C123', 'Critical', '123 Main St', 'Water Supply'
        )
        
        assert 'sms' in template
        assert 'email_subject' in template
        assert 'email_body' in template
        assert 'email_html' in template
        
        assert 'C123' in template['sms']
        assert 'Critical' in template['sms']
        assert '123 Main St' in template['sms']
        assert 'Water Supply' in template['sms']
    
    def test_escalation_template(self):
        """Test escalation template contains required fields."""
        template = NotificationTemplates.escalation(
            'C123', 'Critical', 'SLA exceeded', '2024-01-15 10:00:00'
        )
        
        assert 'sms' in template
        assert 'email_subject' in template
        assert 'email_body' in template
        assert 'email_html' in template
        
        assert 'URGENT' in template['sms']
        assert 'C123' in template['sms']
        assert 'exceeded SLA' in template['sms']
    
    def test_resolution_template(self):
        """Test resolution template contains required fields."""
        template = NotificationTemplates.resolution(
            'C123', '2 hours', 'http://example.com/feedback/C123'
        )
        
        assert 'sms' in template
        assert 'email_subject' in template
        assert 'email_body' in template
        assert 'email_html' in template
        
        assert 'C123' in template['sms']
        assert 'resolved' in template['sms'].lower()
        assert '2 hours' in template['sms']
        assert 'http://example.com/feedback/C123' in template['sms']
