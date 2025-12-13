"""
Unit tests for steering file cleanup - verifying CrewAI references are removed from steering files.

**Validates: Requirements 4.4, 4.5**
"""

from pathlib import Path


def test_tech_md_doesnt_list_crewai():
    """
    Test that tech.md doesn't list crewai in dependencies.
    
    **Validates: Requirements 4.4**
    """
    tech_file = Path(".kiro/steering/tech.md")
    assert tech_file.exists(), "tech.md should exist"
    
    content = tech_file.read_text()
    
    # Check that crewai is not listed in Key Libraries section
    assert "crewai" not in content.lower() or "legacy" in content.lower(), (
        "tech.md should not list crewai as a current dependency"
    )
    
    # Verify Strands SDK is listed
    assert "strands" in content.lower(), "tech.md should list Strands SDK"


def test_structure_md_doesnt_reference_crew_fixed():
    """
    Test that structure.md doesn't reference crew_fixed.py as an active file.
    
    **Validates: Requirements 4.5**
    """
    structure_file = Path(".kiro/steering/structure.md")
    assert structure_file.exists(), "structure.md should exist"
    
    content = structure_file.read_text()
    
    # If crew_fixed.py is mentioned, it should be in the legacy context
    if "crew_fixed.py" in content:
        # Find all occurrences and verify they're in legacy context
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "crew_fixed.py" in line:
                # Check surrounding context (within 5 lines) for "legacy" or "archived"
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 6)
                context = '\n'.join(lines[context_start:context_end]).lower()
                
                assert "legacy" in context or "archived" in context, (
                    f"crew_fixed.py mentioned on line {i+1} without legacy/archived context"
                )


def test_structure_md_doesnt_reference_yaml_configs():
    """
    Test that structure.md doesn't reference agents.yaml or tasks.yaml as active files.
    
    **Validates: Requirements 4.5**
    """
    structure_file = Path(".kiro/steering/structure.md")
    content = structure_file.read_text()
    
    yaml_files = ["agents.yaml", "tasks.yaml"]
    
    for yaml_file in yaml_files:
        if yaml_file in content:
            # Find all occurrences and verify they're in legacy context
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if yaml_file in line:
                    # Check surrounding context for "legacy" or "archived"
                    context_start = max(0, i - 5)
                    context_end = min(len(lines), i + 6)
                    context = '\n'.join(lines[context_start:context_end]).lower()
                    
                    assert "legacy" in context or "archived" in context, (
                        f"{yaml_file} mentioned on line {i+1} without legacy/archived context"
                    )


def test_structure_md_reflects_strands_implementation():
    """
    Test that structure.md reflects Strands-only implementation.
    
    **Validates: Requirements 4.5**
    """
    structure_file = Path(".kiro/steering/structure.md")
    content = structure_file.read_text()
    
    # Should mention Strands Swarm
    assert "strands swarm" in content.lower(), (
        "structure.md should mention Strands Swarm architecture"
    )
    
    # Should reference deployment directory
    assert "deployment/" in content, (
        "structure.md should reference deployment directory"
    )
    
    # Should have a legacy section
    assert "legacy" in content.lower(), (
        "structure.md should have a legacy section for archived code"
    )


def test_steering_files_mark_legacy_clearly():
    """
    Test that steering files clearly mark legacy systems as archived.
    
    **Validates: Requirements 4.7**
    """
    steering_dir = Path(".kiro/steering")
    steering_files = list(steering_dir.glob("*.md"))
    
    for steering_file in steering_files:
        content = steering_file.read_text()
        
        # If the file mentions CrewAI, it should be marked as legacy/archived
        if "crewai" in content.lower():
            # Check that it's in a legacy context
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "crewai" in line.lower():
                    # Get surrounding context
                    context_start = max(0, i - 10)
                    context_end = min(len(lines), i + 11)
                    context = '\n'.join(lines[context_start:context_end]).lower()
                    
                    # Should have legacy/archived/old/not used indicators
                    legacy_indicators = ["legacy", "archived", "old", "not used", "reference only"]
                    has_indicator = any(indicator in context for indicator in legacy_indicators)
                    
                    assert has_indicator, (
                        f"{steering_file.name} mentions CrewAI on line {i+1} "
                        f"without clear legacy/archived marking"
                    )
