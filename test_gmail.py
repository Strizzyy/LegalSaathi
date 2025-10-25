#!/usr/bin/env python3
"""
Simple Gmail SMTP test script
Run this to test your Gmail App Password configuration
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_connection():
    """Test Gmail SMTP connection and authentication"""
    
    # Get credentials from environment
    sender_email = os.getenv('GMAIL_SENDER_EMAIL')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')
    sender_name = os.getenv('GMAIL_SENDER_NAME', 'LegalSaathi Test')
    
    print(f"Testing Gmail SMTP connection...")
    print(f"Sender Email: {sender_email}")
    print(f"Sender Name: {sender_name}")
    print(f"App Password Length: {len(sender_password) if sender_password else 0} characters")
    
    if not sender_email or not sender_password:
        print("❌ ERROR: GMAIL_SENDER_EMAIL or GMAIL_APP_PASSWORD not set in .env file")
        return False
    
    # Check if password looks like an app password (16 chars, no spaces when cleaned)
    clean_password = sender_password.replace(' ', '')
    if len(clean_password) != 16:
        print(f"⚠️  WARNING: App password should be 16 characters (got {len(clean_password)})")
        print("   Make sure you're using a Gmail App Password, not your regular password")
    
    try:
        # Test connection
        print("\n🔄 Testing SMTP connection...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.set_debuglevel(1)  # Show detailed SMTP conversation
            print("✅ Connected to Gmail SMTP server")
            
            print("🔄 Starting TLS encryption...")
            server.starttls()
            print("✅ TLS encryption started")
            
            print("🔄 Attempting authentication...")
            server.login(sender_email, sender_password)
            print("✅ Authentication successful!")
            
            # Send a test email to yourself
            test_email = input(f"\nEnter email address to send test email to (or press Enter to skip): ").strip()
            
            if test_email:
                print(f"🔄 Sending test email to {test_email}...")
                
                msg = MIMEMultipart()
                msg['From'] = f"{sender_name} <{sender_email}>"
                msg['To'] = test_email
                msg['Subject'] = "LegalSaathi Gmail Test - Success!"
                
                body = """
Hello!

This is a test email from LegalSaathi to verify that Gmail SMTP is working correctly.

If you received this email, your Gmail App Password configuration is working perfectly!

Best regards,
LegalSaathi Team
                """
                
                msg.attach(MIMEText(body, 'plain'))
                server.send_message(msg)
                print("✅ Test email sent successfully!")
            
        print("\n🎉 Gmail SMTP configuration is working correctly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION ERROR: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure 2-Factor Authentication is enabled on your Gmail account")
        print("2. Generate a new App Password:")
        print("   - Go to https://myaccount.google.com/security")
        print("   - Click 'App passwords'")
        print("   - Select 'Mail' and 'Other (custom name)'")
        print("   - Enter 'LegalSaathi' as the name")
        print("   - Copy the 16-character password (format: abcd efgh ijkl mnop)")
        print("3. Update GMAIL_APP_PASSWORD in your .env file")
        print("4. Make sure you're using the App Password, not your regular Gmail password")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP ERROR: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LegalSaathi Gmail SMTP Configuration Test")
    print("=" * 60)
    
    success = test_gmail_connection()
    
    if success:
        print("\n✅ Your Gmail configuration is ready for LegalSaathi!")
    else:
        print("\n❌ Please fix the configuration issues above and try again.")
    
    print("\n" + "=" * 60)