# 🏦 AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI and AWS Nova**

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-green.svg)
![AWS Nova](https://img.shields.io/badge/AWS-Nova%20Pro-orange.svg)
![TinyDB](https://img.shields.io/badge/TinyDB-local%20storage-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

An intelligent system that automatically processes derivative trade confirmations using AWS Nova model for PDF extraction and multi-agent workflows for sophisticated trade matching.

## ⚠️ Disclaimer

**This is a personal educational project and has no affiliation, endorsement, or connection with any financial institutions, banks, or companies mentioned in the documentation or sample data. All bank names, trade references, and financial data used are purely fictional and for demonstration purposes only. This project is intended for learning and research purposes.**

## ✨ Key Features

- **📄 AI-Powered PDF Processing** - AWS Nova Pro model with multimodal capabilities for document analysis
- **🖼️ PDF-to-Image Pipeline** - High-quality image conversion for optimal OCR processing
- **🤖 Multi-Agent Architecture** - 4 specialized agents: Document Processor, Researcher, Reporting Analyst, Matching Analyst
- **💾 TinyDB Storage** - Lightweight local database with separate bank/counterparty tables
- **🔍 Intelligent Matching** - Professional-grade matching logic with tolerance handling
- **📊 Comprehensive Reports** - Detailed matching analysis with break identification
- **⚙️ Rate Limiting** - Built-in API rate limiting and execution timeouts

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Poppler (for PDF processing)
- AWS credentials configured (for Bedrock Nova model access)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-trade-matching.git
cd ai-trade-matching

# 2. Install system dependencies
# macOS:
brew install poppler

# Ubuntu/Debian:
sudo apt-get install poppler-utils

# 3. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env and add your AWS credentials

# 6. Run the system!
python -m src.latest_trade_matching_agent.main

# Or using CrewAI CLI
crewai run
```

## 📁 Project Structure

```
ai-trade-matching/
├── src/
│   └── latest_trade_matching_agent/
│       ├── config/
│       │   ├── agents.yaml          # AI agent definitions
│       │   └── tasks.yaml           # Task workflows
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── custom_tool.py       # Custom CrewAI tools
│       │   └── pdf_to_image.py      # PDF conversion tool
│       ├── crew_fixed.py            # Main orchestration
│       └── main.py                  # Entry point
├── data/
│   ├── BANK/                        # Bank confirmations (PDFs)
│   └── COUNTERPARTY/                # Counterparty confirmations (PDFs)
├── storage/                         # TinyDB databases (created at runtime)
├── tests/                           # Test suite
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
└── README.md                        # Documentation
```

## 🔄 How It Works

### Real-World Trade Processing

The system mimics real operations where confirmations arrive at different times:

```
Morning (10:30 AM):
📨 Goldman Sachs confirmation arrives
→ Extracted and stored
→ Status: "PENDING - Awaiting bank confirmation"

Afternoon (2:45 PM):
📨 First Abu Dhabi Bank confirmation arrives  
→ Automatic matching triggered
→ Both trades marked "MATCHED"
→ Match report generated
```

### The Processing Pipeline

1. **PDF Processing** → Document Processor converts PDF to high-quality images
2. **Data Extraction** → Researcher uses OCR and Nova model to extract trade details
3. **Data Storage** → Reporting Analyst stores structured data in TinyDB
4. **Trade Matching** → Matching Analyst performs intelligent matching with professional logic
5. **Report Generation** → Comprehensive matching analysis with break identification

## 🎯 Usage Examples

### Basic Usage
```bash
# Process trade confirmations
python -m src.latest_trade_matching_agent.main

# Or using CrewAI CLI
crewai run
```

### Custom Document Processing
```python
# In src/latest_trade_matching_agent/main.py
def run():
    document_path = './data/BANK/your_trade.pdf'
    unique_identifier = Path(document_path).stem + '_'
    
    inputs = {
        'document_path': document_path,
        'unique_identifier': unique_identifier
    }
    LatestTradeMatchingAgent().crew().kickoff(inputs=inputs)
```

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Required AWS (for Bedrock Nova model)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Optional (for alternative LLM providers)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=your-anthropic-key
```

### Agent Roles

| Agent | Role | Tools |
|-------|------|-------|
| **Document Processor** | Converts PDFs to images | PDFToImageTool, FileWriterTool |
| **Researcher** | Extracts trade data using OCR | OCRTool, FileReadTool, FileWriterTool |
| **Reporting Analyst** | Stores data in TinyDB | FileReadTool, FileWriterTool |
| **Matching Analyst** | Performs intelligent matching | FileReadTool, FileWriterTool |

## 📊 Sample Output

The system generates detailed matching reports with professional analysis:

```
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: ./data/BANK/FAB_26933659.pdf
📊 Total Pages: 3
🎯 DPI: 200
📸 Format: PNG
💾 Local Files: 3 files
   Folder: ./pdf_images
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready for OCR processing

Successfully created ./data/trade_data_FAB_26933659.json with comprehensive trade data

Stored trade FAB-26933659 in bank_trade_data.db
Action: inserted
Database record count: 1

Matching report saved to ./data/FAB_26933659_matching_report.md
Match rate: 85% (within expected range based on counterparty and data quality)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test basic functionality
pytest tests/test_basic.py

# Run with coverage
pytest --cov=src tests/
```

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Poppler not found** | Install: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux) |
| **AWS credentials error** | Configure AWS CLI or set environment variables in .env |
| **PDF conversion fails** | Ensure PDF is not password-protected and poppler is installed |
| **Import errors** | Run `pip install -r requirements.txt` |
| **Rate limiting** | Built-in rate limiting (2 RPM) - increase if needed in crew_fixed.py |

## 🎨 Customization

### Modify Document Path
```python
# In src/latest_trade_matching_agent/main.py
def run():
    document_path = './data/BANK/your_custom_file.pdf'  # Change this
    # ... rest of the function
```

### Adjust Rate Limits
```python
# In src/latest_trade_matching_agent/crew_fixed.py
@agent
def researcher(self) -> Agent:
    return Agent(
        # ...
        max_rpm=5,  # Increase from 2 if needed
        max_execution_time=900,  # Adjust timeout
        # ...
    )
```

## 📈 Performance

- ⚡ PDF conversion: ~2-3 seconds per page at 200 DPI
- 🤖 OCR extraction: 30-60 seconds per document (AWS Nova)
- 💾 TinyDB storage: <1 second per trade
- 🔍 Matching analysis: 10-30 seconds depending on complexity
- 🚦 Rate limiting: 2 RPM (configurable)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## 🙏 Acknowledgments

- [CrewAI](https://www.crewai.com/) - Multi-agent framework
- [AWS Bedrock](https://aws.amazon.com/bedrock/) - Nova Pro model API
- [TinyDB](https://tinydb.readthedocs.io/) - Lightweight database
- [pdf2image](https://github.com/Belval/pdf2image) - PDF to image conversion
- [Pillow](https://pillow.readthedocs.io/) - Image processing

## 📧 Contact

koushaldutt@gmail.com

---

**Built with ❤️ for derivatives operations teams worldwide**