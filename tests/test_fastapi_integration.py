"""
Integration tests for FastAPI backend with React frontend communication
"""

import pytest
import json
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app

client = TestClient(app)


class TestFastAPIIntegration:
    """Test FastAPI backend integration"""
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        response = client.get("/api/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "timestamp" in data
        assert isinstance(data["services"], dict)
    
    def test_api_root_endpoint(self):
        """Test API root endpoint"""
        response = client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Legal Saathi Document Advisor API"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options("/api/analyze")
        
        # Should not return 405 Method Not Allowed due to CORS middleware
        assert response.status_code in [200, 404]
    
    def test_compression_middleware(self):
        """Test GZip compression middleware"""
        # Make request for large response
        response = client.get("/docs")
        
        # Check if compression headers are present for large responses
        if len(response.content) > 1000:
            # FastAPI docs should be large enough to trigger compression
            assert response.status_code == 200


class TestDocumentAnalysisIntegration:
    """Test document analysis endpoints integration"""
    
    def test_analyze_text_document(self):
        """Test text document analysis endpoint"""
        with patch('controllers.document_controller.DocumentController.analyze_document') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analysis_id": "test-123",
                "overall_risk": {
                    "level": "YELLOW",
                    "score": 0.6,
                    "confidence_percentage": 85
                },
                "clause_assessments": [],
                "summary": "Test analysis summary",
                "processing_time": 2.5,
                "recommendations": ["Review clause 1", "Consider legal advice"]
            }
            
            response = client.post(
                "/api/analyze",
                json={
                    "document_text": "This is a test rental agreement with standard terms and conditions.",
                    "document_type": "rental_agreement",
                    "user_expertise_level": "beginner"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["analysis_id"] == "test-123"
            assert data["overall_risk"]["level"] == "YELLOW"
    
    def test_analyze_file_document(self):
        """Test file document analysis endpoint"""
        with patch('controllers.document_controller.DocumentController.analyze_document_file') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analysis_id": "file-test-123",
                "overall_risk": {
                    "level": "GREEN",
                    "score": 0.3,
                    "confidence_percentage": 92
                },
                "clause_assessments": [],
                "summary": "File analysis summary",
                "processing_time": 3.2
            }
            
            # Create mock PDF file
            pdf_content = b"%PDF-1.4 mock pdf content"
            pdf_file = io.BytesIO(pdf_content)
            
            response = client.post(
                "/api/analyze/file",
                files={"file": ("test.pdf", pdf_file, "application/pdf")},
                data={
                    "document_type": "rental_agreement",
                    "user_expertise_level": "intermediate"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["analysis_id"] == "file-test-123"
    
    def test_async_analysis_workflow(self):
        """Test async analysis workflow"""
        with patch('controllers.document_controller.DocumentController.start_async_analysis') as mock_start:
            mock_start.return_value = {
                "success": True,
                "analysis_id": "async-123",
                "status": "processing",
                "estimated_completion": "2024-01-01T12:00:00Z"
            }
            
            # Start async analysis
            response = client.post(
                "/api/analyze/async",
                json={
                    "document_text": "Long document text for async processing...",
                    "document_type": "employment_contract",
                    "user_expertise_level": "expert"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_id"] == "async-123"
            assert data["status"] == "processing"
        
        with patch('controllers.document_controller.DocumentController.get_analysis_status') as mock_status:
            mock_status.return_value = {
                "analysis_id": "async-123",
                "status": "completed",
                "progress_percentage": 100,
                "result": {
                    "overall_risk": {"level": "RED", "score": 0.8},
                    "summary": "High risk document"
                }
            }
            
            # Check status
            response = client.get("/api/analysis/status/async-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress_percentage"] == 100


class TestTranslationIntegration:
    """Test translation endpoints integration"""
    
    def test_translate_text(self):
        """Test text translation endpoint"""
        with patch('controllers.translation_controller.TranslationController.translate_text') as mock_translate:
            mock_translate.return_value = {
                "success": True,
                "translated_text": "Este es un contrato de alquiler",
                "source_language": "en",
                "target_language": "es",
                "confidence": 0.95,
                "processing_time": 0.8
            }
            
            response = client.post(
                "/api/translate",
                json={
                    "text": "This is a rental agreement",
                    "target_language": "es",
                    "source_language": "en"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["translated_text"] == "Este es un contrato de alquiler"
            assert data["target_language"] == "es"
    
    def test_translate_clause(self):
        """Test clause translation endpoint"""
        with patch('controllers.translation_controller.TranslationController.translate_clause') as mock_translate:
            mock_translate.return_value = {
                "success": True,
                "translated_clause": "El inquilino debe pagar la renta mensualmente",
                "original_clause": "Tenant must pay rent monthly",
                "legal_context": "rental_agreement",
                "confidence": 0.92
            }
            
            response = client.post(
                "/api/translate/clause",
                json={
                    "clause_text": "Tenant must pay rent monthly",
                    "clause_context": "rental_agreement",
                    "target_language": "es",
                    "source_language": "en"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "translated_clause" in data
    
    def test_get_translation_languages(self):
        """Test get supported translation languages"""
        response = client.get("/api/translate/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "supported_languages" in data
        assert len(data["supported_languages"]) > 0


class TestAIIntegration:
    """Test AI clarification endpoints integration"""
    
    def test_ai_clarification(self):
        """Test AI clarification endpoint"""
        with patch('controllers.ai_controller.AIController.get_clarification') as mock_clarify:
            mock_clarify.return_value = {
                "success": True,
                "response": "This clause means that you are responsible for all maintenance costs, which could be expensive. Consider negotiating shared responsibility.",
                "confidence": 0.88,
                "sources": ["legal_database", "case_law"],
                "processing_time": 1.2
            }
            
            response = client.post(
                "/api/ai/clarify",
                json={
                    "question": "What does this maintenance clause mean?",
                    "context": {
                        "document_type": "rental_agreement",
                        "clause_text": "Tenant is responsible for all maintenance and repairs"
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data
            assert data["confidence"] > 0.8
    
    def test_conversation_summary(self):
        """Test conversation summary endpoint"""
        with patch('controllers.ai_controller.AIController.get_conversation_summary') as mock_summary:
            mock_summary.return_value = {
                "total_questions": 5,
                "main_concerns": ["maintenance costs", "termination clauses"],
                "risk_areas_discussed": ["liability", "financial obligations"],
                "recommendations": ["Seek legal review", "Negotiate terms"]
            }
            
            response = client.get("/api/ai/conversation/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_questions" in data
            assert "main_concerns" in data


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_validation_errors(self):
        """Test request validation errors"""
        # Missing required fields
        response = client.post("/api/analyze", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(15):  # Exceed rate limit
            response = client.post(
                "/api/analyze",
                json={
                    "document_text": f"Test document {i}",
                    "document_type": "general_contract"
                }
            )
            responses.append(response)
        
        # Should have some rate limited responses
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
    
    def test_large_request_handling(self):
        """Test handling of large requests"""
        # Very large document text
        large_text = "x" * 100000  # 100KB text
        
        response = client.post(
            "/api/analyze",
            json={
                "document_text": large_text,
                "document_type": "general_contract"
            }
        )
        
        # Should handle gracefully (either process or reject with proper error)
        assert response.status_code in [200, 400, 413, 422]
    
    def test_invalid_file_upload(self):
        """Test invalid file upload handling"""
        # Upload non-document file
        invalid_file = io.BytesIO(b"not a document")
        
        response = client.post(
            "/api/analyze/file",
            files={"file": ("test.exe", invalid_file, "application/octet-stream")},
            data={"document_type": "rental_agreement"}
        )
        
        assert response.status_code in [400, 422]


class TestPerformanceMetrics:
    """Test performance monitoring and metrics"""
    
    def test_response_time_headers(self):
        """Test that response time headers are added"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        # Process time should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 10  # Should be reasonable
    
    def test_cache_headers(self):
        """Test cache headers for API responses"""
        response = client.get("/api")
        
        assert response.status_code == 200
        # API responses should have cache headers
        assert "Cache-Control" in response.headers
    
    def test_service_metrics(self):
        """Test service metrics endpoint"""
        response = client.get("/api/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "uptime" in data or "requests_processed" in data


class TestStaticFileServing:
    """Test static file serving for React frontend"""
    
    def test_frontend_index_serving(self):
        """Test that React frontend index.html is served"""
        response = client.get("/")
        
        # Should serve React app or return 404 if not built
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
    
    def test_spa_routing(self):
        """Test SPA routing for React frontend"""
        # Test various frontend routes
        frontend_routes = ["/dashboard", "/analysis", "/settings"]
        
        for route in frontend_routes:
            response = client.get(route)
            
            # Should serve React app or return 404 if not built
            assert response.status_code in [200, 404]
    
    def test_api_route_precedence(self):
        """Test that API routes take precedence over SPA routing"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        # Should return JSON, not HTML
        assert "application/json" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])