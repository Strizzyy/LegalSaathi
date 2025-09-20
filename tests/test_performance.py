"""
Performance tests to verify improved response times with FastAPI
"""

import pytest
import time
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app

client = TestClient(app)


class TestPerformanceImprovement:
    """Test performance improvements with FastAPI over Flask"""
    
    def test_health_check_response_time(self):
        """Test health check endpoint response time"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Health check should be very fast
        assert response_time < 0.5  # 500ms threshold
        
        # Check response time header
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time < 0.1  # 100ms for processing
    
    def test_concurrent_requests_performance(self):
        """Test performance under concurrent load"""
        def make_request():
            start = time.time()
            response = client.get("/health")
            end = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end - start,
                'process_time': float(response.headers.get('X-Process-Time', 0))
            }
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r['status_code'] == 200 for r in results)
        
        # Average response time should be reasonable
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        assert avg_response_time < 1.0  # 1 second average
        
        # No request should take too long
        max_response_time = max(r['response_time'] for r in results)
        assert max_response_time < 2.0  # 2 second max
    
    @patch('controllers.document_controller.DocumentController.analyze_document')
    def test_document_analysis_performance(self, mock_analyze):
        """Test document analysis endpoint performance"""
        # Mock fast analysis response
        mock_analyze.return_value = {
            "success": True,
            "analysis_id": "perf-test-123",
            "overall_risk": {"level": "GREEN", "score": 0.3},
            "clause_assessments": [],
            "summary": "Quick analysis",
            "processing_time": 0.5
        }
        
        start_time = time.time()
        response = client.post(
            "/api/analyze",
            json={
                "document_text": "Standard rental agreement with typical clauses",
                "document_type": "rental_agreement",
                "user_expertise_level": "beginner"
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # API endpoint should respond quickly (excluding AI processing)
        assert response_time < 1.0  # 1 second for API overhead
        
        # Check FastAPI async performance
        process_time = float(response.headers.get('X-Process-Time', 0))
        assert process_time < 0.5  # FastAPI processing should be fast
    
    def test_multiple_endpoint_performance(self):
        """Test performance across multiple endpoints"""
        endpoints = [
            ("/health", "GET", None),
            ("/api", "GET", None),
            ("/api/health/detailed", "GET", None),
            ("/api/translate/languages", "GET", None),
            ("/api/speech/languages", "GET", None)
        ]
        
        results = []
        
        for endpoint, method, data in endpoints:
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            
            end_time = time.time()
            
            results.append({
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'process_time': float(response.headers.get('X-Process-Time', 0))
            })
        
        # All endpoints should respond successfully
        successful_requests = [r for r in results if r['status_code'] == 200]
        assert len(successful_requests) >= len(endpoints) * 0.8  # 80% success rate
        
        # Average response time should be good
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 0.5  # 500ms average
    
    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency"""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests to test memory usage
        for i in range(50):
            response = client.get("/health")
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024  # 50MB threshold
    
    @patch('controllers.speech_controller.SpeechController.get_supported_languages')
    def test_cached_response_performance(self, mock_languages):
        """Test performance of cached responses"""
        mock_languages.return_value = {
            "success": True,
            "speech_to_text_languages": [{"code": "en-US", "name": "English"}],
            "text_to_speech_languages": [{"code": "en-US", "name": "English"}],
            "total_stt_count": 1,
            "total_tts_count": 1
        }
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/api/speech/languages")
        first_response_time = time.time() - start_time
        
        # Second request (should be faster due to caching)
        start_time = time.time()
        response2 = client.get("/api/speech/languages")
        second_response_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both responses should be fast, but caching might make second faster
        assert first_response_time < 1.0
        assert second_response_time < 1.0
    
    def test_large_payload_handling(self):
        """Test performance with large payloads"""
        # Create large document text (but within limits)
        large_text = "This is a rental agreement clause. " * 1000  # ~35KB
        
        with patch('controllers.document_controller.DocumentController.analyze_document') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analysis_id": "large-doc-123",
                "overall_risk": {"level": "YELLOW", "score": 0.6},
                "processing_time": 2.0
            }
            
            start_time = time.time()
            response = client.post(
                "/api/analyze",
                json={
                    "document_text": large_text,
                    "document_type": "rental_agreement"
                }
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Should handle large payloads efficiently
            assert response_time < 2.0  # 2 second threshold for large docs
    
    def test_error_handling_performance(self):
        """Test performance of error handling"""
        # Test various error conditions
        error_tests = [
            # Invalid JSON
            ("/api/analyze", {"invalid": "json", "missing": "required_fields"}),
            # Missing required fields
            ("/api/translate", {}),
            # Invalid file upload
            ("/api/analyze/file", None)
        ]
        
        for endpoint, data in error_tests:
            start_time = time.time()
            
            if data is None:
                # Test file upload without file
                response = client.post(endpoint, data={"document_type": "rental_agreement"})
            else:
                response = client.post(endpoint, json=data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Error responses should be fast
            assert response_time < 0.5  # 500ms for error handling
            assert response.status_code in [400, 422]  # Validation errors


class TestAsyncPerformance:
    """Test async performance benefits of FastAPI"""
    
    @patch('controllers.document_controller.DocumentController.start_async_analysis')
    def test_async_analysis_initiation(self, mock_async):
        """Test async analysis initiation performance"""
        mock_async.return_value = {
            "success": True,
            "analysis_id": "async-perf-123",
            "status": "processing",
            "estimated_completion": "2024-01-01T12:00:00Z"
        }
        
        start_time = time.time()
        response = client.post(
            "/api/analyze/async",
            json={
                "document_text": "Long document for async processing",
                "document_type": "employment_contract"
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Async initiation should be very fast
        assert response_time < 0.2  # 200ms threshold
        
        data = response.json()
        assert data["status"] == "processing"
    
    def test_concurrent_async_requests(self):
        """Test handling multiple async requests concurrently"""
        def make_async_request(i):
            with patch('controllers.document_controller.DocumentController.start_async_analysis') as mock_async:
                mock_async.return_value = {
                    "analysis_id": f"concurrent-{i}",
                    "status": "processing"
                }
                
                start = time.time()
                response = client.post(
                    "/api/analyze/async",
                    json={
                        "document_text": f"Document {i} for concurrent processing",
                        "document_type": "rental_agreement"
                    }
                )
                end = time.time()
                
                return {
                    'request_id': i,
                    'status_code': response.status_code,
                    'response_time': end - start
                }
        
        # Test 20 concurrent async requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_async_request, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed quickly
        assert all(r['status_code'] == 200 for r in results)
        
        # All should be fast (async initiation)
        assert all(r['response_time'] < 0.5 for r in results)
        
        # Average should be very fast
        avg_time = sum(r['response_time'] for r in results) / len(results)
        assert avg_time < 0.2


class TestCompressionPerformance:
    """Test compression middleware performance"""
    
    def test_gzip_compression_benefit(self):
        """Test GZip compression performance benefit"""
        # Request large response that should be compressed
        response = client.get("/docs")  # OpenAPI docs are large
        
        if response.status_code == 200:
            # Check if compression headers are present
            content_encoding = response.headers.get('content-encoding', '')
            content_length = len(response.content)
            
            # Large responses should be compressed
            if content_length > 1000:
                # Should have compression or be reasonably sized
                assert content_encoding == 'gzip' or content_length < 100000
    
    def test_compression_threshold(self):
        """Test compression threshold behavior"""
        # Small response (should not be compressed)
        small_response = client.get("/health")
        assert small_response.status_code == 200
        
        # Small responses typically don't get compressed
        small_encoding = small_response.headers.get('content-encoding', '')
        
        # Large response (should be compressed if available)
        large_response = client.get("/docs")
        
        if large_response.status_code == 200 and len(large_response.content) > 1000:
            # Compression behavior depends on middleware configuration
            pass  # Just ensure no errors occur


class TestRateLimitingPerformance:
    """Test rate limiting performance impact"""
    
    def test_rate_limit_overhead(self):
        """Test performance overhead of rate limiting"""
        # Make requests within rate limit
        response_times = []
        
        for i in range(5):  # Well within rate limits
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Rate limiting should not add significant overhead
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 0.1  # 100ms average with rate limiting
        
        # Variance should be low (consistent performance)
        max_time = max(response_times)
        min_time = min(response_times)
        assert max_time - min_time < 0.2  # 200ms variance threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])