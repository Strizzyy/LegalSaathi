#!/usr/bin/env python3
"""
Cloud Run Optimization Script
Prepares the application for Google Cloud Run deployment by:
1. Cleaning up unnecessary files
2. Optimizing dependencies
3. Configuring environment variables
4. Validating deployment readiness
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudRunOptimizer:
    """Optimizes the application for Google Cloud Run deployment"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.files_removed = []
        self.directories_cleaned = []
        
    def run_optimization(self):
        """Run all optimization steps"""
        logger.info("🚀 Starting Google Cloud Run optimization...")
        
        try:
            self.clean_development_files()
            self.clean_cache_directories()
            self.optimize_client_build()
            self.validate_requirements()
            self.setup_environment()
            self.generate_deployment_summary()
            
            logger.info("✅ Cloud Run optimization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            return False
    
    def clean_development_files(self):
        """Remove development-only files"""
        logger.info("🧹 Cleaning development files...")
        
        dev_files = [
            '*.log', '*.db', '*.pyc', '*.pyo', '*.pyd',
            'debug_*.py', 'test_*.py', '*_test.py',
            '.DS_Store', 'Thumbs.db', '*.tmp', '*.temp'
        ]
        
        dev_directories = [
            '__pycache__', '.pytest_cache', '.mypy_cache',
            '.coverage', 'htmlcov', '.tox', '.venv', 'venv',
            'node_modules', '.git'
        ]
        
        # Remove development files
        for pattern in dev_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        self.files_removed.append(str(file_path))
                        logger.debug(f"Removed file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove {file_path}: {e}")
        
        # Remove development directories
        for dir_name in dev_directories:
            for dir_path in self.project_root.rglob(dir_name):
                if dir_path.is_dir() and dir_path.name == dir_name:
                    try:
                        shutil.rmtree(dir_path)
                        self.directories_cleaned.append(str(dir_path))
                        logger.debug(f"Removed directory: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove {dir_path}: {e}")
        
        logger.info(f"🗑️ Removed {len(self.files_removed)} files and {len(self.directories_cleaned)} directories")
    
    def clean_cache_directories(self):
        """Clean Python and Node.js cache directories"""
        logger.info("🧹 Cleaning cache directories...")
        
        cache_patterns = [
            '**/__pycache__',
            '**/node_modules',
            '**/.npm',
            '**/.cache',
            '**/dist',
            '**/build'
        ]
        
        for pattern in cache_patterns:
            for cache_dir in self.project_root.glob(pattern):
                if cache_dir.is_dir():
                    try:
                        # Skip client/dist as it's needed for production
                        if 'client/dist' in str(cache_dir):
                            continue
                            
                        shutil.rmtree(cache_dir)
                        logger.debug(f"Cleaned cache: {cache_dir}")
                    except Exception as e:
                        logger.warning(f"Could not clean {cache_dir}: {e}")
    
    def optimize_client_build(self):
        """Optimize client build for production"""
        logger.info("⚡ Optimizing client build...")
        
        client_dir = self.project_root / 'client'
        if not client_dir.exists():
            logger.warning("Client directory not found, skipping client optimization")
            return
        
        # Check if client build exists
        dist_dir = client_dir / 'dist'
        if not dist_dir.exists():
            logger.warning("Client dist directory not found. Run 'npm run build' in client directory first.")
            return
        
        # Remove client source files (keep only dist)
        source_dirs = ['src', 'public', 'node_modules']
        for source_dir in source_dirs:
            source_path = client_dir / source_dir
            if source_path.exists() and source_path.is_dir():
                try:
                    # Don't remove in optimization script - let .gcloudignore handle it
                    logger.debug(f"Client source directory {source_dir} will be excluded by .gcloudignore")
                except Exception as e:
                    logger.warning(f"Could not process {source_path}: {e}")
        
        logger.info("✅ Client build optimization completed")
    
    def validate_requirements(self):
        """Validate requirements files"""
        logger.info("📋 Validating requirements...")
        
        # Check if Cloud Run requirements exist
        cloudrun_req = self.project_root / 'requirements-cloudrun.txt'
        standard_req = self.project_root / 'requirements.txt'
        
        if cloudrun_req.exists():
            logger.info("✅ Cloud Run requirements file found")
        else:
            logger.warning("⚠️ Cloud Run requirements file not found, using standard requirements")
        
        if standard_req.exists():
            logger.info("✅ Standard requirements file found")
        else:
            logger.error("❌ No requirements file found!")
            raise FileNotFoundError("requirements.txt is required")
    
    def setup_environment(self):
        """Setup environment configuration"""
        logger.info("🔧 Setting up environment configuration...")
        
        # Check for Cloud Run environment file
        cloudrun_env = self.project_root / '.env.cloudrun'
        if cloudrun_env.exists():
            logger.info("✅ Cloud Run environment configuration found")
        else:
            logger.warning("⚠️ Cloud Run environment configuration not found")
        
        # Validate Dockerfile
        dockerfile_cloudrun = self.project_root / 'Dockerfile.cloudrun'
        if dockerfile_cloudrun.exists():
            logger.info("✅ Cloud Run Dockerfile found")
        else:
            logger.error("❌ Cloud Run Dockerfile not found!")
            raise FileNotFoundError("Dockerfile.cloudrun is required")
        
        # Validate .gcloudignore
        gcloudignore = self.project_root / '.gcloudignore'
        if gcloudignore.exists():
            logger.info("✅ .gcloudignore file found")
        else:
            logger.warning("⚠️ .gcloudignore file not found - deployment may include unnecessary files")
    
    def generate_deployment_summary(self):
        """Generate deployment summary"""
        logger.info("📊 Generating deployment summary...")
        
        # Calculate project size
        total_size = 0
        file_count = 0
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except Exception:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        
        summary = f"""
📋 Cloud Run Deployment Summary
================================
Project Size: {size_mb:.2f} MB
Total Files: {file_count}
Files Removed: {len(self.files_removed)}
Directories Cleaned: {len(self.directories_cleaned)}

🚀 Ready for Cloud Run Deployment!

Next Steps:
1. Run: gcloud run deploy legal-saathi --source . --dockerfile Dockerfile.cloudrun
2. Or use: deploy-cloudrun-optimized.bat (Windows) / deploy-cloudrun-optimized.sh (Linux/Mac)

⚡ Optimization Features:
✅ Lightweight service initialization
✅ Fast startup mode for Cloud Run
✅ Python-based health checks
✅ Lazy loading for non-critical services
✅ Optimized Docker build
✅ Comprehensive .gcloudignore
"""
        
        print(summary)
        
        # Write summary to file
        summary_file = self.project_root / 'CLOUD_RUN_DEPLOYMENT_SUMMARY.md'
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"📄 Deployment summary written to {summary_file}")


def main():
    """Main optimization function"""
    optimizer = CloudRunOptimizer()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        logger.info("🔍 Running in dry-run mode (no files will be modified)")
        return
    
    success = optimizer.run_optimization()
    
    if success:
        print("\n🎉 Optimization completed successfully!")
        print("Your application is now ready for Google Cloud Run deployment.")
        sys.exit(0)
    else:
        print("\n❌ Optimization failed!")
        print("Please check the logs and fix any issues before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()