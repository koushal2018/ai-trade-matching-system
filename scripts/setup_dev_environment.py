#!/usr/bin/env python3
"""
Setup development environment to work with production AWS resources.
This script configures the local environment for safe development.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_symlink_to_env():
    """Create symlink from .env to .env.dev for development."""
    env_file = Path('.env')
    env_dev_file = Path('.env.dev')
    
    if env_file.exists():
        if env_file.is_symlink():
            print("✅ .env symlink already exists")
        else:
            print("⚠️  .env file exists but is not a symlink")
            backup = Path('.env.backup')
            env_file.rename(backup)
            print(f"   Backed up existing .env to {backup}")
    
    if not env_file.exists():
        env_file.symlink_to(env_dev_file)
        print("✅ Created .env -> .env.dev symlink")

def install_python_dependencies():
    """Install Python dependencies for development."""
    print("📦 Installing Python dependencies...")
    
    # Check if virtual environment exists
    venv_path = Path('.venv_new')
    if not venv_path.exists():
        print("   Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', '.venv_new'], check=True)
    
    # Install dependencies
    pip_cmd = ['.venv_new/bin/pip', 'install', '-r', 'requirements.txt']
    if os.name == 'nt':  # Windows
        pip_cmd[0] = '.venv_new\\Scripts\\pip.exe'
    
    subprocess.run(pip_cmd, check=True)
    print("✅ Python dependencies installed")

def install_frontend_dependencies():
    """Install frontend dependencies."""
    print("📦 Installing frontend dependencies...")
    
    web_portal_path = Path('web-portal')
    if web_portal_path.exists():
        subprocess.run(['npm', 'install'], cwd=web_portal_path, check=True)
        print("✅ Frontend dependencies installed")
    else:
        print("⚠️  web-portal directory not found")

def create_data_directory():
    """Create data directory for local testing."""
    data_dir = Path('data')
    if not data_dir.exists():
        data_dir.mkdir()
        print("✅ Created data directory for local testing")
    
    # Create subdirectories
    subdirs = ['COUNTERPARTY', 'BANK', 'MATCHED', 'EXCEPTIONS']
    for subdir in subdirs:
        (data_dir / subdir).mkdir(exist_ok=True)
    
    print("✅ Created data subdirectories")

def setup_git_hooks():
    """Setup git hooks for development workflow."""
    hooks_dir = Path('.git/hooks')
    
    # Pre-commit hook to run tests
    pre_commit_hook = hooks_dir / 'pre-commit'
    pre_commit_content = '''#!/bin/bash
# Pre-commit hook for AI Trade Matching System

echo "🔍 Running pre-commit checks..."

# Check if we're on dev branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "dev" ]; then
    echo "⚠️  Warning: You're not on the dev branch"
    echo "   Current branch: $current_branch"
    echo "   Consider switching to dev for feature work"
fi

# Run Python linting (if available)
if command -v flake8 &> /dev/null; then
    echo "   Running Python linting..."
    flake8 web-portal-api/ scripts/ --max-line-length=100 --ignore=E203,W503
fi

# Run frontend linting (if available)
if [ -d "web-portal" ] && command -v npm &> /dev/null; then
    echo "   Running frontend linting..."
    cd web-portal && npm run lint --silent && cd ..
fi

echo "✅ Pre-commit checks completed"
'''
    
    with open(pre_commit_hook, 'w') as f:
        f.write(pre_commit_content)
    
    pre_commit_hook.chmod(0o755)
    print("✅ Git pre-commit hook installed")

def main():
    """Main setup function."""
    print("🚀 Setting up Development Environment")
    print("=" * 50)
    print("This will configure your local environment to work with production AWS resources")
    print()
    
    try:
        # Create environment configuration
        create_symlink_to_env()
        print()
        
        # Install dependencies
        install_python_dependencies()
        print()
        
        install_frontend_dependencies()
        print()
        
        # Create directories
        create_data_directory()
        print()
        
        # Setup git hooks
        setup_git_hooks()
        print()
        
        print("=" * 50)
        print("🎉 Development Environment Setup Complete!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Verify AWS credentials: aws configure")
        print("2. Test production connection: python scripts/verify_production_connection.py")
        print("3. Start backend: cd web-portal-api && uvicorn app.main:app --reload")
        print("4. Start frontend: cd web-portal && npm start")
        print()
        print("⚠️  IMPORTANT: You're now connected to PRODUCTION resources!")
        print("   Be careful when testing - you're working with live data")
        
        return 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())