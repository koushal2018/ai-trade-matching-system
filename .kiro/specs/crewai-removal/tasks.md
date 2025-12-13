# Implementation Plan: CrewAI Removal

- [x] 1. Update dependency files to remove CrewAI
  - Remove crewai, crewai-tools, litellm, mcp, pdf2image, and Pillow from requirements.txt
  - Update pyproject.toml if it exists to remove CrewAI dependencies
  - Verify the dependency list is clean and only contains actively used packages
  - _Requirements: 1.1, 1.2_

- [x] 1.1 Write unit test for dependency removal
  - Test that requirements.txt doesn't contain crewai or crewai-tools
  - Test that pyproject.toml doesn't contain crewai dependencies
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Write property test for dependency consistency
  - **Property 2: Dependency Consistency**
  - **Validates: Requirements 1.1, 1.2**

- [x] 1.3 Test installation succeeds
  - Run `pip install -e .` to verify installation works
  - Verify no CrewAI packages are installed
  - _Requirements: 1.3, 1.4_

- [x] 2. Create legacy archive directory structure
  - Create `legacy/crewai/` directory
  - Create subdirectories: `config/`, `tools/`, `tests/`
  - Write `legacy/crewai/README.md` explaining the archived code and why it's not used
  - _Requirements: 5.1, 5.4_

- [x] 2.1 Write unit test for legacy directory structure
  - Test that legacy/crewai/ directory exists
  - Test that legacy/crewai/README.md exists and contains appropriate warnings
  - _Requirements: 5.1, 5.4_

- [x] 3. Move CrewAI implementation files to archive
  - Move `src/latest_trade_matching_agent/crew_fixed.py` to `legacy/crewai/`
  - Move `src/latest_trade_matching_agent/main.py` to `legacy/crewai/`
  - Move `src/latest_trade_matching_agent/config/agents.yaml` to `legacy/crewai/config/`
  - Move `src/latest_trade_matching_agent/config/tasks.yaml` to `legacy/crewai/config/`
  - Verify files are preserved in archive
  - _Requirements: 5.2, 5.3_

- [x] 4. Move CrewAI tool files to archive
  - Move `src/latest_trade_matching_agent/tools/custom_tool.py` to `legacy/crewai/tools/`
  - Move `src/latest_trade_matching_agent/tools/ocr_tool.py` to `legacy/crewai/tools/`
  - Move `src/latest_trade_matching_agent/tools/pdf_to_image.py` to `legacy/crewai/tools/`
  - Review `src/latest_trade_matching_agent/tools/trade_source_classifier.py` for CrewAI dependencies
  - If trade_source_classifier.py has CrewAI code, create a clean version and archive the old one
  - _Requirements: 2.3_

- [x] 5. Move CrewAI test files to archive
  - Move `test_property_1_functional_parity.py` to `legacy/crewai/tests/`
  - Move `test_property_1_functional_parity_simple.py` to `legacy/crewai/tests/`
  - Verify test files are preserved in archive
  - _Requirements: 6.1_

- [x] 5.1 Write unit tests for file removal
  - Test that crew_fixed.py is not in src/latest_trade_matching_agent/
  - Test that agents.yaml and tasks.yaml are not in config/
  - Test that CrewAI tool files are not in tools/
  - Test that CrewAI test files are not in project root
  - Test that all files exist in legacy/crewai/
  - _Requirements: 2.1, 2.2, 5.2, 5.3, 6.1_

- [x] 6. Update eks_main.py to remove CrewAI code
  - Remove `from .crew_fixed import LatestTradeMatchingAgent` import
  - Remove `from crewai_tools import MCPServerAdapter` import
  - Remove `from mcp import StdioServerParameters` import
  - Remove `CREWAI_AVAILABLE` flag and all conditional logic
  - Remove CrewAI processing code path in `process_document_async()`
  - Remove simulation mode fallback logic
  - Remove MCP DynamoDB server setup code
  - Simplify the function to only handle health/readiness checks or remove entirely if not used
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6.1 Write unit tests for eks_main.py cleanup
  - Test that eks_main.py doesn't import crew_fixed
  - Test that eks_main.py doesn't import crewai_tools
  - Test that eks_main.py doesn't contain CREWAI_AVAILABLE
  - Test that eks_main.py doesn't contain simulation mode logic
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 6.2 Test API starts successfully
  - Start the web portal API if it's still used
  - Verify it starts without import errors
  - _Requirements: 8.4_

- [-] 7. Search and remove remaining CrewAI imports
  - Search codebase for "from crewai" and "import crewai"
  - Remove any remaining CrewAI imports in active code
  - Update any files that have indirect CrewAI dependencies
  - _Requirements: 2.4, 2.5_

