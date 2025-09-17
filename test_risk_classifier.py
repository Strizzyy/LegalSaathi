#!/usr/bin/env python3
"""
Test script for the risk classification system
"""

from risk_classifier import RiskClassifier, classify_document_risk

def test_risk_classifier():
    """Test the risk classification system with sample clauses"""
    
    # Test cases with different risk levels
    test_clauses = [
        {
            "text": "The security deposit is non-refundable and will be forfeited upon any violation of this agreement.",
            "expected_risk": "RED",
            "description": "Non-refundable deposit clause"
        },
        {
            "text": "Late rent payments will incur a fee of $500 per day after the due date.",
            "expected_risk": "YELLOW", 
            "description": "Excessive late fee clause"
        },
        {
            "text": "The monthly rent is $1200 due on the first day of each month.",
            "expected_risk": "GREEN",
            "description": "Standard rent clause"
        },
        {
            "text": "Tenant waives all rights to notice and landlord may enter at any time without permission.",
            "expected_risk": "RED",
            "description": "Rights waiver and no-notice entry"
        }
    ]
    
    print("Testing Risk Classification System")
    print("=" * 50)
    
    classifier = RiskClassifier()
    
    for i, test_case in enumerate(test_clauses, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Text: {test_case['text']}")
        print(f"Expected Risk: {test_case['expected_risk']}")
        
        try:
            assessment = classifier.classify_risk_level(test_case['text'])
            print(f"Actual Risk: {assessment.level.value}")
            print(f"Risk Score: {assessment.score:.2f}")
            print(f"Confidence: {assessment.confidence:.2f}")
            print(f"Reasons: {', '.join(assessment.reasons[:2])}")
            
            # Check if assessment matches expectation
            if assessment.level.value == test_case['expected_risk']:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)
    
    classifier.close()

def test_document_classification():
    """Test full document risk classification"""
    
    sample_document = """
    RENTAL AGREEMENT
    
    This agreement is between John Doe (Landlord) and Jane Smith (Tenant).
    
    1. The monthly rent is $1500 due on the 1st of each month.
    
    2. The security deposit of $3000 is non-refundable and will be forfeited 
       if tenant violates any terms of this agreement.
    
    3. Late rent payments will incur a penalty of $200 per day.
    
    4. Landlord may enter the premises at any time without notice for any reason.
    
    5. Tenant waives all rights to legal recourse and agrees to unlimited liability
       for any damages to the property.
    
    6. This agreement automatically renews for another year unless tenant 
       provides 6 months written notice.
    """
    
    print("\n" + "=" * 50)
    print("Testing Full Document Classification")
    print("=" * 50)
    
    try:
        result = classify_document_risk(sample_document)
        
        print(f"Overall Risk Level: {result['overall_risk']['level']}")
        print(f"Overall Risk Score: {result['overall_risk']['score']:.2f}")
        print(f"Overall Severity: {result['overall_risk']['severity']}")
        print(f"Total Clauses Analyzed: {result['total_clauses_analyzed']}")
        
        print("\nClause-by-Clause Analysis:")
        for clause_assessment in result['clause_assessments']:
            assessment = clause_assessment['assessment']
            print(f"\n{clause_assessment['clause_id']}: {assessment.level.value}")
            print(f"  Score: {assessment.score:.2f}")
            print(f"  Text: {clause_assessment['text'][:100]}...")
            if assessment.reasons:
                print(f"  Reasons: {', '.join(assessment.reasons[:2])}")
        
        print("\n✅ Document classification completed successfully")
        
    except Exception as e:
        print(f"❌ Document classification failed: {e}")

if __name__ == "__main__":
    test_risk_classifier()
    test_document_classification()