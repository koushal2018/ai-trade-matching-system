#!/usr/bin/env python3
"""
Test the trade matching system with sample data
Demonstrates the complete workflow from PDF extraction to matching
"""
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append('./src')

def run_trade_matching_demo():
    """Run a complete trade matching demonstration"""
    
    print("🚀 AI TRADE MATCHING SYSTEM DEMO")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import the crew after adding to path
        from latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent
        
        print("\n📋 DEMO SCENARIO: Asynchronous Trade Processing")
        print("Simulating real-world scenario where confirmations arrive at different times...")
        
        # Step 1: Process counterparty confirmation first
        print("\n" + "─" * 50)
        print("📨 STEP 1: Processing Counterparty Confirmation")
        print("📄 Document: Goldman Sachs confirmation (GCS381315_V1.pdf)")
        print("🕐 Time: 10:30 AM (First to arrive)")
        
        crew = LatestTradeMatchingAgent().crew()
        
        # Process Goldman Sachs PDF
        inputs_gsi = {
            'document_path': './data/COUNTERPARTY/GCS381315_V1.pdf'
        }
        
        result1 = crew.kickoff(inputs=inputs_gsi)
        print("✅ Counterparty confirmation processed")
        print("   Expected: Trade marked as 'PENDING - Awaiting bank confirmation'")
        
        # Step 2: Process bank confirmation later
        print("\n" + "─" * 50)
        print("📨 STEP 2: Processing Bank Confirmation")
        print("📄 Document: First Abu Dhabi Bank confirmation (FAB_26933659.pdf)")
        print("🕐 Time: 2:45 PM (Arrives 4 hours later)")
        
        # Process FAB PDF
        inputs_fab = {
            'document_path': './data/BANK/FAB_26933659.pdf'
        }
        
        result2 = crew.kickoff(inputs=inputs_fab)
        print("✅ Bank confirmation processed")
        print("   Expected: Automatic match with pending counterparty trade")
        
        # Step 3: Show final results
        print("\n" + "─" * 50)
        print("📊 FINAL RESULTS")
        show_results_summary()
        
        print("\n" + "=" * 50)
        print("🎯 DEMO COMPLETED SUCCESSFULLY!")
        print("Key Features Demonstrated:")
        print("  ✓ PDF extraction from both sides")
        print("  ✓ Asynchronous processing (pending → matched)")
        print("  ✓ Intelligent trade matching")
        print("  ✓ Local TinyDB storage")
        print("  ✓ Realistic derivatives workflow")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Ensure you've installed dependencies: pip install -r requirements.txt")
    
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        print("   Run setup first: python setup.py")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Check your .env file has valid OPENAI_API_KEY")

def show_results_summary():
    """Show summary of processing results"""
    try:
        # Check if databases exist and show stats
        import os
        from tinydb import TinyDB
        
        bank_db = './storage/bank_trade_data.db'
        counterparty_db = './storage/counterparty_trade_data.db'
        
        print("📈 Database Summary:")
        
        if os.path.exists(bank_db):
            db = TinyDB(bank_db)
            bank_trades = len(db.all())
            print(f"   Bank trades: {bank_trades}")
            db.close()
        else:
            print("   Bank trades: 0 (database not found)")
            
        if os.path.exists(counterparty_db):
            db = TinyDB(counterparty_db)
            cp_trades = len(db.all())
            print(f"   Counterparty trades: {cp_trades}")
            db.close()
        else:
            print("   Counterparty trades: 0 (database not found)")
            
        # Check for any generated files
        generated_files = []
        for file in ['matching_report.json', 'trade_data.json']:
            if os.path.exists(file):
                generated_files.append(file)
        
        if generated_files:
            print(f"📄 Generated files: {', '.join(generated_files)}")
        
        print("💾 Storage location: ./storage/")
        print("   View databases with any TinyDB viewer or Python script")
        
    except Exception as e:
        print(f"   Could not read database summary: {e}")

def check_prerequisites():
    """Check if system is ready to run demo"""
    print("🔍 Checking prerequisites...")
    
    issues = []
    
    # Check sample PDFs exist
    pdfs = [
        './data/BANK/FAB_26933659.pdf',
        './data/COUNTERPARTY/GCS381315_V1.pdf'
    ]
    
    for pdf in pdfs:
        if not os.path.exists(pdf):
            issues.append(f"Missing sample PDF: {pdf}")
    
    # Check .env file
    if not os.path.exists('.env'):
        issues.append("Missing .env file - copy from .env.example")
    
    # Check Python path
    if not os.path.exists('./src/latest_trade_matching_agent'):
        issues.append("Source code not found - check directory structure")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 Run setup first: python setup.py")
        return False
    
    print("✅ All prerequisites met")
    return True

if __name__ == "__main__":
    print("AI Trade Matching System - Demo")
    print("Testing complete workflow with sample trade confirmations\n")
    
    if check_prerequisites():
        run_trade_matching_demo()
    else:
        print("\n🔧 Please fix the issues above and try again")
        sys.exit(1)