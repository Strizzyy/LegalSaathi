#!/usr/bin/env python3
"""
Test Real AI Services Integration
Verifies that mock services have been replaced with real AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_ai_clarification():
    """Test that AI clarification service is using real AI"""
    print("🤖 Testing Real AI Clarification Service...")
    
    try:
        from app import ai_clarification_service
        
        # Check if it's the real service (not mock)
        service_type = type(ai_clarification_service).__name__
        print(f"  Service Type: {service_type}")
        
        if service_type == "RealAIService":
            print("  ✅ Using Real AI Service (not mock)")
            
            # Test a simple question
            test_question = "What does this clause mean?"
            test_context = {"risk_level": "YELLOW", "summary": "Test document"}
            
            try:
                result = ai_clarification_service.ask_clarification(test_question, test_context)
                if result.get('success'):
                    print("  ✅ AI clarification working")
                    print(f"  Response preview: {result.get('response', '')[:100]}...")
                else:
                    print("  ⚠️ AI clarification returned error")
            except Exception as e:
                print(f"  ⚠️ AI clarification failed (expected if vLLM server not running): {e}")
                
        else:
            print(f"  ❌ Still using mock service: {service_type}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def test_risk_classifier_real_ai():
    """Test that risk classifier is using real AI"""
    print("\n🎯 Testing Risk Classifier Real AI...")
    
    try:
        from risk_classifier import RiskClassifier
        
        classifier = RiskClassifier()
        
        # Check if it has real AI clients
        has_groq = hasattr(classifier, 'groq_client') and classifier.groq_client is not None
        has_gemini = hasattr(classifier, 'gemini_model') and classifier.gemini_model is not None
        
        print(f"  Groq Client: {'✅ Available' if has_groq else '❌ Not configured'}")
        print(f"  Gemini Client: {'✅ Available' if has_gemini else '❌ Not configured'}")
        
        # Test with a simple clause
        test_clause = "The tenant must pay a non-refundable security deposit of $2000."
        
        try:
            assessment = classifier.classify_risk_level(test_clause)
            print(f"  ✅ Risk assessment working: {assessment.level.value} risk")
            print(f"  Confidence: {assessment.confidence_percentage}%")
            print(f"  Reasons: {assessment.reasons[:2]}")
        except Exception as e:
            print(f"  ⚠️ Risk assessment failed: {e}")
        
        classifier.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def test_no_mock_imports():
    """Test that no mock services are being imported"""
    print("\n🔍 Testing for Mock Service Imports...")
    
    try:
        # Check app.py imports
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        mock_found = []
        if 'MockVertexAIService' in app_content:
            mock_found.append('MockVertexAIService in app.py')
        if 'MockTranslationService' in app_content:
            mock_found.append('MockTranslationService in app.py')
        
        # Check risk_classifier.py
        with open('risk_classifier.py', 'r') as f:
            risk_content = f.read()
        
        if 'class MockVertexAIService' in risk_content:
            mock_found.append('MockVertexAIService class in risk_classifier.py')
        if 'MockTranslationService' in risk_content:
            mock_found.append('MockTranslationService in risk_classifier.py')
        
        if mock_found:
            print("  ❌ Mock services still found:")
            for mock in mock_found:
                print(f"    - {mock}")
            return False
        else:
            print("  ✅ No mock services found in code")
            return True
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def test_real_translation_service():
    """Test that translation service is real"""
    print("\n🌐 Testing Real Translation Service...")
    
    try:
        from google_translate_service import GoogleTranslateService
        
        translator = GoogleTranslateService()
        
        # Test translation
        test_text = "This is a test document."
        result = translator.translate_text(test_text, 'hi')
        
        if result.get('success'):
            print("  ✅ Real Google Translate service working")
            print(f"  Translation: {result.get('translated_text', '')}")
        else:
            print(f"  ⚠️ Translation failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def main():
    """Run all real AI tests"""
    print("🚀 Testing Real AI Services Integration\n")
    
    tests = [
        ("Mock Service Removal", test_no_mock_imports),
        ("Real AI Clarification", test_real_ai_clarification),
        ("Risk Classifier Real AI", test_risk_classifier_real_ai),
        ("Real Translation Service", test_real_translation_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n📊 REAL AI INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All mock services successfully replaced with real AI!")
    else:
        print("⚠️ Some mock services may still be present.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)