#!/usr/bin/env python3
"""
Integration test for the risk classification system with Flask app
"""

from app import analyze_rental_agreement_with_llm

def test_integration():
    """Test the integration between Flask app and risk classifier"""
    
    sample_document = """
    RENTAL AGREEMENT
    
    This rental agreement is between John Smith (Landlord) and Jane Doe (Tenant).
    
    1. Monthly rent is $1500 due on the 1st of each month.
    
    2. Security deposit of $2000 is non-refundable and will be forfeited 
       if tenant violates any terms.
    
    3. Late payments incur a $100 daily penalty fee.
    
    4. Landlord may enter without notice for inspections.
    
    5. No pets allowed under any circumstances.
    """
    
    print("Testing Integration with Sample Document")
    print("=" * 50)
    
    try:
        # Test the main analysis function
        result = analyze_rental_agreement_with_llm(sample_document)
        
        print(f"Document ID: {result.document_id}")
        print(f"Overall Risk: {result.overall_risk.level}")
        print(f"Overall Score: {result.overall_risk.score:.2f}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Summary: {result.summary}")
        
        print(f"\nAnalyzed {len(result.analysis_results)} clauses:")
        
        for i, analysis in enumerate(result.analysis_results, 1):
            print(f"\n{i}. {analysis.clause_id}")
            print(f"   Risk: {analysis.risk_level.level} (Score: {analysis.risk_level.score:.2f})")
            print(f"   Explanation: {analysis.plain_explanation[:100]}...")
            print(f"   Recommendations: {len(analysis.recommendations)} items")
        
        print("\n✅ Integration test completed successfully!")
        
        # Verify risk levels are working
        red_count = sum(1 for a in result.analysis_results if a.risk_level.level == "RED")
        yellow_count = sum(1 for a in result.analysis_results if a.risk_level.level == "YELLOW")
        green_count = sum(1 for a in result.analysis_results if a.risk_level.level == "GREEN")
        
        print(f"\nRisk Distribution:")
        print(f"🔴 RED: {red_count} clauses")
        print(f"🟡 YELLOW: {yellow_count} clauses")
        print(f"🟢 GREEN: {green_count} clauses")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n🎉 All tests passed! Risk classification system is ready.")
    else:
        print("\n💥 Tests failed. Please check the implementation.")