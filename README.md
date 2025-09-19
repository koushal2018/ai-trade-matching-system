# 🏦 AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI and LLMs**

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-latest-green.svg)
![TinyDB](https://img.shields.io/badge/TinyDB-local%20storage-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

An intelligent, production-ready system that automatically processes derivative trade confirmations, extracting data from PDFs and performing sophisticated matching with real-world asynchronous processing.

## ⚠️ Disclaimer

**This is a personal educational project and has no affiliation, endorsement, or connection with any financial institutions, banks, or companies mentioned in the documentation or sample data. All bank names, trade references, and financial data used are purely fictional and for demonstration purposes only. This project is intended for learning and research purposes.**

## ✨ Key Features

- **📄 AI-Powered PDF Extraction** - Uses GPT-4 Vision to extract trade data from any format
- **🤖 Multi-Agent Architecture** - Specialized AI agents for extraction, storage, and matching
- **⚡ Real-time Matching** - Automatic matching when confirmations arrive asynchronously
- **💾 Local-First** - TinyDB for storage, no cloud dependencies required
- **⏳ Pending Management** - Trades wait intelligently for their counterparts
- **📊 Comprehensive Reports** - Detailed matching analysis with break identification
- **🔧 Production Ready** - Handles real-world edge cases and errors gracefully

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Poppler (for PDF processing)
- OpenAI API key (for GPT-4 Vision)

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
# Edit .env and add your OpenAI API key

# 6. Run setup to create sample data
python setup.py

# 7. Run the system!
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
│       │   └── trade_tools.py       # Custom CrewAI tools
│       ├── crew_fixed.py            # Main orchestration
│       └── main.py                  # Entry point
├── data/
│   ├── BANK/                        # Bank confirmations
│   └── COUNTERPARTY/                # Counterparty confirmations
├── storage/                         # Local databases
├── tests/                           # Test suite
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
├── setup.py                         # Setup script
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

### The Magic Behind the Scenes

1. **PDF arrives** → AI extracts all trade details
2. **Data stored** → TinyDB with automatic deduplication  
3. **Matching attempted** → Searches for counterpart
4. **Status updated** → Either "MATCHED" or "PENDING"
5. **Report generated** → Comprehensive matching analysis

## 🎯 Usage Examples

### Basic Usage
```bash
# Process trade confirmations
crewai run
```

### Custom Document Processing
```python
# In src/latest_trade_matching_agent/main.py
inputs = {
    'document_path': './data/BANK/your_trade.pdf'
}
```

### Test with Samples
```bash
# Generate and process sample trades
python test_matching.py
```

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-...your-key-here

# Optional AWS (for Bedrock LLMs)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Optional Anthropic
ANTHROPIC_API_KEY=...
```

### Agent Roles

| Agent | Role | Tools |
|-------|------|-------|
| **Researcher** | Extracts data from PDFs | PDFExtractorTool |
| **Reporting Analyst** | Stores in database | TradeStorageTool |
| **Matching Analyst** | Matches trades | TradeRetrievalTool, MatchingStatusTool |

## 📊 Sample Output

```
TRADE MATCHING STATUS REPORT
============================
Generated: 2024-09-15 14:45:22

SUMMARY:
--------
Bank Trades:
  Total: 5
  Matched: 4
  Pending: 1

Counterparty Trades:
  Total: 5
  Matched: 4
  Pending: 1

Match Rate: 80.0%

PENDING TRADES:
--------------
  • BANK: FAB-2024-78901 - PENDING - Awaiting counterparty
  • COUNTERPARTY: GS-2024-45678 - PENDING - Awaiting bank

RECOMMENDATIONS:
• Monitor for incoming confirmations
• Follow up on aged pending trades (>24 hours)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_extraction.py  # PDF extraction
pytest tests/test_matching.py    # Matching logic
pytest tests/test_storage.py     # Database operations
```

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Poppler not found** | Install: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux) |
| **API key error** | Check .env file has valid OPENAI_API_KEY |
| **PDF extraction fails** | Ensure PDF is not password-protected |
| **Import errors** | Run `pip install -r requirements.txt` |

## 🎨 Customization

### Add Custom Fields
```python
# In tools/trade_tools.py
def extract_custom_fields(self, trade_data):
    # Add your fields
    trade_data['custom_field'] = 'value'
    return trade_data
```

### New Matching Rules
```python
# In tools/trade_tools.py
def custom_matching_logic(self, trade1, trade2):
    # Your matching algorithm
    return confidence_score
```

## 📈 Performance

- ⚡ 5-10 seconds per PDF page
- 🎯 <1 second matching time
- 💾 Handles 10,000+ trades efficiently
- 🔄 Concurrent processing supported

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
- [OpenAI](https://openai.com/) - GPT-4 Vision API
- [TinyDB](https://tinydb.readthedocs.io/) - Lightweight database
- [pdf2image](https://github.com/Belval/pdf2image) - PDF processing

## 📧 Contact

koushaldutt@gmail.com

---

**Built with ❤️ for derivatives operations teams worldwide**