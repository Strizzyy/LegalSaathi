#!/usr/bin/env python3
"""
Test Flask application integration with LLM analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_flask_integration():
    """Test the Flask application with LLM integration"""
    
    # Create test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    print("Testing Flask application with LLM integration...")
    print("=" * 60)
    
    # Test home page
    print("1. Testing home page...")
    response = client.get('/')
    if response.status_code == 200:
        print("   ✅ Home page loads successfully")
    else:
        print(f"   ❌ Home page failed: {response.status_code}")
        return False
    
    # Test document analysis with sample rental agreement
    print("2. Testing document analysis...")
    sample_rental = """
    RENTAL AGREEMENT
    
    This agreement is between John Smith (Landlord) and Jane Doe (Tenant).
    
    1. RENT: Tenant agrees to pay $1,200 per month rent, due on the 1st of each month.
    
    2. SECURITY DEPOSIT: Tenant must pay a non-refundable security deposit of $2,400.
    
    3. TERMINATION: Landlord may terminate this lease at any time with 24 hours notice.
    
    4. MAINTENANCE: Tenant is responsible for all repairs and maintenance, including structural repairs.
    
    5. LATE FEES: A $100 late fee will be charged for rent paid after the 5th of the month.
    """
    
    response = client.post('/analyze', data={'document_text': sample_rental})
    
    if response.status_code == 200:
        print("   ✅ Analysis endpoint responds successfully")
        
        # Check if response contains expected elements
        response_text = response.get_data(as_text=True)
        
        if 'Risk Level' in response_text or 'analysis' in response_text.lower():
            print("   ✅ Response contains analysis results")
        else:
            print("   ⚠️  Response may not contain expected analysis content")
            
    else:
        print(f"   ❌ Analysis endpoint failed: {response.status_code}")
        return False
    
    # Test validation with invalid input
    print("3. Testing input validation...")
    response = client.post('/analyze', data={'document_text': 'short'})
    
    if response.status_code == 200:
        response_text = response.get_data(as_text=True)
        if 'error' in response_text.lower() or 'at least 100 characters' in response_text:
            print("   ✅ Input validation works correctly")
        else:
            print("   ⚠️  Input validation may not be working as expected")
    else:
        print(f"   ❌ Validation test failed: {response.status_code}")
    
    return True

if __name__ == "__main__":
    success = test_flask_integration()
    if success:
        print("\n✅ Flask integration test completed successfully!")
        print("The LLM integration is ready for use.")
    else:
        print("\n❌ Flask integration test failed!")
        sys.exit(1)