#!/usr/bin/env python3
"""
Simple test to verify real AI services are working
"""

def test_ai_service_type():
    """Test AI service type"""
    print("🤖 Testing AI Service Type...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import ai_clarification_service
        
        service_type = type(ai_clarification_service).__name__
        print(f"  Service Type: {service_type}")
        
        if service_type == "RealAIService":
            print("  ✅ Using Real AI Service")
            return True
        else:
            print(f"  ❌ Still using: {service_type}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_translation_service():
    """Test translation service"""
    print("\n🌐 Testing Translation Service...")
    
    try:
        from google_translate_service import GoogleTranslateService
        
        translator = GoogleTranslateService()
        print("  ✅ GoogleTranslateService imported successfully")
        
        # Test basic functionality
        languages = translator.get_supported_languages()
        print(f"  ✅ Supports {len(languages)} languages")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_risk_classifier():
    """Test risk classifier"""
    print("\n🎯 Testing Risk Classifier...")
    
    try:
        from risk_classifier import RiskClassifier
        
        classifier = RiskClassifier()
        print("  ✅ RiskClassifier imported successfully")
        
        # Check for real AI clients
        has_groq = hasattr(classifier, 'groq_client')
        has_gemini = hasattr(classifier, 'gemini_model')
        
        print(f"  Groq Client: {'✅' if has_groq else '❌'}")
        print(f"  Gemini Client: {'✅' if has_gemini else '❌'}")
        
        classifier.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run simple tests"""
    print("🚀 Simple Real AI Services Test\n")
    
    tests = [
        test_ai_service_type,
        test_translation_service,
        test_risk_classifier
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Real AI services are properly configured!")
    else:
        print("⚠️ Some issues found with AI services.")

if __name__ == "__main__":
    main()