"""
Unit tests for CrewAI file removal.
Validates: Requirements 2.1, 2.2, 5.2, 5.3, 6.1
"""
import sys
from pathlib import Path


def test_crew_fixed_not_in_src():
    """Test that crew_fixed.py is not in src/latest_trade_matching_agent/"""
    crew_fixed_path = Path("src/latest_trade_matching_agent/crew_fixed.py")
    assert not crew_fixed_path.exists(), \
        "crew_fixed.py should not exist in src/latest_trade_matching_agent/"


def test_agents_yaml_not_in_config():
    """Test that agents.yaml is not in src/latest_trade_matching_agent/config/"""
    agents_yaml_path = Path("src/latest_trade_matching_agent/config/agents.yaml")
    assert not agents_yaml_path.exists(), \
        "agents.yaml should not exist in src/latest_trade_matching_agent/config/"


def test_tasks_yaml_not_in_config():
    """Test that tasks.yaml is not in src/latest_trade_matching_agent/config/"""
    tasks_yaml_path = Path("src/latest_trade_matching_agent/config/tasks.yaml")
    assert not tasks_yaml_path.exists(), \
        "tasks.yaml should not exist in src/latest_trade_matching_agent/config/"


def test_custom_tool_not_in_tools():
    """Test that custom_tool.py is not in src/latest_trade_matching_agent/tools/"""
    custom_tool_path = Path("src/latest_trade_matching_agent/tools/custom_tool.py")
    assert not custom_tool_path.exists(), \
        "custom_tool.py should not exist in src/latest_trade_matching_agent/tools/"


def test_ocr_tool_not_in_tools():
    """Test that ocr_tool.py is not in src/latest_trade_matching_agent/tools/"""
    ocr_tool_path = Path("src/latest_trade_matching_agent/tools/ocr_tool.py")
    assert not ocr_tool_path.exists(), \
        "ocr_tool.py should not exist in src/latest_trade_matching_agent/tools/"


def test_pdf_to_image_not_in_tools():
    """Test that pdf_to_image.py is not in src/latest_trade_matching_agent/tools/"""
    pdf_to_image_path = Path("src/latest_trade_matching_agent/tools/pdf_to_image.py")
    assert not pdf_to_image_path.exists(), \
        "pdf_to_image.py should not exist in src/latest_trade_matching_agent/tools/"


def test_crewai_test_files_not_in_root():
    """Test that CrewAI test files are not in project root"""
    test_files = [
        "test_property_1_functional_parity.py",
        "test_property_1_functional_parity_simple.py"
    ]
    
    for test_file in test_files:
        test_path = Path(test_file)
        assert not test_path.exists(), \
            f"{test_file} should not exist in project root"


def test_legacy_crewai_directory_exists():
    """Test that legacy/crewai/ directory exists"""
    legacy_dir = Path("legacy/crewai")
    assert legacy_dir.exists() and legacy_dir.is_dir(), \
        "legacy/crewai/ directory should exist"


def test_legacy_crewai_readme_exists():
    """Test that legacy/crewai/README.md exists and contains appropriate warnings"""
    readme_path = Path("legacy/crewai/README.md")
    assert readme_path.exists(), \
        "legacy/crewai/README.md should exist"
    
    content = readme_path.read_text()
    
    # Check for warning about archived code
    assert "archived" in content.lower() or "legacy" in content.lower(), \
        "README should mention that code is archived or legacy"
    
    # Check for warning about not being used in production
    assert "not used" in content.lower() or "deprecated" in content.lower(), \
        "README should warn that code is not used in production"


def test_crew_fixed_in_legacy():
    """Test that crew_fixed.py exists in legacy/crewai/"""
    crew_fixed_path = Path("legacy/crewai/crew_fixed.py")
    assert crew_fixed_path.exists(), \
        "crew_fixed.py should exist in legacy/crewai/"


def test_main_py_in_legacy():
    """Test that main.py exists in legacy/crewai/"""
    main_path = Path("legacy/crewai/main.py")
    assert main_path.exists(), \
        "main.py should exist in legacy/crewai/"


