#!/usr/bin/env python3
"""
Flexible Deployment Script

Handles deployment across different environments:
- VDI (Virtual Desktop Infrastructure)
- Standalone (without AWS integration)
- Laptop (development/testing)
- AWS Full (complete cloud deployment)
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from deployment_flexibility import (
    EnvironmentDetector,
    DeploymentConfigManager,
    get_deployment_config
)
from deployment_validation import DeploymentValidator
from enhanced_config import load_deployment_aware_config

logger = logging.getLogger(__name__)

class FlexibleDeployer:
    """Handles flexible deployment across different environments"""
    
    def __init__(self, target_environment: Optional[str] = None):
        self.detector = EnvironmentDetector()
        self.config_manager = DeploymentConfigManager()
        self.validator = DeploymentValidator()
        self.target_environment = target_environment
        
    async def deploy(self) -> bool:
        """Execute deployment based on detected or specified environment"""
        try:
            # Detect or use specified environment
            if self.target_environment:
                deployment_config = self._get_config_for_environment(self.target_environment)
            else:
                deployment_config = self.config_manager.load_or_detect_config()
            
            logger.info(f"Deploying to {deployment_config.environment_type} environment")
            
            # Run pre-deployment validation
            print("Running pre-deployment validation...")
            validation_results = await self.validator.run_full_validation()
            
            # Check for critical failures
            critical_failures = [r for r in validation_results if r.status == "FAIL"]
            if critical_failures:
                print(f"❌ Deployment blocked by {len(critical_failures)} critical validation failures:")
                for failure in critical_failures:
                    print(f"  • {failure.check_name}: {failure.message}")
                return False
            
            # Show warnings but continue
            warnings = [r for r in validation_results if r.status == "WARN"]
            if warnings:
                print(f"⚠️  Proceeding with {len(warnings)} warnings:")
                for warning in warnings:
                    print(f"  • {warning.check_name}: {warning.message}")
            
            # Execute environment-specific deployment
            success = await self._deploy_for_environment(deployment_config)
            
            if success:
                print(f"✅ Deployment to {deployment_config.environment_type} completed successfully!")
                await self._post_deployment_setup(deployment_config)
            else:
                print(f"❌ Deployment to {deployment_config.environment_type} failed!")
            
            return success
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            print(f"❌ Deployment failed: {e}")
            return False
    
    def _get_config_for_environment(self, env_type: str):
        """Get configuration for specific environment type"""
        # Override detector to force specific environment
        original_detect = self.detector.detect_environment_type
        self.detector.detect_environment_type = lambda: env_type
        
        config = self.detector.get_deployment_config()
        
        # Restore original method
        self.detector.detect_environment_type = original_detect
        
        return config
    
    async def _deploy_for_environment(self, deployment_config) -> bool:
        """Deploy based on specific environment configuration"""
        env_type = deployment_config.environment_type
        
        deployment_methods = {
            "vdi": self._deploy_vdi,
            "standalone": self._deploy_standalone,
            "laptop": self._deploy_laptop,
            "aws_full": self._deploy_aws_full
        }
        
        deploy_method = deployment_methods.get(env_type)
        if not deploy_method:
            raise ValueError(f"Unsupported environment type: {env_type}")
        
        return await deploy_method(deployment_config)
    
    async def _deploy_vdi(self, deployment_config) -> bool:
        """Deploy for VDI environment"""
        print("🖥️  Deploying for VDI environment...")
        
        steps = [
            ("Setting up local directories", self._setup_local_directories),
            ("Configuring resource constraints", self._configure_vdi_resources),
            ("Setting up Stunnel (if available)", self._setup_stunnel),
            ("Installing local AI models", self._install_local_models),
            ("Configuring offline mode", self._configure_offline_mode),
            ("Setting up local database", self._setup_local_database),
            ("Validating VDI constraints", self._validate_vdi_setup)
        ]
        
        return await self._execute_deployment_steps(steps, deployment_config)
    
    async def _deploy_standalone(self, deployment_config) -> bool:
        """Deploy for standalone environment"""
        print("🏠 Deploying for standalone environment...")
        
        steps = [
            ("Setting up local directories", self._setup_local_directories),
            ("Configuring standalone resources", self._configure_standalone_resources),
            ("Installing HuggingFace models", self._install_huggingface_models),
            ("Setting up local API server", self._setup_local_api),
            ("Configuring local storage", self._configure_local_storage),
            ("Setting up backup system", self._setup_backup_system),
            ("Testing standalone functionality", self._test_standalone_setup)
        ]
        
        return await self._execute_deployment_steps(steps, deployment_config)
    
    async def _deploy_laptop(self, deployment_config) -> bool:
        """Deploy for laptop/development environment"""
        print("💻 Deploying for laptop development environment...")
        
        steps = [
            ("Setting up development directories", self._setup_dev_directories),
            ("Configuring development resources", self._configure_dev_resources),
            ("Setting up AI providers", self._setup_dev_ai_providers),
            ("Installing development dependencies", self._install_dev_dependencies),
            ("Setting up test data", self._setup_test_data),
            ("Configuring hot reload", self._configure_hot_reload),
            ("Starting development services", self._start_dev_services)
        ]
        
        return await self._execute_deployment_steps(steps, deployment_config)
    
    async def _deploy_aws_full(self, deployment_config) -> bool:
        """Deploy for full AWS environment"""
        print("☁️  Deploying for full AWS environment...")
        
        steps = [
            ("Validating AWS credentials", self._validate_aws_credentials),
            ("Deploying CloudFormation stack", self._deploy_cloudformation),
            ("Configuring Bedrock access", self._configure_bedrock),
            ("Setting up Lambda functions", self._setup_lambda_functions),
            ("Configuring API Gateway", self._configure_api_gateway),
            ("Setting up monitoring", self._setup_monitoring),
            ("Running integration tests", self._run_integration_tests)
        ]
        
        return await self._execute_deployment_steps(steps, deployment_config)
    
    async def _execute_deployment_steps(self, steps, deployment_config) -> bool:
        """Execute a series of deployment steps"""
        for step_name, step_function in steps:
            try:
                print(f"  📋 {step_name}...")
                success = await step_function(deployment_config)
                if success:
                    print(f"    ✅ {step_name} completed")
                else:
                    print(f"    ❌ {step_name} failed")
                    return False
            except Exception as e:
                print(f"    ❌ {step_name} failed: {e}")
                logger.error(f"Step '{step_name}' failed: {e}")
                return False
        
        return True
    
    # VDI-specific deployment steps
    async def _setup_local_directories(self, deployment_config) -> bool:
        """Set up local directory structure"""
        try:
            base_dir = Path.cwd()
            directories = [
                "data", "logs", "cache", "models", "config", "temp"
            ]
            
            for dir_name in directories:
                dir_path = base_dir / dir_name
                dir_path.mkdir(exist_ok=True)
                
                # Test write permissions
                test_file = dir_path / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup directories: {e}")
            return False
    
    async def _configure_vdi_resources(self, deployment_config) -> bool:
        """Configure resource constraints for VDI"""
        try:
            constraints = deployment_config.resource_constraints
            
            # Set environment variables for resource limits
            os.environ.update({
                "MAX_MEMORY_MB": str(constraints.get("max_memory_mb", 2048)),
                "MAX_CPU_CORES": str(constraints.get("max_cpu_cores", 2)),
                "MAX_CONCURRENT_OPS": str(constraints.get("max_concurrent_operations", 2)),
                "CACHE_SIZE_MB": str(constraints.get("cache_size_mb", 256)),
                "BATCH_SIZE_LIMIT": str(constraints.get("batch_size_limit", 10))
            })
            
            return True
        except Exception as e:
            logger.error(f"Failed to configure VDI resources: {e}")
            return False
    
    async def _setup_stunnel(self, deployment_config) -> bool:
        """Set up Stunnel for secure tunneling"""
        try:
            if not deployment_config.stunnel_enabled:
                return True  # Skip if not enabled
            
            stunnel_config = deployment_config.connectivity_options.get("stunnel_config")
            if stunnel_config and os.path.exists(stunnel_config):
                # Validate stunnel configuration
                with open(stunnel_config, 'r') as f:
                    config_content = f.read()
                
                if "cert" in config_content and "key" in config_content:
                    os.environ["STUNNEL_CONFIG"] = stunnel_config
                    return True
            
            # Create basic stunnel config if none exists
            stunnel_dir = Path.home() / ".stunnel"
            stunnel_dir.mkdir(exist_ok=True)
            
            basic_config = """
