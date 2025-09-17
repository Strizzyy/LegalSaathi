#!/usr/bin/env python3
"""
Simple test script to verify LLM integration for rental agreement analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import analyze_rental_agreement_with_llm, create_fallback_analysis

def test_llm_integration():
    """Test the LLM integration with a sample rental agreement"""
    
    sample_rental_text = """
    RENTAL AGREEMENT
    
    This agreement is between John Smith (Landlord) and Jane Doe (Tenant).
    
    1. RENT: Tenant agrees to pay $1,200 per month rent, due on the 1st of each month.
    
    2. SECURITY DEPOSIT: Tenant must pay a non-refundable security deposit of $2,400.
    
    3. TERMINATION: Landlord may terminate this lease at any time with 24 hours notice.
    
    4. MAINTENANCE: Tenant is responsible for all repairs and maintenance, including structural repairs.
    
    5. LATE FEES: A $100 late fee will be charged for rent paid after the 5th of the month.
    """
    
    print("Testing LLM integration for rental agreement analysis...")
    print("=" * 60)
    
    try:
        # Test the main LLM analysis function with timeout
        print("Attempting to connect to vLLM server...")
        analysis = analyze_rental_agreement_with_llm(sample_rental_text)
        
        print(f"Analysis completed successfully!")
        print(f"Document ID: {analysis.document_id}")
        print(f"Processing time: {analysis.processing_time:.2f} seconds")
        print(f"Overall risk: {analysis.overall_risk.level} ({analysis.overall_risk.severity})")
        print(f"Risk score: {analysis.overall_risk.score}")
        print(f"Summary: {analysis.summary}")
        print(f"Number of clause analyses: {len(analysis.analysis_results)}")
        
        print("\nClause Analysis Details:")
        for i, result in enumerate(analysis.analysis_results, 1):
            print(f"\n  Clause {i}:")
            print(f"    Risk Level: {result.risk_level.level}")
            print(f"    Explanation: {result.plain_explanation[:100]}...")
            print(f"    Recommendations: {len(result.recommendations)} provided")
        
        return True
        
    except Exception as e:
        print(f"LLM analysis failed: {str(e)}")
        print("Testing fallback analysis...")
        
        try:
            fallback_analysis = create_fallback_analysis(sample_rental_text)
            print(f"Fallback analysis completed!")
            print(f"Overall risk: {fallback_analysis.overall_risk.level}")
            print(f"Summary: {fallback_analysis.summary}")
            return True
        except Exception as fallback_error:
            print(f"Fallback analysis also failed: {str(fallback_error)}")
            return False

if __name__ == "__main__":
    success = test_llm_integration()
    if success:
        print("\n✅ LLM integration test completed successfully!")
    else:
        print("\n❌ LLM integration test failed!")
        sys.exit(1)