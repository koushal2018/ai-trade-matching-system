"""
Property-based test for datetime deprecation elimination.
Feature: agent-issues-fix, Property 5: Datetime Deprecation Elimination
Validates: Requirements 3.1

Property 5: Datetime Deprecation Elimination
For all Python files in the deployment/ directory, there should be no occurrences
of datetime.utcnow() after the fix is applied.
"""
import os
import re
from pathlib import Path
from typing import List, Tuple


# Files specifically targeted by the agent-issues-fix spec (Task 1)
TARGETED_AGENT_FILES = [
    "deployment/pdf_adapter/pdf_adapter_agent_strands.py",
    "deployment/trade_extraction/agent.py",
    "deployment/exception_management/exception_management_agent_strands.py",
    "deployment/swarm_agentcore/http_agent_orchestrator.py",
    "deployment/orchestrator/orchestrator_agent_strands.py",
    "deployment/orchestrator/orchestrator_agent_strands_goal_based.py",
]


def find_deprecated_datetime_usage(directory: str = "deployment", targeted_only: bool = False) -> List[Tuple[str, int, str]]:
    """
    Scan all Python files in the specified directory for deprecated datetime.utcnow() usage.
    
    Args:
        directory: Directory to scan (relative to project root)
        targeted_only: If True, only scan the files specifically targeted by the spec
        
    Returns:
        List of tuples containing (file_path, line_number, line_content) for each occurrence
    """
    # Get project root (parent of tests directory)
    project_root = Path(__file__).parent.parent.parent
    target_dir = project_root / directory
    
    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {target_dir}")
    
    occurrences = []
    
    # Pattern to match datetime.utcnow() calls
    pattern = re.compile(r'datetime\.utcnow\s*\(\s*\)')
    
    if targeted_only:
        # Only scan the specific files targeted by the spec
        files_to_scan = [project_root / f for f in TARGETED_AGENT_FILES]
    else:
        # Walk through all Python files
        files_to_scan = list(target_dir.rglob("*.py"))
    
    for py_file in files_to_scan:
        # Skip __pycache__ and .venv directories
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue
        
        if not py_file.exists():
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.search(line):
                        # Get relative path for cleaner output
                        rel_path = py_file.relative_to(project_root)
                        occurrences.append((str(rel_path), line_num, line.strip()))
        except (UnicodeDecodeError, PermissionError):
            # Skip files that can't be read
            continue
    
    return occurrences


def test_property_no_deprecated_datetime_utcnow_targeted():
    """
    Property 5: Datetime Deprecation Elimination (Targeted Files)
    
    For the specific agent files targeted by the agent-issues-fix spec,
    there should be no occurrences of datetime.utcnow() after the fix is applied.
    
    This test scans only the files specified in Task 1 of the spec.
    
    **Feature: agent-issues-fix, Property 5: Datetime Deprecation Elimination**
    **Validates: Requirements 3.1**
    """
    occurrences = find_deprecated_datetime_usage("deployment", targeted_only=True)
    
    if occurrences:
        # Build detailed error message
        error_lines = [
            f"\nFound {len(occurrences)} occurrence(s) of deprecated datetime.utcnow() in targeted files:",
            ""
        ]
        for file_path, line_num, line_content in occurrences:
            error_lines.append(f"  {file_path}:{line_num}")
            error_lines.append(f"    {line_content}")
            error_lines.append("")
        
        error_lines.append("Fix: Replace datetime.utcnow() with datetime.now(timezone.utc)")
        error_lines.append("     Add 'from datetime import datetime, timezone' to imports")
        
        raise AssertionError("\n".join(error_lines))


