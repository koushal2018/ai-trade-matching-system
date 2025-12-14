# Contributing to AI Trade Matching System

Thank you for your interest in contributing to the AI Trade Matching System! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- AWS Account with Bedrock access
- Git
- Basic understanding of:
  - Multi-agent systems
  - AWS services (S3, DynamoDB, Bedrock)
  - Financial trade processing concepts

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/ai-trade-matching-system.git
   cd ai-trade-matching-system
   ```

2. **Set Up Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure AWS**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes** - Fix issues in existing functionality
- **Feature enhancements** - Improve existing features
- **New features** - Add new capabilities
- **Documentation** - Improve or add documentation
- **Tests** - Add or improve test coverage
- **Performance** - Optimize existing code

### Areas for Contribution

#### High Priority
- **Agent Improvements**: Enhance existing agents with better error handling
- **Matching Algorithms**: Improve fuzzy matching accuracy
- **Web Dashboard**: Add new features to the React frontend
- **Testing**: Increase test coverage, especially integration tests
- **Documentation**: Improve setup guides and API documentation

#### Medium Priority
- **Performance Optimization**: Reduce processing time and token usage
- **Monitoring**: Add more comprehensive observability
- **Security**: Enhance security features and audit trails
- **Deployment**: Improve deployment automation and CI/CD

#### Future Enhancements
- **Multi-language Support**: Support for non-English documents
- **Additional File Formats**: Support for Excel, CSV, etc.
- **Machine Learning**: Improve matching with ML models
- **Integration**: Add support for more trading systems

## Pull Request Process

### Before Submitting

1. **Check existing issues** - Look for related issues or discussions
2. **Create an issue** - For significant changes, create an issue first
3. **Follow coding standards** - Ensure your code follows project conventions
4. **Add tests** - Include tests for new functionality
5. **Update documentation** - Update relevant documentation

### Submission Steps

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number
   ```

2. **Make your changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test categories
   pytest tests/unit/ -v
   pytest tests/integration/ -v
   pytest tests/e2e/ -v
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new matching algorithm"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**
```
feat(matching): add fuzzy matching for counterparty names
fix(pdf-adapter): handle corrupted PDF files gracefully
docs(readme): update installation instructions
test(matching): add unit tests for scoring algorithm
```

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. **Clear title** - Summarize the issue
2. **Environment details** - OS, Python version, AWS region
3. **Steps to reproduce** - Detailed steps to recreate the issue
4. **Expected behavior** - What should happen
5. **Actual behavior** - What actually happens
6. **Error messages** - Include full error messages and stack traces
7. **Sample data** - If applicable, provide sample files (sanitized)

### Feature Requests

For feature requests, please include:

1. **Use case** - Why is this feature needed?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - Other approaches you've considered
4. **Additional context** - Any other relevant information

## Development Workflow

### Code Organization

```
deployment/
├── swarm/             # Strands Swarm implementation
├── pdf_adapter/       # PDF processing agent
├── trade_extraction/  # Data extraction agent
├── trade_matching/    # Matching agent
└── exception_management/ # Exception handling agent

deployment/
├── swarm/             # Strands Swarm implementation
├── pdf_adapter/       # PDF processing agent
├── trade_extraction/  # Data extraction agent
├── trade_matching/    # Matching agent
└── exception_management/ # Exception handling agent
```

### Coding Standards

#### Python Code Style

- **PEP 8** compliance
- **Type hints** for all function parameters and return values
- **Docstrings** for all classes and functions (Google style)
- **Maximum line length**: 100 characters
- **Import organization**: Standard library, third-party, local imports

#### Example:

