#!/usr/bin/env python3
"""
Gmail OAuth Setup Script for LegalSaathi
This script helps you set up Gmail OAuth credentials
"""

import os
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# OAuth 2.0 scopes for Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_oauth_credentials():
    """Set up Gmail OAuth credentials"""
    
    print("=" * 60)
    print("Gmail OAuth Setup for LegalSaathi")
    print("=" * 60)
    
    # Check if client secrets file exists
    client_secrets_file = 'gmail_client_secrets.json'
    
    if not os.path.exists(client_secrets_file):
        print(f"\n❌ {client_secrets_file} not found!")
        print("\n📋 First, you need to create OAuth credentials:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project or select existing project")
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API' and enable it")
        print("4. Create OAuth credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Choose 'Desktop application'")
        print("   - Name it 'LegalSaathi Gmail'")
        print("   - Download the JSON file")
        print(f"5. Rename the downloaded file to '{client_secrets_file}'")
        print(f"6. Place it in this directory: {os.getcwd()}")
        print("\n🔄 Run this script again after completing these steps.")
        return False
    
    try:
        # Create the flow using the client secrets file
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=SCOPES
        )
        
        # Set up the redirect URI for desktop app
        flow.redirect_uri = 'http://localhost:8080'
        
        # Get the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print(f"\n🌐 Please visit this URL to authorize the application:")
        print(f"{auth_url}")
        
        print(f"\n📋 After authorization, you'll be redirected to localhost:8080")
        print(f"📋 Copy the ENTIRE URL from your browser's address bar and paste it here:")
        
        # Get the authorization response
        authorization_response = input("\nPaste the full redirect URL here: ").strip()
        
        # Exchange the authorization code for credentials
        flow.fetch_token(authorization_response=authorization_response)
        
        # Get the credentials
        credentials = flow.credentials
        
        # Create the credentials dictionary
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'type': 'authorized_user'
        }
        
        # Save credentials to file
        with open('gmail_oauth_credentials.json', 'w') as f:
            json.dump(creds_dict, f, indent=2)
        
        print("\n✅ OAuth credentials saved to 'gmail_oauth_credentials.json'")
        
        # Update .env file
        creds_json = json.dumps(creds_dict)
        print(f"\n📝 Add this to your .env file:")
        print(f"GMAIL_OAUTH_CREDENTIALS='{creds_json}'")
        
        # Test the credentials
        print(f"\n🧪 Testing credentials...")
        test_credentials(credentials)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up OAuth: {e}")
        return False

def test_credentials(credentials):
    """Test the OAuth credentials"""
    try:
        from googleapiclient.discovery import build
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Test by getting user profile
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        
        print(f"✅ OAuth credentials working!")
        print(f"✅ Authorized email: {email}")
        
    except Exception as e:
        print(f"⚠️  Credentials saved but test failed: {e}")

if __name__ == "__main__":
    setup_oauth_credentials()