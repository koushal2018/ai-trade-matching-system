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

def create_tinydb_databases():
    """Initialize TinyDB databases for trade storage"""
    print("\n💾 Initializing TinyDB databases...")
    
    try:
        from tinydb import TinyDB
        
        # Create bank trade database
        bank_db_path = './storage/bank_trade_data.db'
        bank_db = TinyDB(bank_db_path)
        print(f"   ✓ {bank_db_path}")
        
        # Create counterparty trade database  
        counterparty_db_path = './storage/counterparty_trade_data.db'
        counterparty_db = TinyDB(counterparty_db_path)
        print(f"   ✓ {counterparty_db_path}")
        
        # Close databases
        bank_db.close()
        counterparty_db.close()
        
        print("   ✓ TinyDB databases initialized successfully")
        
    except ImportError:
        print("   ⚠️  TinyDB not installed - databases will be created on first run")
        print("      Install with: pip install tinydb")
    except Exception as e:
        print(f"   ❌ Error creating databases: {e}")



def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = ['crewai', 'openai', 'tinydb', 'pdf2image']
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
        print("   Then edit .env with your API keys")
        return False
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    if 'OPENAI_API_KEY=sk-' not in env_content:
        print("   ⚠️  OPENAI_API_KEY not configured in .env")
        print("   Add your OpenAI API key to .env file")
        return False
    
    print("   ✓ .env file configured")
    return True

def main():
    """Main setup function"""
    print("🚀 AI Trade Matching System Setup")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Initialize TinyDB databases
    create_tinydb_databases()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check environment
    env_ok = check_env_file()
    
    print("\n" + "=" * 40)
    print("📋 Setup Summary:")
    
    if deps_ok and env_ok:
        print("✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Ensure Poppler is installed (brew install poppler)")
        print("   2. Run: crewai run")
        print("   3. Check ./storage/ for results")
    else:
        print("⚠️  Setup completed with warnings")
        print("   Please address the issues above before running")
    
    print("\n📚 Documentation: README.md")
    print("🐛 Issues: https://github.com/yourusername/ai-trade-matching/issues")

if __name__ == "__main__":
    main()