def test_property_no_deprecated_datetime_utcnow_all():
    """
    Property 5: Datetime Deprecation Elimination (All Files)
    
    For all Python files in the deployment/ directory, there should be no occurrences
    of datetime.utcnow() after the fix is applied.
    
    This is a comprehensive test that scans all files.
    
    **Feature: agent-issues-fix, Property 5: Datetime Deprecation Elimination**
    **Validates: Requirements 3.1**
    """
    occurrences = find_deprecated_datetime_usage("deployment", targeted_only=False)
    
    if occurrences:
        # Build detailed error message
        error_lines = [
            f"\nFound {len(occurrences)} occurrence(s) of deprecated datetime.utcnow():",
            ""
        ]
        for file_path, line_num, line_content in occurrences:
            error_lines.append(f"  {file_path}:{line_num}")
            error_lines.append(f"    {line_content}")
            error_lines.append("")
        
        error_lines.append("Fix: Replace datetime.utcnow() with datetime.now(timezone.utc)")
        error_lines.append("     Add 'from datetime import datetime, timezone' to imports")
        
        raise AssertionError("\n".join(error_lines))


def test_property_timezone_import_present():
    """
    Verify that files using datetime.now(timezone.utc) have the proper import.
    
    This is a complementary test to ensure the fix was applied correctly.
    
    **Feature: agent-issues-fix, Property 5: Datetime Deprecation Elimination**
    **Validates: Requirements 3.2**
    """
    project_root = Path(__file__).parent.parent.parent
    target_dir = project_root / "deployment"
    
    # Pattern to match datetime.now(timezone.utc) usage
    usage_pattern = re.compile(r'datetime\.now\s*\(\s*timezone\.utc\s*\)')
    # Pattern to match proper import
    import_pattern = re.compile(r'from\s+datetime\s+import\s+.*timezone')
    
    files_missing_import = []
    
    for py_file in target_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            
            # Check if file uses datetime.now(timezone.utc)
            if usage_pattern.search(content):
                # Verify it has the proper import
                if not import_pattern.search(content):
                    rel_path = py_file.relative_to(project_root)
                    files_missing_import.append(str(rel_path))
        except (UnicodeDecodeError, PermissionError):
            continue
    
    if files_missing_import:
        error_msg = (
            f"\nFiles using datetime.now(timezone.utc) but missing 'timezone' import:\n"
            + "\n".join(f"  - {f}" for f in files_missing_import)
            + "\n\nFix: Add 'timezone' to the datetime import statement"
        )
        raise AssertionError(error_msg)


if __name__ == '__main__':
    print("="*80)
    print("Property 5: Datetime Deprecation Elimination")
    print("Feature: agent-issues-fix")
    print("Validates: Requirements 3.1, 3.2")
    print("="*80)
    print()
    
    # Run the targeted test first (files specified in Task 1)
    print("Scanning TARGETED agent files for deprecated datetime.utcnow() usage...")
    print("Files targeted by spec:")
    for f in TARGETED_AGENT_FILES:
        print(f"  - {f}")
    print()
    
    try:
        occurrences = find_deprecated_datetime_usage("deployment", targeted_only=True)
        
        if occurrences:
            print(f"\n❌ FAILED: Found {len(occurrences)} occurrence(s) of deprecated datetime.utcnow() in targeted files:\n")
            for file_path, line_num, line_content in occurrences:
                print(f"  {file_path}:{line_num}")
                print(f"    {line_content}")
                print()
            print("Fix: Replace datetime.utcnow() with datetime.now(timezone.utc)")
            print("     Add 'from datetime import datetime, timezone' to imports")
            exit(1)
        else:
            print("✅ PASSED: No deprecated datetime.utcnow() usage found in targeted files")
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        exit(1)
    
    # Run the import verification test
    print("\nVerifying timezone imports are present in targeted files...")
    try:
        test_property_timezone_import_present()
        print("✅ PASSED: All targeted files have proper timezone imports")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    # Also report on other files (informational)
    print("\n" + "-"*80)
    print("INFORMATIONAL: Scanning ALL deployment files...")
    print("-"*80)
    
    all_occurrences = find_deprecated_datetime_usage("deployment", targeted_only=False)
    if all_occurrences:
        print(f"\n⚠️  Found {len(all_occurrences)} occurrence(s) in OTHER files (not part of Task 1):")
        for file_path, line_num, line_content in all_occurrences:
            print(f"  {file_path}:{line_num}")
        print("\nThese files may need to be addressed in a future task.")
    else:
        print("✅ No deprecated datetime.utcnow() usage found in any deployment files")
    
    print("\n" + "="*80)
    print("✅ TARGETED TESTS PASSED")
    print("="*80)