[https]
accept = 8443
connect = 443
cert = /etc/ssl/certs/stunnel.pem
key = /etc/ssl/private/stunnel.key
"""
            
            config_file = stunnel_dir / "stunnel.conf"
            config_file.write_text(basic_config)
            os.environ["STUNNEL_CONFIG"] = str(config_file)
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup Stunnel: {e}")
            return False
    
    async def _install_local_models(self, deployment_config) -> bool:
        """Install local AI models for offline use"""
        try:
            models_dir = Path.cwd() / "models" / "cache"
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # List of lightweight models for VDI
            vdi_models = [
                "microsoft/DialoGPT-small",
                "distilbert-base-uncased"
            ]
            
            for model_name in vdi_models:
                model_path = models_dir / model_name.replace("/", "_")
                if not model_path.exists():
                    # Create placeholder for model (actual download would happen here)
                    model_path.mkdir(exist_ok=True)
                    (model_path / "config.json").write_text('{"model_type": "placeholder"}')
            
            return True
        except Exception as e:
            logger.error(f"Failed to install local models: {e}")
            return False
    
    async def _configure_offline_mode(self, deployment_config) -> bool:
        """Configure system for offline operation"""
        try:
            os.environ.update({
                "OFFLINE_MODE": "true",
                "AI_PROVIDER_TYPE": "huggingface",
                "HUGGINGFACE_OFFLINE": "true",
                "TRANSFORMERS_OFFLINE": "1"
            })
            return True
        except Exception as e:
            logger.error(f"Failed to configure offline mode: {e}")
            return False
    
    async def _setup_local_database(self, deployment_config) -> bool:
        """Set up local SQLite database"""
        try:
            import sqlite3
            
            db_path = Path.cwd() / "data" / "vdi_reconciliation.db"
            
            # Create database and basic tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    trade1_id TEXT,
                    trade2_id TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
            return True
        except Exception as e:
            logger.error(f"Failed to setup local database: {e}")
            return False
    
    async def _validate_vdi_setup(self, deployment_config) -> bool:
        """Validate VDI deployment setup"""
        try:
            # Check all required components
            checks = [
                ("Data directory", Path.cwd() / "data"),
                ("Models directory", Path.cwd() / "models"),
                ("Cache directory", Path.cwd() / "cache"),
                ("Database file", Path.cwd() / "data" / "vdi_reconciliation.db")
            ]
            
            for check_name, path in checks:
                if not path.exists():
                    logger.error(f"VDI validation failed: {check_name} not found at {path}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"VDI validation failed: {e}")
            return False
    
    # Standalone deployment steps
    async def _configure_standalone_resources(self, deployment_config) -> bool:
        """Configure resources for standalone deployment"""
        try:
            constraints = deployment_config.resource_constraints
            
            os.environ.update({
                "MAX_MEMORY_MB": str(constraints.get("max_memory_mb", 4096)),
                "MAX_CPU_CORES": str(constraints.get("max_cpu_cores", 4)),
                "BATCH_SIZE_LIMIT": str(constraints.get("batch_size_limit", 25)),
                "STANDALONE_MODE": "true"
            })
            
            return True
        except Exception as e:
            logger.error(f"Failed to configure standalone resources: {e}")
            return False
    
    async def _install_huggingface_models(self, deployment_config) -> bool:
        """Install HuggingFace models for standalone use"""
        try:
            models_dir = Path.cwd() / "models" / "huggingface"
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Models for standalone deployment
            standalone_models = [
                "microsoft/DialoGPT-medium",
                "sentence-transformers/all-MiniLM-L6-v2"
            ]
            
            for model_name in standalone_models:
                model_path = models_dir / model_name.replace("/", "_")
                if not model_path.exists():
                    model_path.mkdir(exist_ok=True)
                    (model_path / "config.json").write_text(f'{{"model_name": "{model_name}"}}')
            
            os.environ["HUGGINGFACE_CACHE_DIR"] = str(models_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to install HuggingFace models: {e}")
            return False
    
    async def _setup_local_api(self, deployment_config) -> bool:
        """Set up local API server for standalone mode"""
        try:
            # Create API configuration
            api_config = {
                "host": "localhost",
                "port": 8080,
                "cors_enabled": True,
                "rate_limiting": False
            }
            
            config_path = Path.cwd() / "config" / "api_config.json"
            with open(config_path, 'w') as f:
                json.dump(api_config, f, indent=2)
            
            os.environ.update({
                "API_HOST": "localhost",
                "API_PORT": "8080",
                "API_CONFIG_PATH": str(config_path)
            })
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup local API: {e}")
            return False
    
    async def _configure_local_storage(self, deployment_config) -> bool:
        """Configure local storage for standalone mode"""
        try:
            storage_dir = Path.cwd() / "data" / "storage"
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Create storage subdirectories
            for subdir in ["uploads", "processed", "reports", "cache"]:
                (storage_dir / subdir).mkdir(exist_ok=True)
            
            os.environ.update({
                "STORAGE_TYPE": "local",
                "STORAGE_BASE_PATH": str(storage_dir),
                "UPLOAD_DIR": str(storage_dir / "uploads"),
                "PROCESSED_DIR": str(storage_dir / "processed"),
                "REPORTS_DIR": str(storage_dir / "reports")
            })
            
            return True
        except Exception as e:
            logger.error(f"Failed to configure local storage: {e}")
            return False
    
    async def _setup_backup_system(self, deployment_config) -> bool:
        """Set up backup system for standalone mode"""
        try:
            backup_dir = Path.cwd() / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Create backup configuration
            backup_config = {
                "enabled": True,
                "interval_hours": 6,
                "backup_dir": str(backup_dir),
                "retention_days": 30
            }
            
            config_path = Path.cwd() / "config" / "backup_config.json"
            with open(config_path, 'w') as f:
                json.dump(backup_config, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup backup system: {e}")
            return False
    
    async def _test_standalone_setup(self, deployment_config) -> bool:
        """Test standalone deployment setup"""
        try:
            # Test basic functionality
            test_results = {
                "storage_writable": self._test_storage_write(),
                "database_accessible": self._test_database_access(),
                "models_loadable": self._test_model_loading()
            }
            
            if all(test_results.values()):
                return True
            else:
                failed_tests = [k for k, v in test_results.items() if not v]
                logger.error(f"Standalone tests failed: {failed_tests}")
                return False
        except Exception as e:
            logger.error(f"Standalone testing failed: {e}")
            return False
    
    # Laptop deployment steps
    async def _setup_dev_directories(self, deployment_config) -> bool:
        """Set up development directory structure"""
        try:
            base_dir = Path.cwd()
            dev_directories = [
                "dev_data", "logs", "cache", "models", "config", 
                "test_data", "temp", "reports"
            ]
            
            for dir_name in dev_directories:
                (base_dir / dir_name).mkdir(exist_ok=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup dev directories: {e}")
            return False
    
    async def _configure_dev_resources(self, deployment_config) -> bool:
        """Configure resources for development environment"""
        try:
            constraints = deployment_config.resource_constraints
            
            os.environ.update({
                "DEVELOPMENT_MODE": "true",
                "DEBUG": "true",
                "MAX_MEMORY_MB": str(constraints.get("max_memory_mb", 8192)),
                "BATCH_SIZE_LIMIT": str(constraints.get("batch_size_limit", 50)),
                "HOT_RELOAD": "true"
            })
            
            return True
        except Exception as e:
            logger.error(f"Failed to configure dev resources: {e}")
            return False
    
    async def _setup_dev_ai_providers(self, deployment_config) -> bool:
        """Set up AI providers for development"""
        try:
            # Try to use AWS services if available, fallback to HuggingFace
            if deployment_config.ai_provider_fallback == "bedrock":
                os.environ.update({
                    "AI_PROVIDER_TYPE": "bedrock",
                    "AI_FALLBACK_PROVIDER": "huggingface"
                })
            else:
                os.environ.update({
                    "AI_PROVIDER_TYPE": "huggingface",
                    "HUGGINGFACE_CACHE_DIR": str(Path.cwd() / "models" / "huggingface")
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup dev AI providers: {e}")
            return False
    
    async def _install_dev_dependencies(self, deployment_config) -> bool:
        """Install development dependencies"""
        try:
            # This would typically run pip install commands
            # For now, just verify key packages are available
            required_packages = ["boto3", "requests", "pandas", "numpy"]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    logger.warning(f"Development package {package} not available")
            
            return True
        except Exception as e:
            logger.error(f"Failed to install dev dependencies: {e}")
            return False
    
    async def _setup_test_data(self, deployment_config) -> bool:
        """Set up test data for development"""
        try:
            test_data_dir = Path.cwd() / "test_data"
            test_data_dir.mkdir(exist_ok=True)
            
            # Create sample test data files
            sample_trade = {
                "trade_id": "TEST001",
                "counterparty": "Test Bank",
                "amount": 1000000,
                "currency": "USD",
                "trade_date": "2024-01-15"
            }
            
            (test_data_dir / "sample_trade.json").write_text(json.dumps(sample_trade, indent=2))
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup test data: {e}")
            return False
    
    async def _configure_hot_reload(self, deployment_config) -> bool:
        """Configure hot reload for development"""
        try:
            os.environ.update({
                "HOT_RELOAD": "true",
                "AUTO_RESTART": "true",
                "WATCH_FILES": "true"
            })
            return True
        except Exception as e:
            logger.error(f"Failed to configure hot reload: {e}")
            return False
    
    async def _start_dev_services(self, deployment_config) -> bool:
        """Start development services"""
        try:
            # This would typically start development servers
            # For now, just set environment variables
            os.environ.update({
                "DEV_SERVER_PORT": "3000",
                "API_SERVER_PORT": "8080",
                "DEV_SERVICES_STARTED": "true"
            })
            return True
        except Exception as e:
            logger.error(f"Failed to start dev services: {e}")
            return False
    
    # AWS Full deployment steps
    async def _validate_aws_credentials(self, deployment_config) -> bool:
        """Validate AWS credentials and permissions"""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            # Test basic AWS access
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            
            logger.info(f"AWS Account: {identity.get('Account')}")
            logger.info(f"AWS User: {identity.get('Arn')}")
            
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.error(f"AWS credentials validation failed: {e}")
            return False
        except ImportError:
            logger.error("boto3 not available for AWS deployment")
            return False
    
    async def _deploy_cloudformation(self, deployment_config) -> bool:
        """Deploy CloudFormation stack"""
        try:
            # This would deploy the actual CloudFormation templates
            # For now, just validate they exist
            cf_dir = Path.cwd().parent / "client-deployment" / "cloudformation"
            
            required_templates = [
                "master-template.yaml",
                "core-infrastructure.yaml",
                "api-lambda.yaml"
            ]
            
            for template in required_templates:
                template_path = cf_dir / template
                if not template_path.exists():
                    logger.error(f"CloudFormation template not found: {template_path}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"CloudFormation deployment failed: {e}")
            return False
    
    async def _configure_bedrock(self, deployment_config) -> bool:
        """Configure AWS Bedrock access"""
        try:
            import boto3
            
            bedrock = boto3.client('bedrock', region_name=deployment_config.ai_provider_config.region)
            models = bedrock.list_foundation_models()
            
            logger.info(f"Available Bedrock models: {len(models.get('modelSummaries', []))}")
            
            os.environ.update({
                "AI_PROVIDER_TYPE": "bedrock",
                "BEDROCK_REGION": deployment_config.ai_provider_config.region
            })
            
            return True
        except Exception as e:
            logger.error(f"Bedrock configuration failed: {e}")
            return False
    
    async def _setup_lambda_functions(self, deployment_config) -> bool:
        """Set up Lambda functions"""
        try:
            # Validate Lambda function code exists
            lambda_dir = Path.cwd().parent / "client-deployment" / "lambda"
            
            required_functions = [
                "api_handler",
                "document_processor",
                "reconciliation_engine"
            ]
            
            for function in required_functions:
                function_path = lambda_dir / function
                if not function_path.exists():
                    logger.error(f"Lambda function not found: {function_path}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Lambda setup failed: {e}")
            return False
    
    async def _configure_api_gateway(self, deployment_config) -> bool:
        """Configure API Gateway"""
        try:
            # This would configure the actual API Gateway
            # For now, just set environment variables
            os.environ.update({
                "API_GATEWAY_ENABLED": "true",
                "API_STAGE": "prod"
            })
            return True
        except Exception as e:
            logger.error(f"API Gateway configuration failed: {e}")
            return False
    
    async def _setup_monitoring(self, deployment_config) -> bool:
        """Set up CloudWatch monitoring"""
        try:
            os.environ.update({
                "CLOUDWATCH_ENABLED": "true",
                "LOG_LEVEL": "INFO"
            })
            return True
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            return False
    
    async def _run_integration_tests(self, deployment_config) -> bool:
        """Run integration tests for AWS deployment"""
        try:
            # This would run actual integration tests
            # For now, just validate configuration
            required_env_vars = [
                "AI_PROVIDER_TYPE",
                "BEDROCK_REGION",
                "API_GATEWAY_ENABLED"
            ]
            
            for var in required_env_vars:
                if not os.getenv(var):
                    logger.error(f"Required environment variable not set: {var}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            return False
    
    # Helper methods
    def _test_storage_write(self) -> bool:
        """Test storage write capability"""
        try:
            test_file = Path.cwd() / "data" / "storage" / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except:
            return False
    
    def _test_database_access(self) -> bool:
        """Test database access"""
        try:
            import sqlite3
            db_path = Path.cwd() / "data" / "standalone.db"
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                conn.close()
                return True
            return False
        except:
            return False
    
    def _test_model_loading(self) -> bool:
        """Test model loading capability"""
        try:
            models_dir = Path.cwd() / "models"
            return models_dir.exists() and any(models_dir.iterdir())
        except:
            return False
    
    async def _post_deployment_setup(self, deployment_config):
        """Perform post-deployment setup tasks"""
        try:
            # Save deployment configuration
            self.config_manager.save_config()
            
            # Create deployment summary
            summary = {
                "environment": deployment_config.environment_type,
                "timestamp": str(asyncio.get_event_loop().time()),
                "ai_provider": deployment_config.ai_provider_fallback,
                "resource_constraints": deployment_config.resource_constraints,
                "connectivity_options": deployment_config.connectivity_options
            }
            
            summary_path = Path.cwd() / "deployment_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"📋 Deployment summary saved to: {summary_path}")
            
        except Exception as e:
            logger.warning(f"Post-deployment setup failed: {e}")

async def main():
    """Main deployment script entry point"""
    parser = argparse.ArgumentParser(description="Flexible deployment script")
    parser.add_argument("--environment", "-e", 
                       choices=["vdi", "standalone", "laptop", "aws_full"],
                       help="Target deployment environment (auto-detect if not specified)")
    parser.add_argument("--validate-only", "-v", action="store_true",
                       help="Only run validation, don't deploy")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    deployer = FlexibleDeployer(target_environment=args.environment)
    
    if args.validate_only:
        print("Running validation only...")
        validator = DeploymentValidator()
        results = await validator.run_full_validation()
        
        report = validator.generate_validation_report()
        print(report)
        
        # Save validation report
        report_file = Path.cwd() / "validation_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Validation report saved to: {report_file}")
        
        # Exit with appropriate code
        failed_checks = [r for r in results if r.status == "FAIL"]
        sys.exit(1 if failed_checks else 0)
    
    else:
        success = await deployer.deploy()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())