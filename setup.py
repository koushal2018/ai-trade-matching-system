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

def create_sample_pdfs():
    """Create sample trade confirmation PDFs"""
    print("\n📄 Generating sample trade confirmations...")
    
    try:
        # Import the PDF creation code
        sys.path.append('./src')
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        create_bank_pdf()
        create_counterparty_pdf()
        
        print("   ✓ Sample PDFs created successfully")
        
    except ImportError as e:
        print(f"   ⚠️  Could not create sample PDFs: {e}")
        print("      Install reportlab: pip install reportlab")
    except Exception as e:
        print(f"   ❌ Error creating PDFs: {e}")

def create_bank_pdf():
    """Create bank-side sample PDF"""
    doc = SimpleDocTemplate(
        './data/BANK/FAB_26933659.pdf',
        pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=16, spaceAfter=30, alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    elements.append(Paragraph("FIRST ABU DHABI BANK", title_style))
    elements.append(Paragraph("DERIVATIVES TRADE CONFIRMATION", title_style))
    elements.append(Spacer(1, 20))
    
    # Trade details table
    trade_data = [
        ['Trade Reference:', 'FAB-DRV-2024-26933659'],
        ['Trade Date:', '2024-09-15'],
        ['Product:', 'Interest Rate Swap'],
        ['Notional:', 'USD 50,000,000'],
        ['Maturity:', '2029-09-17 (5 Years)'],
        ['Fixed Rate:', '3.750% (FAB pays)'],
        ['Floating Rate:', 'USD-SOFR + 0.25% (GSI pays)']
    ]
    
    table = Table(trade_data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Party information
    elements.append(Paragraph("COUNTERPARTIES", styles['Heading2']))
    party_data = [
        ['Bank:', 'First Abu Dhabi Bank PJSC'],
        ['LEI:', '254900O1WT2BXINOTE68'],  
        ['Counterparty:', 'Goldman Sachs International'],
        ['LEI:', '549300IYTZEDU5LF4J88'],
    ]
    
    party_table = Table(party_data, colWidths=[2*inch, 3*inch])
    party_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(party_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "Authorized by: Sarah Al-Mansouri, Director<br/>Date: 2024-09-15", 
        styles['Normal']
    ))
    
    doc.build(elements)

def create_counterparty_pdf():
    """Create counterparty-side sample PDF"""
    doc = SimpleDocTemplate(
        './data/COUNTERPARTY/GCS381315_V1.pdf',
        pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=16, spaceAfter=30, alignment=TA_CENTER,
        textColor=colors.darkred
    )
    
    elements.append(Paragraph("GOLDMAN SACHS INTERNATIONAL", title_style))
    elements.append(Paragraph("OTC DERIVATIVES CONFIRMATION", title_style))
    elements.append(Spacer(1, 20))
    
    # Trade details (slightly different perspective)
    trade_data = [
        ['GSI Reference:', 'GCS381315-V1'],
        ['Client Reference:', 'FAB-DRV-2024-26933659'],
        ['Trade Date:', '15-Sep-2024'],
        ['Product:', 'Interest Rate Swap'],
        ['Notional:', 'USD 50,000,000.00'],
        ['Termination:', '17-Sep-2029'],
        ['Fixed Rate:', '3.75000% (Client pays)'],
        ['Floating Rate:', 'USD-SOFR + 25bp (GS pays)']
    ]
    
    table = Table(trade_data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Counterparties
    elements.append(Paragraph("PARTIES", styles['Heading2']))
    party_data = [
        ['Goldman Sachs:', 'Goldman Sachs International'],
        ['LEI:', '549300IYTZEDU5LF4J88'],
        ['Client:', 'First Abu Dhabi Bank PJSC'], 
        ['LEI:', '254900O1WT2BXINOTE68'],
    ]
    
    party_table = Table(party_data, colWidths=[2*inch, 3*inch])
    party_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(party_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "Goldman Sachs International<br/>Authorized by: Marcus Richardson, Executive Director<br/>Date: 15 September 2024", 
        styles['Normal']
    ))
    
    doc.build(elements)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = ['crewai', 'openai', 'tinydb', 'pdf2image', 'reportlab']
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
    
    # Create sample PDFs
    create_sample_pdfs()
    
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