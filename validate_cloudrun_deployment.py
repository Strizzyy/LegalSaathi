#!/usr/bin/env python3
"""
Cloud Run Deployment Validation Script
Validates that the application is ready for Google Cloud Run deployment
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudRunValidator:
    """Validates Cloud Run deployment readiness"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.validation_results = []
        
    def validate_deployment(self) -> bool:
        """Run all validation checks"""
        logger.info("🔍 Validating Google Cloud Run deployment readiness...")
        
        checks = [
            ("Docker Configuration", self.check_docker_config),
            ("Requirements Files", self.check_requirements),
            ("Environment Configuration", self.check_environment),
            ("Application Structure", self.check_app_structure),
            ("Cloud Run Optimizations", self.check_cloudrun_optimizations),
            ("Security Configuration", self.check_security),
            ("Performance Optimizations", self.check_performance)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                self.validation_results.append((check_name, passed, message))
                
                if passed:
                    logger.info(f"✅ {check_name}: {message}")
                else:
                    logger.error(f"❌ {check_name}: {message}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {check_name}: Validation failed - {e}")
                self.validation_results.append((check_name, False, f"Validation failed: {e}"))
                all_passed = False
        
        self.print_summary()
        return all_passed
    
    def check_docker_config(self) -> Tuple[bool, str]:
        """Check Docker configuration"""
        dockerfile = self.project_root / 'Dockerfile.cloudrun'
        
        if not dockerfile.exists():
            return False, "Dockerfile.cloudrun not found"
        
        # Check dockerfile content
        content = dockerfile.read_text()
        
        required_elements = [
            'FROM python:3.11-slim',
            'GOOGLE_CLOUD_DEPLOYMENT=true',
            'requirements-cloudrun.txt',
            'EXPOSE 8080'
        ]
        
        missing = [elem for elem in required_elements if elem not in content]
        
        if missing:
            return False, f"Missing elements in Dockerfile: {missing}"
        
        return True, "Dockerfile.cloudrun is properly configured"
    
    def check_requirements(self) -> Tuple[bool, str]:
        """Check requirements files"""
        cloudrun_req = self.project_root / 'requirements-cloudrun.txt'
        standard_req = self.project_root / 'requirements.txt'
        
        # Use Cloud Run requirements if available, otherwise standard
        if cloudrun_req.exists():
            req_file = cloudrun_req
            req_name = "requirements-cloudrun.txt"
        else:
            req_file = standard_req
            req_name = "requirements.txt"
        
        if not req_file.exists():
            return False, f"{req_name} not found"
        
        # Check for heavy dependencies that should be removed
        content = req_file.read_text()
        heavy_deps = [
            'sentence-transformers',
            'transformers',
            'faiss-cpu',
            'spacy',
            'nltk'
        ]
        
        # Only check for uncommented dependencies
        lines = content.split('\n')
        active_deps = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        active_content = '\n'.join(active_deps)
        
        found_heavy = [dep for dep in heavy_deps if dep in active_content]
        
        if found_heavy:
            return False, f"Heavy dependencies found (should be removed): {found_heavy}"
        
        # Check for required dependencies
        required_deps = [
            'fastapi',
            'uvicorn',
            'google-cloud-aiplatform',
            'google-generativeai'
        ]
        
        missing_deps = [dep for dep in required_deps if dep not in active_content]
        
        if missing_deps:
            return False, f"Missing required dependencies: {missing_deps}"
        
        return True, f"Requirements in {req_name} are optimized for Cloud Run"
    
    def check_environment(self) -> Tuple[bool, str]:
        """Check environment configuration"""
        env_file = self.project_root / '.env.cloudrun'
        gcloudignore = self.project_root / '.gcloudignore'
        
        issues = []
        
        if not env_file.exists():
            issues.append(".env.cloudrun not found")
        
        if not gcloudignore.exists():
            issues.append(".gcloudignore not found")
        else:
            # Check gcloudignore content
            content = gcloudignore.read_text()
            required_ignores = [
                '__pycache__/',
                '*.log',
                '*.db',
                '.venv/',
                'docs/',
                'md files/'
            ]
            
            missing_ignores = [ignore for ignore in required_ignores if ignore not in content]
            if missing_ignores:
                issues.append(f"Missing .gcloudignore entries: {missing_ignores}")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "Environment configuration is complete"
    
    def check_app_structure(self) -> Tuple[bool, str]:
        """Check application structure"""
        required_files = [
            'main.py',
            'controllers/',
            'models/',
            'services/',
            'client/dist/'
        ]
        
        missing = []
        for item in required_files:
            path = self.project_root / item
            if not path.exists():
                missing.append(item)
        
        if missing:
            return False, f"Missing required files/directories: {missing}"
        
        # Check main.py for Cloud Run optimizations
        main_py = self.project_root / 'main.py'
        try:
            content = main_py.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = main_py.read_text(encoding='latin-1')
            except Exception as e:
                return False, f"Cannot read main.py: {e}"
        
        if 'GOOGLE_CLOUD_DEPLOYMENT' not in content:
            return False, "main.py missing Cloud Run environment detection"
        
        if 'fallback_lifespan' not in content:
            return False, "main.py missing fast startup configuration"
        
        return True, "Application structure is correct"
    
    def check_cloudrun_optimizations(self) -> Tuple[bool, str]:
        """Check Cloud Run specific optimizations"""
        # Check advanced_rag_service.py for lightweight mode
        rag_service = self.project_root / 'services' / 'advanced_rag_service.py'
        
        if rag_service.exists():
            try:
                content = rag_service.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = rag_service.read_text(encoding='latin-1')
                except Exception as e:
                    return False, f"Cannot read advanced_rag_service.py: {e}"
            
            if 'google_cloud_deployment' not in content.lower():
                return False, "advanced_rag_service.py missing Cloud Run optimization"
            
            if '_initialize_lightweight_models' not in content:
                return False, "advanced_rag_service.py missing lightweight model initialization"
        
        # Check for lightweight service manager
        lightweight_manager = self.project_root / 'services' / 'lightweight_service_manager.py'
        if not lightweight_manager.exists():
            return False, "lightweight_service_manager.py not found"
        
        return True, "Cloud Run optimizations are in place"
    
    def check_security(self) -> Tuple[bool, str]:
        """Check security configuration"""
        # Check that sensitive files are not included
        sensitive_files = [
            'google-cloud-credentials.json',
            'client_secret_*.json',
            'legal-saathi-*-firebase-adminsdk-*.json'
        ]
        
        found_sensitive = []
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                found_sensitive.append(str(file_path))
        
        if found_sensitive:
            return False, f"Sensitive files found (should be in environment variables): {found_sensitive}"
        
        return True, "No sensitive files found in deployment"
    
    def check_performance(self) -> Tuple[bool, str]:
        """Check performance optimizations"""
        # Check client build
        client_dist = self.project_root / 'client' / 'dist'
        if not client_dist.exists():
            return False, "Client build (client/dist) not found - run 'npm run build' first"
        
        # Check for development files that should be excluded
        dev_files = list(self.project_root.rglob('*.log')) + list(self.project_root.rglob('*.db'))
        
        if dev_files:
            return False, f"Development files found (should be cleaned): {[str(f) for f in dev_files[:5]]}"
        
        return True, "Performance optimizations are in place"
    
    def print_summary(self):
        """Print validation summary"""
        passed = sum(1 for _, success, _ in self.validation_results if success)
        total = len(self.validation_results)
        
        print(f"\n📊 Validation Summary: {passed}/{total} checks passed")
        print("=" * 50)
        
        for check_name, success, message in self.validation_results:
            status = "✅" if success else "❌"
            print(f"{status} {check_name}: {message}")
        
        if passed == total:
            print(f"\n🎉 All checks passed! Ready for Cloud Run deployment.")
            print(f"\nTo deploy, run:")
            print(f"  gcloud run deploy legal-saathi --source . --dockerfile Dockerfile.cloudrun --region us-central1")
        else:
            print(f"\n⚠️ {total - passed} issues need to be fixed before deployment.")


def main():
    """Main validation function"""
    validator = CloudRunValidator()
    
    success = validator.validate_deployment()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()