```python
from typing import Dict, List, Optional
import json
from datetime import datetime

from pydantic import BaseModel
import boto3

# Example imports would be from deployment agents
# from deployment.trade_extraction.trade_extraction_agent_strands import TradeExtractionAgent


class TradeProcessor:
    """Processes trade confirmations for matching.
    
    This class handles the extraction and processing of trade data
    from PDF confirmations using AWS Bedrock.
    
    Args:
        region_name: AWS region for Bedrock operations
        model_id: Bedrock model identifier
    """
    
    def __init__(self, region_name: str = "us-east-1", model_id: str = "amazon.nova-pro-v1:0"):
        self.region_name = region_name
        self.model_id = model_id
        self._bedrock_client = boto3.client("bedrock-runtime", region_name=region_name)
    
    def process_trade(self, pdf_content: bytes, source_type: str) -> Optional[Trade]:
        """Extract trade data from PDF content.
        
        Args:
            pdf_content: Raw PDF file content
            source_type: Either 'BANK' or 'COUNTERPARTY'
            
        Returns:
            Extracted trade data or None if extraction fails
            
        Raises:
            ValueError: If source_type is invalid
            ProcessingError: If PDF processing fails
        """
        if source_type not in ["BANK", "COUNTERPARTY"]:
            raise ValueError(f"Invalid source_type: {source_type}")
        
        # Implementation here...
        pass
```

#### Agent Development

- **Use Strands SDK** for new agents
- **Follow tool patterns** - Use `@tool` decorator for agent tools
- **Error handling** - Implement comprehensive error handling
- **Logging** - Use structured logging with appropriate levels
- **Configuration** - Use environment variables for configuration

#### Frontend Development (React)

- **TypeScript** - All new code should use TypeScript
- **Material-UI** - Use Material-UI components with theme tokens
- **AWS Design System** - Follow AWS design principles
- **Responsive design** - Ensure mobile compatibility
- **Accessibility** - Follow WCAG 2.1 AA guidelines

## Testing

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1 second per test)

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use real AWS services (with test data)
   - Moderate execution time (< 30 seconds per test)

3. **End-to-End Tests** (`tests/e2e/`)
   - Test complete workflows
   - Use sample PDF files
   - Longer execution time (< 5 minutes per test)

4. **Property-Based Tests** (`tests/property_based/`)
   - Test with generated data using Hypothesis
   - Verify invariants and edge cases

### Test Data

- **Use sanitized data** - No real financial information
- **Provide fixtures** - Create reusable test fixtures
- **Mock external services** - Mock AWS services in unit tests
- **Clean up resources** - Ensure tests clean up after themselves

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific categories
pytest tests/unit/ -v
pytest tests/integration/ -v --aws-profile test
pytest tests/e2e/ -v --aws-profile test

# With coverage
pytest tests/ --cov=src --cov-report=html

# Property-based tests
pytest tests/property_based/ -v --hypothesis-show-statistics
```

## Documentation

### Types of Documentation

1. **Code Documentation**
   - Docstrings for all public functions and classes
   - Type hints for better IDE support
   - Inline comments for complex logic

2. **API Documentation**
   - Update OpenAPI specs for API changes
   - Include examples and error responses

3. **User Documentation**
   - Update README.md for user-facing changes
   - Add to docs/ directory for detailed guides
   - Include screenshots for UI changes

4. **Developer Documentation**
   - Architecture decisions in docs/architecture/
   - Deployment guides in deployment/
   - Troubleshooting guides

### Documentation Standards

- **Clear and concise** - Write for your audience
- **Examples included** - Provide code examples
- **Up to date** - Keep documentation current with code changes
- **Searchable** - Use clear headings and structure

## Getting Help

### Community Support

- **GitHub Discussions** - For questions and general discussion
- **GitHub Issues** - For bug reports and feature requests
- **Documentation** - Check existing documentation first

### Maintainer Contact

For urgent issues or security concerns, contact the maintainers directly through GitHub.

## Recognition

Contributors will be recognized in:
- **CHANGELOG.md** - For significant contributions
- **README.md** - In the contributors section
- **Release notes** - For major features

Thank you for contributing to the AI Trade Matching System! 🚀