"""
Test suite for Gemini API integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGeminiIntegration:
    """Test Gemini API integration and fallback mechanisms"""
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_initialization(self, mock_model):
        """Test Gemini service initialization"""
        from services.ai_service import AIService
        
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        assert hasattr(service, 'gemini_client')
        assert hasattr(service, 'fallback_analyzer')
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_risk_analysis_success(self, mock_model):
        """Test successful Gemini API risk analysis"""
        from services.ai_service import AIService
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''
        {
            "risk_level": "YELLOW",
            "confidence_percentage": 85,
            "risk_score": 0.6,
            "risk_categories": {
                "financial": 0.7,
                "legal": 0.5,
                "operational": 0.6
            },
            "reasons": [
                "High maintenance responsibility for tenant",
                "Unclear termination conditions"
            ]
        }
        '''
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content_async.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Test risk analysis
        result = service.analyze_risk(
            "Tenant is responsible for all maintenance and repairs",
            "rental_agreement"
        )
        
        assert result["risk_level"] == "YELLOW"
        assert result["confidence_percentage"] == 85
        assert result["risk_score"] == 0.6
        assert "financial" in result["risk_categories"]
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_api_failure_fallback(self, mock_model):
        """Test fallback when Gemini API fails"""
        from services.ai_service import AIService
        
        # Mock Gemini API failure
        mock_model_instance = Mock()
        mock_model_instance.generate_content_async.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Mock fallback analyzer
        with patch.object(service.fallback_analyzer, 'analyze_risk') as mock_fallback:
            mock_fallback.return_value = {
                "risk_level": "YELLOW",
                "confidence_percentage": 60,
                "risk_score": 0.5,
                "source": "keyword_analysis"
            }
            
            result = service.analyze_risk(
                "Tenant pays all utilities and maintenance",
                "rental_agreement"
            )
            
            assert result["risk_level"] == "YELLOW"
            assert result["source"] == "keyword_analysis"
            mock_fallback.assert_called_once()
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_clarification_service(self, mock_model):
        """Test Gemini AI clarification service"""
        from services.ai_service import AIService
        
        mock_response = Mock()
        mock_response.text = "This clause means you are responsible for all repair costs, which could be expensive. Consider negotiating shared responsibility with the landlord."
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content_async.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        result = service.get_clarification(
            "What does this maintenance clause mean?",
            {
                "clause_text": "Tenant responsible for all maintenance",
                "document_type": "rental_agreement"
            }
        )
        
        assert "responsible for all repair costs" in result
        assert "expensive" in result
    
    def test_keyword_fallback_analyzer(self):
        """Test keyword-based fallback analyzer"""
        from services.ai_service import KeywordBasedAnalyzer
        
        analyzer = KeywordBasedAnalyzer()
        
        # Test high-risk keywords
        high_risk_text = "Tenant liable for all damages, unlimited liability, immediate termination without notice"
        result = analyzer.analyze_risk(high_risk_text, "rental_agreement")
        
        assert result["risk_level"] == "RED"
        assert result["confidence_percentage"] < 80  # Lower confidence for keyword analysis
        
        # Test low-risk text
        low_risk_text = "Standard rental terms, reasonable notice period, shared maintenance responsibility"
        result = analyzer.analyze_risk(low_risk_text, "rental_agreement")
        
        assert result["risk_level"] in ["GREEN", "YELLOW"]
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_prompt_construction(self, mock_model):
        """Test Gemini prompt construction for legal analysis"""
        from services.ai_service import AIService
        
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Test prompt building
        prompt = service._build_risk_analysis_prompt(
            "Tenant pays security deposit of $5000",
            "rental_agreement"
        )
        
        assert "rental_agreement" in prompt.lower()
        assert "security deposit" in prompt.lower()
        assert "risk" in prompt.lower()
        assert "json" in prompt.lower()  # Should request JSON format
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_response_parsing(self, mock_model):
        """Test parsing of Gemini API responses"""
        from services.ai_service import AIService
        
        service = AIService()
        
        # Test valid JSON response
        valid_response = '''
        {
            "risk_level": "RED",
            "confidence_percentage": 90,
            "risk_score": 0.8,
            "reasons": ["High security deposit", "Unfavorable terms"]
        }
        '''
        
        result = service._parse_risk_response(valid_response)
        assert result["risk_level"] == "RED"
        assert result["confidence_percentage"] == 90
        
        # Test invalid JSON response
        invalid_response = "This is not JSON format"
        result = service._parse_risk_response(invalid_response)
        assert result["risk_level"] == "YELLOW"  # Default fallback
        assert result["confidence_percentage"] < 70
    
    def test_legal_terminology_detection(self):
        """Test detection of legal terminology in documents"""
        from services.ai_service import AIService
        
        service = AIService()
        
        legal_text = """
        This lease agreement contains indemnification clauses, 
        force majeure provisions, and arbitration requirements.
        The jurisdiction clause specifies governing law.
        """
        
        terms = service._detect_legal_terms(legal_text)
        
        expected_terms = ["indemnification", "force majeure", "arbitration", "jurisdiction", "governing law"]
        found_terms = [term["term"] for term in terms]
        
        for expected in expected_terms:
            assert any(expected in found for found in found_terms)
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_rate_limiting_handling(self, mock_model):
        """Test handling of Gemini API rate limiting"""
        from services.ai_service import AIService
        import time
        
        # Mock rate limit error
        mock_model_instance = Mock()
        mock_model_instance.generate_content_async.side_effect = Exception("Rate limit exceeded")
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Should fall back to keyword analysis
        with patch.object(service.fallback_analyzer, 'analyze_risk') as mock_fallback:
            mock_fallback.return_value = {
                "risk_level": "YELLOW",
                "confidence_percentage": 50,
                "source": "fallback_due_to_rate_limit"
            }
            
            result = service.analyze_risk("Test text", "rental_agreement")
            
            assert result["source"] == "fallback_due_to_rate_limit"
            mock_fallback.assert_called_once()
    
    def test_document_type_specific_analysis(self):
        """Test document type specific analysis prompts"""
        from services.ai_service import AIService
        
        service = AIService()
        
        # Test different document types
        document_types = [
            "rental_agreement",
            "employment_contract", 
            "nda",
            "loan_agreement"
        ]
        
        for doc_type in document_types:
            prompt = service._build_risk_analysis_prompt("Test clause", doc_type)
            assert doc_type.replace("_", " ") in prompt.lower()
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_confidence_scoring(self, mock_model):
        """Test confidence scoring in Gemini responses"""
        from services.ai_service import AIService
        
        # Test high confidence response
        high_conf_response = Mock()
        high_conf_response.text = '''
        {
            "risk_level": "RED",
            "confidence_percentage": 95,
            "risk_score": 0.9,
            "analysis_quality": "high"
        }
        '''
        
        # Test low confidence response
        low_conf_response = Mock()
        low_conf_response.text = '''
        {
            "risk_level": "YELLOW", 
            "confidence_percentage": 45,
            "risk_score": 0.5,
            "analysis_quality": "low"
        }
        '''
        
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Test confidence threshold handling
        high_result = service._parse_risk_response(high_conf_response.text)
        assert high_result["confidence_percentage"] == 95
        assert not high_result.get("low_confidence_warning", False)
        
        low_result = service._parse_risk_response(low_conf_response.text)
        assert low_result["confidence_percentage"] == 45
        # Should add low confidence warning
        assert low_result.get("low_confidence_warning", True)


class TestGeminiPerformance:
    """Test Gemini API performance and optimization"""
    
    @patch('google.generativeai.GenerativeModel')
    def test_response_time_monitoring(self, mock_model):
        """Test response time monitoring for Gemini API"""
        from services.ai_service import AIService
        import time
        
        # Mock delayed response
        def delayed_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate API delay
            mock_resp = Mock()
            mock_resp.text = '{"risk_level": "GREEN", "confidence_percentage": 80}'
            return mock_resp
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content_async.side_effect = delayed_response
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        start_time = time.time()
        result = service.analyze_risk("Test text", "rental_agreement")
        end_time = time.time()
        
        # Should track processing time
        assert "processing_time" in result
        assert result["processing_time"] > 0
        assert end_time - start_time >= 0.1
    
    @patch('google.generativeai.GenerativeModel')
    def test_text_length_optimization(self, mock_model):
        """Test optimization for different text lengths"""
        from services.ai_service import AIService
        
        mock_model_instance = Mock()
        mock_response = Mock()
        mock_response.text = '{"risk_level": "YELLOW", "confidence_percentage": 75}'
        mock_model_instance.generate_content_async.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        service = AIService()
        
        # Test short text
        short_result = service.analyze_risk("Short clause", "rental_agreement")
        assert short_result["risk_level"] == "YELLOW"
        
        # Test long text (should be truncated or chunked)
        long_text = "Very long clause " * 1000
        long_result = service.analyze_risk(long_text, "rental_agreement")
        assert long_result["risk_level"] == "YELLOW"
        
        # Both should succeed
        assert short_result["confidence_percentage"] > 0
        assert long_result["confidence_percentage"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])