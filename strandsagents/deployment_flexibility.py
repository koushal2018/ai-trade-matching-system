"""
Deployment Flexibility Module

Provides flexible deployment configurations for different environments:
- VDI (Virtual Desktop Infrastructure) environments
- Standalone deployments without full AWS integration
- Laptop/local development configurations
- Restricted network environments with Stunnel/UV support
"""

import os
import sys
import json
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import socket
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class DeploymentEnvironment:
    """Configuration for different deployment environments"""
    environment_type: str  # "vdi", "standalone", "laptop", "aws_full"
    network_restrictions: bool
    local_resources_only: bool
    stunnel_enabled: bool
    uv_connectivity: bool
    ai_provider_fallback: str
    resource_constraints: Dict[str, Any]
    connectivity_options: Dict[str, Any]

@dataclass
class ResourceConstraints:
    """Resource constraints for different deployment types"""
    max_memory_mb: int
    max_cpu_cores: int
    max_concurrent_operations: int
    cache_size_mb: int
    batch_size_limit: int

class EnvironmentDetector:
    """Detects deployment environment and configures accordingly"""
    
    def __init__(self):
        self.platform_info = self._get_platform_info()
        self.network_info = self._get_network_info()
        self.aws_availability = self._check_aws_availability()
        
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform and system information"""
        return {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "user": os.getenv("USER", os.getenv("USERNAME", "unknown"))
        }
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Detect network configuration and restrictions"""
        network_info = {
            "has_internet": False,
            "proxy_detected": False,
            "restricted_network": False,
            "stunnel_available": False,
            "uv_available": False
        }
        
        try:
            # Test internet connectivity
            response = requests.get("https://httpbin.org/ip", timeout=5)
            network_info["has_internet"] = response.status_code == 200
        except:
            network_info["has_internet"] = False
        
        # Check for proxy configuration
        proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
        network_info["proxy_detected"] = any(os.getenv(var) for var in proxy_vars)
        
        # Check for Stunnel availability
        network_info["stunnel_available"] = self._check_command_available("stunnel")
        
        # Check for UV connectivity tools
        network_info["uv_available"] = self._check_command_available("uv")
        
        # Detect restricted network (corporate/VDI environment)
        network_info["restricted_network"] = (
            not network_info["has_internet"] or 
            network_info["proxy_detected"] or
            "vdi" in socket.gethostname().lower() or
            "corp" in socket.gethostname().lower()
        )
        
        return network_info
    
    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in the system"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _check_aws_availability(self) -> Dict[str, Any]:
        """Check AWS service availability and credentials"""
        aws_info = {
            "credentials_available": False,
            "bedrock_available": False,
            "sagemaker_available": False,
            "region": os.getenv("AWS_REGION", "us-east-1")
        }
        
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            # Check credentials
            try:
                session = boto3.Session()
                credentials = session.get_credentials()
                aws_info["credentials_available"] = credentials is not None
            except NoCredentialsError:
                aws_info["credentials_available"] = False
            
            if aws_info["credentials_available"]:
                # Check Bedrock availability
                try:
                    bedrock = boto3.client('bedrock', region_name=aws_info["region"])
                    bedrock.list_foundation_models()
                    aws_info["bedrock_available"] = True
                except:
                    aws_info["bedrock_available"] = False
                
                # Check SageMaker availability
                try:
                    sagemaker = boto3.client('sagemaker', region_name=aws_info["region"])
                    sagemaker.list_endpoints()
                    aws_info["sagemaker_available"] = True
                except:
                    aws_info["sagemaker_available"] = False
        
        except ImportError:
            logger.warning("boto3 not available, AWS services disabled")
        
        return aws_info
    
    def detect_environment_type(self) -> str:
        """Detect the deployment environment type"""
        hostname = self.platform_info["hostname"].lower()
        
        # VDI environment detection (highest priority)
        if any(indicator in hostname for indicator in ["vdi", "virtual", "citrix", "vmware"]):
            return "vdi"
        
        # Full AWS environment (check credentials and internet first)
        if (self.aws_availability["credentials_available"] and 
            self.network_info["has_internet"] and
            not self.network_info["restricted_network"]):
            return "aws_full"
        
        # Corporate/restricted environment
        if self.network_info["restricted_network"]:
            return "standalone"
        
        # Laptop/development environment (default for personal machines)
        if (self.platform_info["system"] in ["Darwin", "Windows"] and 
            not self.network_info["restricted_network"]):
            return "laptop"
        
        return "standalone"
    
    def get_deployment_config(self) -> DeploymentEnvironment:
        """Generate deployment configuration based on detected environment"""
        env_type = self.detect_environment_type()
        
        configs = {
            "vdi": self._get_vdi_config(),
            "standalone": self._get_standalone_config(),
            "laptop": self._get_laptop_config(),
            "aws_full": self._get_aws_full_config()
        }
        
        return configs.get(env_type, self._get_standalone_config())
    
    def _get_vdi_config(self) -> DeploymentEnvironment:
        """Configuration for VDI environments"""
        return DeploymentEnvironment(
            environment_type="vdi",
            network_restrictions=True,
            local_resources_only=True,
            stunnel_enabled=self.network_info["stunnel_available"],
            uv_connectivity=self.network_info["uv_available"],
            ai_provider_fallback="huggingface",
            resource_constraints={
                "max_memory_mb": 2048,
                "max_cpu_cores": 2,
                "max_concurrent_operations": 2,
                "cache_size_mb": 256,
                "batch_size_limit": 10
            },
            connectivity_options={
                "use_proxy": self.network_info["proxy_detected"],
                "stunnel_config": "/etc/stunnel/stunnel.conf" if self.network_info["stunnel_available"] else None,
                "timeout_seconds": 30,
                "retry_attempts": 3
            }
        )
    
    def _get_standalone_config(self) -> DeploymentEnvironment:
        """Configuration for standalone deployments"""
        return DeploymentEnvironment(
            environment_type="standalone",
            network_restrictions=self.network_info["restricted_network"],
            local_resources_only=True,
            stunnel_enabled=self.network_info["stunnel_available"],
            uv_connectivity=self.network_info["uv_available"],
            ai_provider_fallback="huggingface",
            resource_constraints={
                "max_memory_mb": 4096,
                "max_cpu_cores": 4,
                "max_concurrent_operations": 4,
                "cache_size_mb": 512,
                "batch_size_limit": 25
            },
            connectivity_options={
                "use_proxy": self.network_info["proxy_detected"],
                "local_model_cache": True,
                "offline_mode": not self.network_info["has_internet"],
                "timeout_seconds": 60,
                "retry_attempts": 2
            }
        )
    
    def _get_laptop_config(self) -> DeploymentEnvironment:
        """Configuration for laptop/development environments"""
        return DeploymentEnvironment(
            environment_type="laptop",
            network_restrictions=False,
            local_resources_only=False,
            stunnel_enabled=False,
            uv_connectivity=self.network_info["uv_available"],
            ai_provider_fallback="bedrock" if self.aws_availability["bedrock_available"] else "huggingface",
            resource_constraints={
                "max_memory_mb": 8192,
                "max_cpu_cores": 8,
                "max_concurrent_operations": 8,
                "cache_size_mb": 1024,
                "batch_size_limit": 50
            },
            connectivity_options={
                "use_proxy": False,
                "local_model_cache": True,
                "development_mode": True,
                "timeout_seconds": 120,
                "retry_attempts": 3
            }
        )
    
    def _get_aws_full_config(self) -> DeploymentEnvironment:
        """Configuration for full AWS environments"""
        return DeploymentEnvironment(
            environment_type="aws_full",
            network_restrictions=False,
            local_resources_only=False,
            stunnel_enabled=False,
            uv_connectivity=False,
            ai_provider_fallback="bedrock",
            resource_constraints={
                "max_memory_mb": 16384,
                "max_cpu_cores": 16,
                "max_concurrent_operations": 16,
                "cache_size_mb": 2048,
                "batch_size_limit": 100
            },
            connectivity_options={
                "use_proxy": False,
                "aws_optimized": True,
                "timeout_seconds": 300,
                "retry_attempts": 5
            }
        )

