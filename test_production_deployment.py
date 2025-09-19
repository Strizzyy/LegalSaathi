#!/usr/bin/env python3
"""
Production Deployment Testing Suite
Comprehensive end-to-end testing for competition readiness
"""

import requests
import time
import json
import sys
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionTester:
    """Comprehensive production testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = 30
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("🚀 Starting LegalSaathi Production Test Suite")
        
        test_methods = [
            self.test_health_endpoint,
            self.test_home_page,
            self.test_demo_environment,
            self.test_analytics_dashboard,
            self.test_document_analysis,
            self.test_ai_clarification,
            self.test_translation_service,
            self.test_performance_metrics,
            self.test_error_handling,
            self.test_security_headers,
            self.test_mobile_responsiveness,
            self.test_concurrent_users
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                result = test_method()
                if result['passed']:
                    passed += 1
                    logger.info(f"✅ {result['test_name']}: PASSED")
                else:
                    failed += 1
                    logger.error(f"❌ {result['test_name']}: FAILED - {result['error']}")
                
                self.test_results.append(result)
                
            except Exception as e:
                failed += 1
                error_result = {
                    'test_name': test_method.__name__,
                    'passed': False,
                    'error': str(e),
                    'execution_time': 0
                }
                self.test_results.append(error_result)
                logger.error(f"❌ {test_method.__name__}: EXCEPTION - {str(e)}")
        
        # Generate summary
        summary = {
            'total_tests': len(test_methods),
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / len(test_methods)) * 100,
            'test_results': self.test_results
        }
        
        logger.info(f"🏁 Test Suite Complete: {passed}/{len(test_methods)} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary
    
    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test system health endpoint"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Validate health response structure
                required_fields = ['status', 'timestamp', 'uptime_seconds', 'services']
                missing_fields = [field for field in required_fields if field not in health_data]
                
                if missing_fields:
                    return {
                        'test_name': 'Health Endpoint',
                        'passed': False,
                        'error': f'Missing fields: {missing_fields}',
                        'execution_time': execution_time
                    }
                
                # Check if system is healthy
                is_healthy = health_data['status'] in ['healthy', 'degraded']
                
                return {
                    'test_name': 'Health Endpoint',
                    'passed': is_healthy,
                    'error': None if is_healthy else f"System status: {health_data['status']}",
                    'execution_time': execution_time,
                    'details': health_data
                }
            else:
                return {
                    'test_name': 'Health Endpoint',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Health Endpoint',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_home_page(self) -> Dict[str, Any]:
        """Test home page accessibility"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/")
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check for key elements in HTML
                html_content = response.text
                required_elements = [
                    'LegalSaathi',
                    'document',
                    'analyze',
                    'legal'
                ]
                
                missing_elements = [elem for elem in required_elements 
                                  if elem.lower() not in html_content.lower()]
                
                if missing_elements:
                    return {
                        'test_name': 'Home Page',
                        'passed': False,
                        'error': f'Missing elements: {missing_elements}',
                        'execution_time': execution_time
                    }
                
                return {
                    'test_name': 'Home Page',
                    'passed': True,
                    'error': None,
                    'execution_time': execution_time
                }
            else:
                return {
                    'test_name': 'Home Page',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Home Page',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_demo_environment(self) -> Dict[str, Any]:
        """Test demo environment for judges"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/demo")
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                # Test demo API endpoints
                demo_endpoints = [
                    '/api/demo/document/rental_agreement_problematic',
                    '/api/demo/scenario/first_time_renter',
                    '/api/demo/tour/quick_demo'
                ]
                
                for endpoint in demo_endpoints:
                    try:
                        demo_response = self.session.get(f"{self.base_url}{endpoint}")
                        if demo_response.status_code != 200:
                            return {
                                'test_name': 'Demo Environment',
                                'passed': False,
                                'error': f'Demo endpoint {endpoint} failed: HTTP {demo_response.status_code}',
                                'execution_time': execution_time
                            }
                    except Exception as e:
                        return {
                            'test_name': 'Demo Environment',
                            'passed': False,
                            'error': f'Demo endpoint {endpoint} error: {str(e)}',
                            'execution_time': execution_time
                        }
                
                return {
                    'test_name': 'Demo Environment',
                    'passed': True,
                    'error': None,
                    'execution_time': execution_time
                }
            else:
                return {
                    'test_name': 'Demo Environment',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Demo Environment',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_analytics_dashboard(self) -> Dict[str, Any]:
        """Test analytics dashboard functionality"""
        start_time = time.time()
        
        try:
            # Test analytics page
            response = self.session.get(f"{self.base_url}/analytics")
            if response.status_code != 200:
                return {
                    'test_name': 'Analytics Dashboard',
                    'passed': False,
                    'error': f'Analytics page HTTP {response.status_code}',
                    'execution_time': time.time() - start_time
                }
            
            # Test analytics API
            api_response = self.session.get(f"{self.base_url}/api/analytics")
            execution_time = time.time() - start_time
            
            if api_response.status_code == 200:
                analytics_data = api_response.json()
                
                # Validate analytics data structure
                required_fields = ['current_status', 'trends', 'performance_summary']
                missing_fields = [field for field in required_fields if field not in analytics_data]
                
                if missing_fields:
                    return {
                        'test_name': 'Analytics Dashboard',
                        'passed': False,
                        'error': f'Missing analytics fields: {missing_fields}',
                        'execution_time': execution_time
                    }
                
                return {
                    'test_name': 'Analytics Dashboard',
                    'passed': True,
                    'error': None,
                    'execution_time': execution_time
                }
            else:
                return {
                    'test_name': 'Analytics Dashboard',
                    'passed': False,
                    'error': f'Analytics API HTTP {api_response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Analytics Dashboard',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_document_analysis(self) -> Dict[str, Any]:
        """Test core document analysis functionality"""
        start_time = time.time()
        
        try:
            # Sample document for testing
            test_document = """
            RENTAL AGREEMENT
            
            This agreement is between Landlord and Tenant.
            
            1. RENT: Tenant agrees to pay $2000 per month.
            2. DEPOSIT: Security deposit of $4000 is required.
            3. TERMINATION: Either party may terminate with 30 days notice.
            """
            
            # Test document analysis
            response = self.session.post(
                f"{self.base_url}/analyze",
                data={
                    'document_text': test_document,
                    'document_type': 'rental_agreement'
                }
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response contains analysis results
                html_content = response.text
                
                # Look for analysis indicators
                analysis_indicators = [
                    'risk',
                    'analysis',
                    'recommendation',
                    'clause'
                ]
                
                found_indicators = [indicator for indicator in analysis_indicators 
                                  if indicator.lower() in html_content.lower()]
                
                if len(found_indicators) >= 2:
                    return {
                        'test_name': 'Document Analysis',
                        'passed': True,
                        'error': None,
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'test_name': 'Document Analysis',
                        'passed': False,
                        'error': f'Analysis results not found. Found indicators: {found_indicators}',
                        'execution_time': execution_time
                    }
            else:
                return {
                    'test_name': 'Document Analysis',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Document Analysis',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_ai_clarification(self) -> Dict[str, Any]:
        """Test AI clarification service"""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/ask",
                json={
                    'question': 'What does this clause mean?',
                    'context': {'test': True}
                }
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if AI service responded
                if result.get('success') and result.get('response'):
                    return {
                        'test_name': 'AI Clarification',
                        'passed': True,
                        'error': None,
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'test_name': 'AI Clarification',
                        'passed': False,
                        'error': f'AI service failed: {result.get("error", "Unknown error")}',
                        'execution_time': execution_time
                    }
            else:
                return {
                    'test_name': 'AI Clarification',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'AI Clarification',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_translation_service(self) -> Dict[str, Any]:
        """Test translation functionality"""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/translate",
                json={
                    'text': 'This is a test document.',
                    'target_language': 'hi'
                }
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success') and result.get('translated_text'):
                    return {
                        'test_name': 'Translation Service',
                        'passed': True,
                        'error': None,
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'test_name': 'Translation Service',
                        'passed': False,
                        'error': f'Translation failed: {result.get("error", "Unknown error")}',
                        'execution_time': execution_time
                    }
            else:
                return {
                    'test_name': 'Translation Service',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Translation Service',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance and response times"""
        start_time = time.time()
        
        try:
            # Test multiple endpoints for performance
            endpoints = [
                '/',
                '/health',
                '/demo',
                '/analytics'
            ]
            
            response_times = []
            
            for endpoint in endpoints:
                endpoint_start = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                endpoint_time = time.time() - endpoint_start
                
                if response.status_code == 200:
                    response_times.append(endpoint_time)
                else:
                    return {
                        'test_name': 'Performance Metrics',
                        'passed': False,
                        'error': f'Endpoint {endpoint} failed: HTTP {response.status_code}',
                        'execution_time': time.time() - start_time
                    }
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Performance thresholds
            performance_ok = avg_response_time < 5.0 and max_response_time < 10.0
            
            return {
                'test_name': 'Performance Metrics',
                'passed': performance_ok,
                'error': None if performance_ok else f'Performance issues: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s',
                'execution_time': time.time() - start_time,
                'details': {
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'individual_times': dict(zip(endpoints, response_times))
                }
            }
            
        except Exception as e:
            return {
                'test_name': 'Performance Metrics',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and graceful degradation"""
        start_time = time.time()
        
        try:
            # Test invalid endpoints
            invalid_response = self.session.get(f"{self.base_url}/nonexistent")
            
            # Should return 404
            if invalid_response.status_code != 404:
                return {
                    'test_name': 'Error Handling',
                    'passed': False,
                    'error': f'Invalid endpoint returned {invalid_response.status_code} instead of 404',
                    'execution_time': time.time() - start_time
                }
            
            # Test malformed requests
            malformed_response = self.session.post(
                f"{self.base_url}/analyze",
                json={'invalid': 'data'}
            )
            
            # Should handle gracefully (not 500)
            if malformed_response.status_code == 500:
                return {
                    'test_name': 'Error Handling',
                    'passed': False,
                    'error': 'Malformed request caused server error (500)',
                    'execution_time': time.time() - start_time
                }
            
            return {
                'test_name': 'Error Handling',
                'passed': True,
                'error': None,
                'execution_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'test_name': 'Error Handling',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers and configurations"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/")
            execution_time = time.time() - start_time
            
            # Check for security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection'
            ]
            
            missing_headers = [header for header in security_headers 
                             if header not in response.headers]
            
            if missing_headers:
                return {
                    'test_name': 'Security Headers',
                    'passed': False,
                    'error': f'Missing security headers: {missing_headers}',
                    'execution_time': execution_time
                }
            
            return {
                'test_name': 'Security Headers',
                'passed': True,
                'error': None,
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'test_name': 'Security Headers',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_mobile_responsiveness(self) -> Dict[str, Any]:
        """Test mobile responsiveness"""
        start_time = time.time()
        
        try:
            # Test with mobile user agent
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            response = self.session.get(f"{self.base_url}/", headers=mobile_headers)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check for responsive design indicators
                html_content = response.text
                responsive_indicators = [
                    'viewport',
                    'responsive',
                    'mobile',
                    'bootstrap'
                ]
                
                found_indicators = [indicator for indicator in responsive_indicators 
                                  if indicator.lower() in html_content.lower()]
                
                if len(found_indicators) >= 1:
                    return {
                        'test_name': 'Mobile Responsiveness',
                        'passed': True,
                        'error': None,
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'test_name': 'Mobile Responsiveness',
                        'passed': False,
                        'error': 'No responsive design indicators found',
                        'execution_time': execution_time
                    }
            else:
                return {
                    'test_name': 'Mobile Responsiveness',
                    'passed': False,
                    'error': f'HTTP {response.status_code}',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Mobile Responsiveness',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_concurrent_users(self) -> Dict[str, Any]:
        """Test concurrent user handling"""
        start_time = time.time()
        
        try:
            def make_request():
                response = requests.get(f"{self.base_url}/health", timeout=30)
                return response.status_code == 200
            
            # Test with 10 concurrent requests
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in futures]
            
            execution_time = time.time() - start_time
            success_rate = sum(results) / len(results)
            
            # Require 80% success rate for concurrent requests
            if success_rate >= 0.8:
                return {
                    'test_name': 'Concurrent Users',
                    'passed': True,
                    'error': None,
                    'execution_time': execution_time,
                    'details': {
                        'success_rate': success_rate,
                        'successful_requests': sum(results),
                        'total_requests': len(results)
                    }
                }
            else:
                return {
                    'test_name': 'Concurrent Users',
                    'passed': False,
                    'error': f'Low success rate: {success_rate:.2f} (expected >= 0.8)',
                    'execution_time': execution_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Concurrent Users',
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

def main():
    """Main testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LegalSaathi Production Testing Suite')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL to test (default: http://localhost:5000)')
    parser.add_argument('--output', default='test_results.json',
                       help='Output file for test results (default: test_results.json)')
    
    args = parser.parse_args()
    
    # Run tests
    tester = ProductionTester(args.url)
    results = tester.run_all_tests()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"🏁 LegalSaathi Production Test Results")
    print(f"{'='*60}")
    print(f"📊 Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {results['success_rate']:.1f}%")
    print(f"📄 Detailed results saved to: {args.output}")
    
    if results['failed'] > 0:
        print(f"\n❌ Failed Tests:")
        for test in results['test_results']:
            if not test['passed']:
                print(f"  - {test['test_name']}: {test['error']}")
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)

if __name__ == '__main__':
    main()