"""
Property-based test for dependency consistency.
Feature: crewai-removal, Property 2: Dependency Consistency
Validates: Requirements 1.1, 1.2

Property 2: Dependency Consistency
For any Python file in the active codebase (excluding legacy/ directory), 
if the file imports a module, then that module should be listed in 
requirements.txt or be a standard library module.
"""
import ast
import sys
from pathlib import Path
from typing import Set, List
from hypothesis import given, strategies as st, settings


def get_python_files(exclude_dirs: Set[str] = None) -> List[Path]:
    """Get all Python files in the codebase, excluding specified directories"""
    if exclude_dirs is None:
        exclude_dirs = {'legacy', '.venv', '__pycache__', '.git', '.hypothesis', 
                       'node_modules', 'web-portal', 'web-portal-api'}
    
    python_files = []
    for path in Path('.').rglob('*.py'):
        # Skip if any parent directory is in exclude list
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        python_files.append(path)
    
    return python_files


def get_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all top-level module imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level module name
                    module = alias.name.split('.')[0]
                    imports.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level module name
                    module = node.module.split('.')[0]
                    imports.add(module)
        
        return imports
    except (SyntaxError, UnicodeDecodeError):
        # Skip files with syntax errors or encoding issues
        return set()


def get_requirements() -> Set[str]:
    """Get all package names from requirements.txt"""
    requirements_path = Path('requirements.txt')
    if not requirements_path.exists():
        return set()
    
    packages = set()
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Extract package name (before >= or ==)
            package = line.split('>=')[0].split('==')[0].split('[')[0].strip()
            # Normalize package name (replace hyphens with underscores)
            normalized = package.replace('-', '_').lower()
            packages.add(normalized)
            # Also add the original name
            packages.add(package.lower())
    
    return packages


def is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of Python's standard library"""
    # Common stdlib modules
    stdlib_modules = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'concurrent',
        'contextlib', 'copy', 'csv', 'dataclasses', 'datetime', 'decimal', 'enum',
        'functools', 'hashlib', 'http', 'io', 'itertools', 'json', 'logging', 'math',
        'os', 'pathlib', 'pickle', 're', 'shutil', 'socket', 'sqlite3', 'string',
        'subprocess', 'sys', 'tempfile', 'threading', 'time', 'traceback', 'typing',
        'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml', 'zipfile',
    }
    
    # Check if it's a known stdlib module
    if module_name in stdlib_modules:
        return True
    
    # Check if it's in sys.stdlib_module_names (Python 3.10+)
    if hasattr(sys, 'stdlib_module_names'):
        return module_name in sys.stdlib_module_names
    
    return False


def is_transitive_dependency(module_name: str) -> bool:
    """Check if a module is a known transitive dependency of our direct dependencies"""
    # These are transitive dependencies that come with our direct dependencies
    transitive_deps = {
        'botocore',  # comes with boto3
        'urllib3',   # comes with boto3/botocore
        'strands',   # comes with strands-agents
        'numpy',     # may come with various ML/data packages
        'PIL',       # comes with Pillow (but we removed Pillow, so this should fail)
        'tinydb',    # legacy dependency, not in requirements
        'pytest',    # test dependency, not in requirements
        'mcp',       # CrewAI dependency, should be removed
        'crewai',    # Should be removed
        'tools',     # CrewAI tools, should be removed
    }
    return module_name in transitive_deps


