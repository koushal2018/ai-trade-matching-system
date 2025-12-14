#!/usr/bin/env python3
"""
Setup script for AI Trade Matching System
Creates necessary directories and sample data for first-time setup
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'data/BANK',
        'data/COUNTERPARTY', 
        'storage',
        'tests',
        'logs'
    ]
    
    print("📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}/")

def check_aws_resources():
    """Check AWS resources are accessible"""
    print("\n☁️  Checking AWS resources...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Try to create S3 client
        s3_client = boto3.client('s3')
        print("   ✓ AWS credentials configured")
        
        # Check if S3 bucket exists
        bucket_name = os.getenv('S3_BUCKET_NAME', 'trade-matching-system-agentcore-production')
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"   ✓ S3 bucket accessible: {bucket_name}")
        except ClientError:
            print(f"   ⚠️  S3 bucket not found: {bucket_name}")
            print("      Run terraform apply to create infrastructure")
        
    except NoCredentialsError:
        print("   ⚠️  AWS credentials not configured")
        print("      Configure AWS credentials in .env file")
    except ImportError:
        print("   ⚠️  boto3 not installed")
        print("      Install with: pip install -r requirements.txt")
    except Exception as e:
        print(f"   ⚠️  Error checking AWS resources: {e}")



def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = ['strands', 'boto3', 'anthropic', 'bedrock_agentcore']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package}")
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("\n🔐 Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print("   ⚠️  .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then edit .env with your AWS credentials")
        return False
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    missing_vars = [var for var in required_vars if var not in env_content]
    
    if missing_vars:
        print(f"   ⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Add your AWS credentials to .env file")
        return False
    
    print("   ✓ .env file configured")
    return True

def main():
    """Main setup function"""
    print("🚀 AI Trade Matching System Setup")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check environment
    env_ok = check_env_file()
    
    # Check AWS resources
    check_aws_resources()
    
    print("\n" + "=" * 40)
    print("📋 Setup Summary:")
    
    if deps_ok and env_ok:
        print("✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Configure AWS credentials in .env file")
        print("   2. Run: terraform apply (to create infrastructure)")
        print("   3. Run: python deployment/swarm/trade_matching_swarm.py <pdf_path> --source-type BANK")
        print("   4. Check S3 bucket for results")
    else:
        print("⚠️  Setup completed with warnings")
        print("   Please address the issues above before running")
    
    print("\n📚 Documentation: README.md")
    print("🐛 Issues: https://github.com/yourusername/ai-trade-matching/issues")

if __name__ == "__main__":
    main()