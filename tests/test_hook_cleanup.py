"""
Unit tests for hook cleanup - verifying CrewAI references are removed from active hooks.

**Validates: Requirements 7.1**
"""

import json
import os
from pathlib import Path


def test_hooks_dont_reference_crewai():
    """
    Test that active hooks don't reference CrewAI.
    
    **Validates: Requirements 7.1**
    """
    hooks_dir = Path(".kiro/hooks")
    assert hooks_dir.exists(), "Hooks directory should exist"
    
    hook_files = list(hooks_dir.glob("*.kiro.hook"))
    assert len(hook_files) > 0, "Should have at least one hook file"
    
    crewai_references = []
    
    for hook_file in hook_files:
        with open(hook_file, 'r') as f:
            content = f.read()
            hook_data = json.loads(content)
            
            # Check description for CrewAI references
            description = hook_data.get("description", "")
            if "crewai" in description.lower():
                crewai_references.append(f"{hook_file.name}: description contains 'CrewAI'")
            
            # Check prompt for CrewAI references
            if "then" in hook_data and "prompt" in hook_data["then"]:
                prompt = hook_data["then"]["prompt"]
                if "crewai" in prompt.lower():
                    crewai_references.append(f"{hook_file.name}: prompt contains 'CrewAI'")
            
            # Check file patterns for crew_fixed.py references
            if "when" in hook_data and "patterns" in hook_data["when"]:
                patterns = hook_data["when"]["patterns"]
                for pattern in patterns:
                    if "crew_fixed.py" in pattern:
                        crewai_references.append(f"{hook_file.name}: pattern references crew_fixed.py")
    
    assert len(crewai_references) == 0, (
        f"Found CrewAI references in active hooks:\n" + 
        "\n".join(crewai_references)
    )


def test_hooks_dont_reference_legacy_files():
    """
    Test that active hooks don't reference legacy CrewAI files.
    
    **Validates: Requirements 7.1**
    """
    hooks_dir = Path(".kiro/hooks")
    hook_files = list(hooks_dir.glob("*.kiro.hook"))
    
    legacy_file_references = []
    legacy_files = ["crew_fixed.py", "agents.yaml", "tasks.yaml"]
    
    for hook_file in hook_files:
        with open(hook_file, 'r') as f:
            content = f.read()
            hook_data = json.loads(content)
            
            # Check file patterns for legacy file references
            if "when" in hook_data and "patterns" in hook_data["when"]:
                patterns = hook_data["when"]["patterns"]
                for pattern in patterns:
                    for legacy_file in legacy_files:
                        if legacy_file in pattern and "legacy/" not in pattern:
                            legacy_file_references.append(
                                f"{hook_file.name}: pattern references {legacy_file}"
                            )
    
    assert len(legacy_file_references) == 0, (
        f"Found legacy file references in active hooks:\n" + 
        "\n".join(legacy_file_references)
    )


def test_hooks_only_reference_strands_and_agentcore():
    """
    Test that hooks reference only Strands SDK and AgentCore frameworks.
    
    **Validates: Requirements 7.1**
    """
    hooks_dir = Path(".kiro/hooks")
    hook_files = list(hooks_dir.glob("*.kiro.hook"))
    
    for hook_file in hook_files:
        with open(hook_file, 'r') as f:
            content = f.read()
            
            # If the hook mentions frameworks, it should only mention Strands/AgentCore
            if "framework" in content.lower() or "orchestration" in content.lower():
                # Should not mention CrewAI as a current option
                assert "crewai" not in content.lower() or "legacy" in content.lower(), (
                    f"{hook_file.name} mentions CrewAI without marking it as legacy"
                )