def test_agents_yaml_in_legacy():
    """Test that agents.yaml exists in legacy/crewai/config/"""
    agents_yaml_path = Path("legacy/crewai/config/agents.yaml")
    assert agents_yaml_path.exists(), \
        "agents.yaml should exist in legacy/crewai/config/"


def test_tasks_yaml_in_legacy():
    """Test that tasks.yaml exists in legacy/crewai/config/"""
    tasks_yaml_path = Path("legacy/crewai/config/tasks.yaml")
    assert tasks_yaml_path.exists(), \
        "tasks.yaml should exist in legacy/crewai/config/"


def test_custom_tool_in_legacy():
    """Test that custom_tool.py exists in legacy/crewai/tools/"""
    custom_tool_path = Path("legacy/crewai/tools/custom_tool.py")
    assert custom_tool_path.exists(), \
        "custom_tool.py should exist in legacy/crewai/tools/"


def test_ocr_tool_in_legacy():
    """Test that ocr_tool.py exists in legacy/crewai/tools/"""
    ocr_tool_path = Path("legacy/crewai/tools/ocr_tool.py")
    assert ocr_tool_path.exists(), \
        "ocr_tool.py should exist in legacy/crewai/tools/"


def test_pdf_to_image_in_legacy():
    """Test that pdf_to_image.py exists in legacy/crewai/tools/"""
    pdf_to_image_path = Path("legacy/crewai/tools/pdf_to_image.py")
    assert pdf_to_image_path.exists(), \
        "pdf_to_image.py should exist in legacy/crewai/tools/"


def test_functional_parity_test_in_legacy():
    """Test that test_property_1_functional_parity.py exists in legacy/crewai/tests/"""
    test_path = Path("legacy/crewai/tests/test_property_1_functional_parity.py")
    assert test_path.exists(), \
        "test_property_1_functional_parity.py should exist in legacy/crewai/tests/"


def test_functional_parity_simple_test_in_legacy():
    """Test that test_property_1_functional_parity_simple.py exists in legacy/crewai/tests/"""
    test_path = Path("legacy/crewai/tests/test_property_1_functional_parity_simple.py")
    assert test_path.exists(), \
        "test_property_1_functional_parity_simple.py should exist in legacy/crewai/tests/"



def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("crew_fixed.py not in src", test_crew_fixed_not_in_src),
        ("agents.yaml not in config", test_agents_yaml_not_in_config),
        ("tasks.yaml not in config", test_tasks_yaml_not_in_config),
        ("custom_tool.py not in tools", test_custom_tool_not_in_tools),
        ("ocr_tool.py not in tools", test_ocr_tool_not_in_tools),
        ("pdf_to_image.py not in tools", test_pdf_to_image_not_in_tools),
        ("CrewAI test files not in root", test_crewai_test_files_not_in_root),
        ("legacy/crewai/ directory exists", test_legacy_crewai_directory_exists),
        ("legacy/crewai/README.md exists", test_legacy_crewai_readme_exists),
        ("crew_fixed.py in legacy", test_crew_fixed_in_legacy),
        ("main.py in legacy", test_main_py_in_legacy),
        ("agents.yaml in legacy", test_agents_yaml_in_legacy),
        ("tasks.yaml in legacy", test_tasks_yaml_in_legacy),
        ("custom_tool.py in legacy", test_custom_tool_in_legacy),
        ("ocr_tool.py in legacy", test_ocr_tool_in_legacy),
        ("pdf_to_image.py in legacy", test_pdf_to_image_in_legacy),
        ("functional_parity test in legacy", test_functional_parity_test_in_legacy),
        ("functional_parity_simple test in legacy", test_functional_parity_simple_test_in_legacy),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    print("=" * 80)
    print("Running CrewAI File Removal Tests")
    print("Validates: Requirements 2.1, 2.2, 5.2, 5.3, 6.1")
    print("=" * 80)
    print()
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ PASS: {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {e}")
            failed += 1
            errors.append((test_name, str(e)))
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   Error: {e}")
            failed += 1
            errors.append((test_name, str(e)))
    
    print()
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed > 0:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
