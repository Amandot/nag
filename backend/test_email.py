"""
Test script to verify email notification setup.
"""
from app import create_app
from services.notification_service import notification_service
import sys

def test_email_configuration():
    """Test if SendGrid is properly configured."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Email Configuration Test")
        print("=" * 60)
        
        # Check if SendGrid API key is configured
        api_key = app.config.get('SENDGRID_API_KEY')
        sender_email = app.config.get('SENDER_EMAIL')
        
        print(f"\n1. Configuration Check:")
        print(f"   SendGrid API Key: {'✓ Configured' if api_key else '✗ Not configured'}")
        if api_key:
            print(f"   API Key starts with 'SG.': {'✓ Yes' if api_key.startswith('SG.') else '✗ No (Invalid format!)'}")
            print(f"   API Key length: {len(api_key)} characters")
        print(f"   Sender Email: {sender_email}")
        
        # Check if SendGrid client is initialized
        print(f"\n2. SendGrid Client:")
        print(f"   Client initialized: {'✓ Yes' if notification_service.sendgrid_client else '✗ No'}")
        
        if not notification_service.sendgrid_client:
            print("\n❌ SendGrid client not initialized!")
            print("   Please check your SENDGRID_API_KEY in the .env file.")
            return False
        
        # Ask user if they want to send a test email
        print("\n3. Test Email:")
        test_email = input("   Enter email address to send test email (or press Enter to skip): ").strip()
        
        if test_email:
            print(f"   Sending test email to {test_email}...")
            
            result = notification_service.send_email(
                email=test_email,
                subject='Test Email from Grievance System',
                body='This is a test email to verify SendGrid integration works correctly.',
                html_body='''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #28a745;">✓ Email Test Successful!</h2>
                    <p>If you're reading this, your SendGrid integration is working correctly.</p>
                    <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <p><strong>Configuration Status:</strong> ✓ Working</p>
                        <p><strong>Sender Email:</strong> ''' + sender_email + '''</p>
                    </div>
                    <p>You can now receive complaint resolution notifications.</p>
                    <p style="margin-top: 30px;">Best regards,<br>Grievance System</p>
                </body>
                </html>
                '''
            )
            
            if result:
                print(f"   ✓ Test email sent successfully!")
                print(f"   Check your inbox at {test_email}")
            else:
                print(f"   ✗ Failed to send test email")
                print(f"   Check the logs for more details")
                return False
        else:
            print("   Skipped test email")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        return True


def test_resolution_notification():
    """Test the resolution notification template."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 60)
        print("Resolution Notification Test")
        print("=" * 60)
        
        test_email = input("\nEnter email address to send test resolution notification: ").strip()
        
        if not test_email:
            print("No email provided, skipping test")
            return
        
        print(f"\nSending resolution notification to {test_email}...")
        
        result = notification_service.notify_resolution(
            user_phone='+1234567890',  # Dummy phone
            user_email=test_email,
            complaint_id='TEST-12345',
            resolution_time='2 days, 3 hours',
            feedback_url='http://localhost:3000/complaint/TEST-12345/feedback'
        )
        
        print(f"\nResults:")
        print(f"  SMS: {'✓ Sent' if result['sms'] else '✗ Failed (Twilio not configured)'}")
        print(f"  Email: {'✓ Sent' if result['email'] else '✗ Failed'}")
        print(f"  Push: {'✓ Sent' if result['push'] else '✗ Failed'}")
        
        if result['email']:
            print(f"\n✓ Resolution notification sent successfully!")
            print(f"  Check your inbox at {test_email}")
        else:
            print(f"\n✗ Failed to send resolution notification")
            print(f"  Check the logs for more details")


if __name__ == '__main__':
    print("\nGrievance System - Email Notification Test\n")
    
    # Test configuration
    config_ok = test_email_configuration()
    
    if config_ok:
        # Ask if user wants to test resolution notification
        print("\n")
        test_resolution = input("Do you want to test the resolution notification? (y/n): ").strip().lower()
        
        if test_resolution == 'y':
            test_resolution_notification()
    else:
        print("\n❌ Configuration test failed. Please fix the issues above before testing notifications.")
        sys.exit(1)