class DeploymentConfigManager:
    """Manages deployment configurations and adaptations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config", "deployment_config.json"
        )
        self.detector = EnvironmentDetector()
        self.current_config = None
        
    def load_or_detect_config(self) -> DeploymentEnvironment:
        """Load existing config or detect and create new one"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self.current_config = DeploymentEnvironment(**config_data)
                logger.info(f"Loaded deployment config from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, detecting environment")
                self.current_config = self.detector.get_deployment_config()
        else:
            self.current_config = self.detector.get_deployment_config()
            self.save_config()
        
        return self.current_config
    
    def save_config(self):
        """Save current configuration to file"""
        if self.current_config:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.current_config), f, indent=2)
            logger.info(f"Saved deployment config to {self.config_path}")
    
    def adapt_ai_provider_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt AI provider configuration based on deployment environment"""
        if not self.current_config:
            self.load_or_detect_config()
        
        adapted_config = base_config.copy()
        
        # Apply environment-specific adaptations
        if self.current_config.environment_type == "vdi":
            adapted_config.update({
                "provider_type": "huggingface",
                "local_model_cache": True,
                "offline_mode": True,
                "timeout_multiplier": 2.0,
                "batch_size": min(adapted_config.get("batch_size", 10), 5)
            })
        
        elif self.current_config.environment_type == "standalone":
            adapted_config.update({
                "provider_type": self.current_config.ai_provider_fallback,
                "local_model_cache": True,
                "fallback_enabled": True,
                "resource_constraints": self.current_config.resource_constraints
            })
        
        elif self.current_config.environment_type == "laptop":
            adapted_config.update({
                "provider_type": self.current_config.ai_provider_fallback,
                "development_mode": True,
                "verbose_logging": True,
                "cache_enabled": True
            })
        
        # Apply network-specific adaptations
        if self.current_config.network_restrictions:
            adapted_config.update({
                "use_proxy": self.current_config.connectivity_options.get("use_proxy", False),
                "timeout_seconds": self.current_config.connectivity_options.get("timeout_seconds", 30),
                "retry_attempts": self.current_config.connectivity_options.get("retry_attempts", 2)
            })
        
        # Apply Stunnel configuration if available
        if self.current_config.stunnel_enabled:
            adapted_config.update({
                "stunnel_config": self.current_config.connectivity_options.get("stunnel_config"),
                "secure_tunnel": True
            })
        
        return adapted_config
    
    def get_resource_limits(self) -> ResourceConstraints:
        """Get resource constraints for current environment"""
        if not self.current_config:
            self.load_or_detect_config()
        
        constraints = self.current_config.resource_constraints
        return ResourceConstraints(
            max_memory_mb=constraints.get("max_memory_mb", 4096),
            max_cpu_cores=constraints.get("max_cpu_cores", 4),
            max_concurrent_operations=constraints.get("max_concurrent_operations", 4),
            cache_size_mb=constraints.get("cache_size_mb", 512),
            batch_size_limit=constraints.get("batch_size_limit", 25)
        )

# Global deployment manager instance
deployment_manager = DeploymentConfigManager()

def get_deployment_config() -> DeploymentEnvironment:
    """Get current deployment configuration"""
    return deployment_manager.load_or_detect_config()

def adapt_config_for_environment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Adapt configuration for current deployment environment"""
    return deployment_manager.adapt_ai_provider_config(config)