- [x] 7.1 Write property test for CrewAI import absence
  - **Property 1: CrewAI Import Absence**
  - **Validates: Requirements 2.4, 2.5**

- [x] 8. Update steering file: tech.md
  - Remove crewai and crewai-tools from Key Libraries section
  - Remove litellm, mcp, pdf2image, Pillow from dependencies
  - Remove any CrewAI-related configuration or commands
  - Ensure only Strands SDK and AWS services are listed as current tech
  - _Requirements: 4.4_

- [x] 9. Update steering file: structure.md
  - Remove references to crew_fixed.py as a key file in Directory Organization section
  - Remove references to agents.yaml and tasks.yaml in Directory Organization section
  - Remove "Custom CrewAI tools" text from tools/ directory description
  - Update Legacy Code section to clarify these files are archived, not active
  - Ensure structure reflects Strands-only implementation
  - _Requirements: 4.5_

- [x] 9.1 Write unit tests for steering file cleanup
  - Test that tech.md doesn't list crewai in dependencies
  - Test that structure.md doesn't reference crew_fixed.py
  - Test that structure.md doesn't reference agents.yaml or tasks.yaml
  - _Requirements: 4.4, 4.5_

- [x] 10. Update documentation files
  - Search README.md for CrewAI references and remove or mark as legacy
  - Search ARCHITECTURE.md for CrewAI references and remove or mark as legacy
  - Search DOCUMENTATION_UPDATE_COMPLETE.md and update to reflect CrewAI removal
  - Search AGENTCORE_MIGRATION_NEXT_STEPS.md and mark CrewAI tasks as complete
  - Ensure all documentation reflects Strands as the only implementation
  - _Requirements: 4.1, 4.2_

- [x] 10.1 Write unit tests for documentation cleanup
  - Test that README.md doesn't reference CrewAI as current tech
  - Test that ARCHITECTURE.md doesn't reference CrewAI as current tech
  - _Requirements: 4.1, 4.2_

- [x] 11. Update task files to mark CrewAI tasks as not applicable
  - Open `.kiro/specs/agentcore-migration/tasks.md`
  - Find Property 1 (CrewAI functional parity) tasks
  - Mark them as "Not applicable - CrewAI deprecated"
  - Update any other CrewAI-related tasks
  - _Requirements: 4.6, 6.4_

- [x] 12. Update hooks to remove CrewAI references
  - Update `agentcore-mcp-guide.kiro.hook` to remove CrewAI mentions from description and guidance text
  - Remove references to crew_fixed.py from the hook guidance
  - Ensure hooks only reference Strands SDK and AgentCore
  - _Requirements: 7.1_

- [x] 12.1 Write unit test for hook cleanup
  - Test that active hooks don't reference CrewAI
  - _Requirements: 7.1_

- [x] 13. Review and clean up remaining tool files
  - Check `src/latest_trade_matching_agent/tools/dynamodb_tool.py` for CrewAI dependencies
  - Check `src/latest_trade_matching_agent/tools/llm_extraction_tool.py` for CrewAI dependencies
  - Remove or refactor any tools that depend on CrewAI BaseTool
  - Ensure all remaining tools are used by the Strands implementation
  - _Requirements: 2.3_

- [x] 14. Checkpoint - Verify no CrewAI imports remain
  - Run grep search for "from crewai" and "import crewai" in active code
  - Verify zero results (excluding legacy/ directory)
  - Run property test for CrewAI import absence
  - _Requirements: 2.4, 2.5_

- [x] 15. Run full test suite
  - Execute all unit tests
  - Execute all property tests
  - Verify all tests pass (except removed CrewAI parity tests)
  - Fix any broken tests that depend on removed code
  - _Requirements: 8.3_

- [ ]* 15.1 Write property test for system functionality preservation
  - **Property 3: System Functionality Preservation**
  - **Validates: Requirements 8.2, 8.5**

- [x] 16. Test Strands swarm execution
  - Run `python deployment/swarm/trade_matching_swarm.py` with a sample trade
  - Verify the swarm processes the trade successfully
  - Verify results are correct and match expected output
  - Ensure no errors related to missing CrewAI code
  - _Requirements: 8.2, 8.5_

- [x] 17. Final validation and cleanup
  - Verify installation succeeds: `pip install -e .`
  - Verify no CrewAI packages installed: `pip list | grep crewai`
  - Verify all documentation is consistent
  - Verify legacy code is properly archived
  - Run end-to-end trade processing test
  - _Requirements: 1.3, 1.4, 8.1, 8.2, 8.5_

- [ ] 18. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise
  - _Requirements: 8.3_
