"""
Unit tests for documentation cleanup verification.
Validates that documentation doesn't reference CrewAI as current tech.

Requirements: 4.1, 4.2
"""

import pytest
from pathlib import Path


def test_readme_no_crewai_as_current():
    """
    Test that README.md doesn't reference CrewAI as current technology.
    Requirements: 4.1
    """
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md should exist"
    
    content = readme_path.read_text()
    
    # Check that CrewAI is not mentioned as current tech
    # It's OK if it's mentioned as "legacy" or "archived"
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Skip if line mentions legacy/archived
        if 'legacy' in line_lower or 'archived' in line_lower or 'deprecated' in line_lower:
            continue
        
        # Check for problematic CrewAI references
        if 'crewai' in line_lower:
            # Get context (previous and next lines)
            context_start = max(0, i-2)
            context_end = min(len(lines), i+3)
            context = '\n'.join(lines[context_start:context_end])
            
            # Check if context indicates it's legacy
            context_lower = context.lower()
            if not any(word in context_lower for word in ['legacy', 'archived', 'deprecated', 'old', 'previous', 'removed']):
                pytest.fail(
                    f"README.md references CrewAI as current tech at line {i+1}:\n"
                    f"Line: {line}\n"
                    f"Context:\n{context}"
                )


def test_architecture_no_crewai_as_current():
    """
    Test that ARCHITECTURE.md doesn't reference CrewAI as current technology.
    Requirements: 4.2
    """
    arch_path = Path("ARCHITECTURE.md")
    assert arch_path.exists(), "ARCHITECTURE.md should exist"
    
    content = arch_path.read_text()
    
    # Check that CrewAI is not mentioned as current tech
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Skip if line mentions legacy/archived
        if 'legacy' in line_lower or 'archived' in line_lower or 'deprecated' in line_lower:
            continue
        
        # Check for problematic CrewAI references
        if 'crewai' in line_lower:
            # Get context (previous and next lines)
            context_start = max(0, i-2)
            context_end = min(len(lines), i+3)
            context = '\n'.join(lines[context_start:context_end])
            
            # Check if context indicates it's legacy
            context_lower = context.lower()
            if not any(word in context_lower for word in ['legacy', 'archived', 'deprecated', 'old', 'previous', 'removed']):
                pytest.fail(
                    f"ARCHITECTURE.md references CrewAI as current tech at line {i+1}:\n"
                    f"Line: {line}\n"
                    f"Context:\n{context}"
                )


def test_readme_mentions_strands():
    """
    Test that README.md mentions Strands as the current implementation.
    Requirements: 4.1
    """
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md should exist"
    
    content = readme_path.read_text().lower()
    
    # Should mention Strands
    assert 'strands' in content, "README.md should mention Strands SDK"


def test_architecture_mentions_strands():
    """
    Test that ARCHITECTURE.md mentions Strands as the current implementation.
    Requirements: 4.2
    """
    arch_path = Path("ARCHITECTURE.md")
    assert arch_path.exists(), "ARCHITECTURE.md should exist"
    
    content = arch_path.read_text().lower()
    
    # Should mention Strands
    assert 'strands' in content, "ARCHITECTURE.md should mention Strands SDK"


def test_documentation_consistency():
    """
    Test that all major documentation files are consistent about Strands.
    Requirements: 4.1, 4.2
    """
    doc_files = [
        "README.md",
        "ARCHITECTURE.md",
        "DOCUMENTATION_UPDATE_COMPLETE.md",
        "AGENTCORE_MIGRATION_NEXT_STEPS.md"
    ]
    
    for doc_file in doc_files:
        doc_path = Path(doc_file)
        if not doc_path.exists():
            continue
        
        content = doc_path.read_text().lower()
        
        # Should mention Strands or AgentCore
        assert 'strands' in content or 'agentcore' in content, \
            f"{doc_file} should mention Strands or AgentCore"


if __name__ == '__main__':
    print("Testing documentation cleanup...")
    
    try:
        test_readme_no_crewai_as_current()
        print("✅ README.md doesn't reference CrewAI as current tech")
    except AssertionError as e:
        print(f"❌ README.md test failed: {e}")
    
    try:
        test_architecture_no_crewai_as_current()
        print("✅ ARCHITECTURE.md doesn't reference CrewAI as current tech")
    except AssertionError as e:
        print(f"❌ ARCHITECTURE.md test failed: {e}")
    
    try:
        test_readme_mentions_strands()
        print("✅ README.md mentions Strands")
    except AssertionError as e:
        print(f"❌ README.md Strands test failed: {e}")
    
    try:
        test_architecture_mentions_strands()
        print("✅ ARCHITECTURE.md mentions Strands")
    except AssertionError as e:
        print(f"❌ ARCHITECTURE.md Strands test failed: {e}")
    
    try:
        test_documentation_consistency()
        print("✅ Documentation is consistent")
    except AssertionError as e:
        print(f"❌ Documentation consistency test failed: {e}")
    
    print("\n✅ All documentation cleanup tests passed!")