def get_resource_constraints() -> ResourceConstraints:
    """Get resource constraints for current environment"""
    return deployment_manager.get_resource_constraints()


class FlexibleDeploymentManager:
    """Flexible deployment manager for different environments."""
    
    def __init__(self):
        """Initialize flexible deployment manager."""
        self.config_manager = DeploymentConfigManager()
        self.environment_detector = EnvironmentDetector()
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get configuration for specific environment."""
        environment_configs = {
            'aws': {
                'environment_type': 'aws_full',
                'network_restrictions': False,
                'local_resources_only': False,
                'ai_provider_fallback': 'bedrock',
                'resource_constraints': {
                    'max_memory_mb': 8192,
                    'max_cpu_cores': 8,
                    'max_concurrent_operations': 10,
                    'cache_size_mb': 2048,
                    'batch_size_limit': 1000
                }
            },
            'vdi': {
                'environment_type': 'vdi',
                'network_restrictions': True,
                'local_resources_only': True,
                'ai_provider_fallback': 'huggingface',
                'resource_constraints': {
                    'max_memory_mb': 4096,
                    'max_cpu_cores': 4,
                    'max_concurrent_operations': 4,
                    'cache_size_mb': 512,
                    'batch_size_limit': 25
                }
            },
            'standalone': {
                'environment_type': 'standalone',
                'network_restrictions': False,
                'local_resources_only': False,
                'ai_provider_fallback': 'huggingface',
                'resource_constraints': {
                    'max_memory_mb': 6144,
                    'max_cpu_cores': 6,
                    'max_concurrent_operations': 6,
                    'cache_size_mb': 1024,
                    'batch_size_limit': 100
                }
            },
            'laptop': {
                'environment_type': 'laptop',
                'network_restrictions': False,
                'local_resources_only': False,
                'ai_provider_fallback': 'bedrock',
                'resource_constraints': {
                    'max_memory_mb': 8192,
                    'max_cpu_cores': 8,
                    'max_concurrent_operations': 8,
                    'cache_size_mb': 1024,
                    'batch_size_limit': 50
                }
            }
        }
        
        return environment_configs.get(environment, environment_configs['aws'])
    
    def detect_current_environment(self) -> str:
        """Detect current deployment environment."""
        config = self.environment_detector.get_deployment_config()
        return config.environment_type
    
    def adapt_configuration(self, base_config: Dict[str, Any], target_environment: str) -> Dict[str, Any]:
        """Adapt configuration for target environment."""
        env_config = self.get_environment_config(target_environment)
        adapted_config = base_config.copy()
        
        # Apply environment-specific adaptations
        adapted_config.update(env_config)
        
        return adapted_config