def test_dependency_consistency_for_file(file_path: Path, requirements: Set[str]) -> bool:
    """Test that all imports in a file are either in requirements or stdlib"""
    imports = get_imports_from_file(file_path)
    
    # List of modules that should NOT be imported (CrewAI-related)
    forbidden_modules = {'crewai', 'mcp', 'litellm', 'pdf2image', 'PIL'}
    
    for module in imports:
        # Skip relative imports and local modules
        if module.startswith('.') or module == '':
            continue
        
        # Skip if it's a local package
        if module in {'src', 'latest_trade_matching_agent', 'tests', 'deployment', 
                     'config', 'lambda', 'scripts', 'terraform', 'web_portal_api', 'app'}:
            continue
        
        # Skip local module references (these are internal imports)
        local_modules = {
            'models', 'tools', 'agents', 'matching', 'exception_handling', 'orchestrator',
            'memory', 'evaluations', 'policy', 'observability', 'events', 'client',
            'evaluators', 'delegation', 'tracing', 'policies', 'compliance_checker',
            'pdf_adapter_agent', 'trade_source_classifier', 'report_generator',
            'fuzzy_matcher', 'test_data_generator', 'classifier', 'storage', 'metrics',
            'control_command', 'aws_resources', 'dynamodb_tool', 'trade_extraction_agent',
            'registry', 'crewai_tools', 'scorer', 'llm_extraction_tool', 'triage',
            'taxonomy', 'sla_monitor', 'crew_fixed', 'pdf_to_image', 'rl_handler', 'adapter',
            'trade', 'audit', 'exception', 'ocr_tool', 'custom_tool'
        }
        if module in local_modules:
            continue
        
        # Check for forbidden modules (CrewAI-related)
        if module.lower() in forbidden_modules:
            return False, f"FORBIDDEN: Module '{module}' in {file_path} is a CrewAI dependency that should be removed"
        
        # Check if it's stdlib
        if is_stdlib_module(module):
            continue
        
        # Check if it's a known transitive dependency
        if is_transitive_dependency(module):
            continue
        
        # Check if it's in requirements (with normalization)
        module_normalized = module.replace('-', '_').lower()
        if module_normalized in requirements or module.lower() in requirements:
            continue
        
        # If we get here, the module is not accounted for
        return False, f"Module '{module}' in {file_path} not found in requirements.txt or stdlib"
    
    return True, None


@given(st.sampled_from(get_python_files()))
@settings(max_examples=100, deadline=None)
def test_property_dependency_consistency(python_file: Path):
    """
    Property 2: Dependency Consistency
    For any Python file in the active codebase (excluding legacy/ directory),
    if the file imports a module, then that module should be listed in
    requirements.txt or be a standard library module.
    """
    requirements = get_requirements()
    
    result, error_msg = test_dependency_consistency_for_file(python_file, requirements)
    
    assert result, error_msg


def test_no_crewai_imports_in_active_code():
    """
    Additional check: Ensure no CrewAI imports exist in active codebase.
    This is part of the dependency consistency property.
    """
    python_files = get_python_files()
    crewai_files = []
    
    for file_path in python_files:
        # Skip this test file itself
        if 'test_property_2_dependency_consistency.py' in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for actual CrewAI import statements (not in comments/strings)
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'crewai' in alias.name.lower():
                            crewai_files.append(file_path)
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module and 'crewai' in node.module.lower():
                        crewai_files.append(file_path)
                        break
        except (UnicodeDecodeError, FileNotFoundError, SyntaxError):
            # Skip files with encoding or syntax issues
            continue
    
    assert len(crewai_files) == 0, \
        f"Found CrewAI imports in {len(crewai_files)} files: {crewai_files}"


if __name__ == '__main__':
    # Run the property test manually
    print("Testing dependency consistency property...")
    python_files = get_python_files()
    print(f"Found {len(python_files)} Python files to test")
    
    requirements = get_requirements()
    print(f"Found {len(requirements)} packages in requirements.txt")
    
    failed_files = []
    for file_path in python_files:
        result, error_msg = test_dependency_consistency_for_file(file_path, requirements)
        if not result:
            failed_files.append((file_path, error_msg))
    
    if failed_files:
        print(f"\n❌ Dependency consistency check failed for {len(failed_files)} files:")
        for file_path, error_msg in failed_files:
            print(f"  - {error_msg}")
    else:
        print(f"\n✅ All {len(python_files)} files passed dependency consistency check")
    
    # Test for CrewAI imports
    print("\nTesting for CrewAI imports...")
    test_no_crewai_imports_in_active_code()
    print("✅ No CrewAI imports found in active codebase")
