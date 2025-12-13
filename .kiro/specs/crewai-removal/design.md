# Design Document: CrewAI Removal

## Overview

This design document outlines the approach for removing all CrewAI-related code, dependencies, and references from the AI Trade Matching System. The system has fully migrated to Strands SDK with AWS Bedrock AgentCore, making the legacy CrewAI implementation obsolete. This cleanup will:

- Remove confusing legacy code that is no longer used
- Reduce dependency bloat (CrewAI, crewai-tools, litellm, mcp)
- Simplify the codebase by eliminating dual implementations
- Improve maintainability by having a single, clear implementation path
- Preserve legacy code in an archive for historical reference

The cleanup is purely a code removal and reorganization task - no functional changes to the production Strands implementation.

## Architecture

### Current State

The codebase currently contains two parallel implementations:

1. **Production (Strands SDK)**: Located in `deployment/` directory
   - Uses Strands SDK for multi-agent orchestration
   - Direct boto3 access for AWS services
   - Swarm-based autonomous agent handoffs
   - Currently deployed and actively used

2. **Legacy (CrewAI)**: Located in `src/latest_trade_matching_agent/`
   - Uses CrewAI framework for agent orchestration
   - MCP (Model Context Protocol) for tool integration
   - Sequential task execution
   - No longer used in production

### Target State

After cleanup:

1. **Production Code Only**: `deployment/` directory remains unchanged
2. **Supporting Modules**: `src/latest_trade_matching_agent/` contains only:
   - `matching/` - Fuzzy matching logic (used by deployment)
   - `exception_handling/` - Exception classification (used by deployment)
   - `orchestrator/` - SLA monitoring (used by deployment)
   - `models/` - Pydantic models (used by deployment)
   - `tools/` - Custom tools (refactored to remove CrewAI dependencies)
3. **Legacy Archive**: `legacy/crewai/` contains archived CrewAI code
4. **Clean Dependencies**: requirements.txt contains only Strands and AWS dependencies

## Components and Interfaces

### Files to Remove

**Primary CrewAI Implementation:**
- `src/latest_trade_matching_agent/crew_fixed.py` - Main CrewAI crew definition
- `src/latest_trade_matching_agent/main.py` - CrewAI entry point
- `src/latest_trade_matching_agent/config/agents.yaml` - Agent configurations
- `src/latest_trade_matching_agent/config/tasks.yaml` - Task configurations

**CrewAI-Dependent Tools:**
- `src/latest_trade_matching_agent/tools/custom_tool.py` - Uses `crewai.tools.BaseTool`
- `src/latest_trade_matching_agent/tools/ocr_tool.py` - Uses `crewai.tools.BaseTool`
- `src/latest_trade_matching_agent/tools/pdf_to_image.py` - Uses `crewai.tools.BaseTool`
- `src/latest_trade_matching_agent/tools/trade_source_classifier.py` - Has CrewAI compatibility layer

**Test Files:**
- `test_property_1_functional_parity.py` - Tests CrewAI parity (no longer relevant)
- `test_property_1_functional_parity_simple.py` - Simplified parity test

### Files to Modify

**eks_main.py:**
- Remove `from .crew_fixed import LatestTradeMatchingAgent`
- Remove `from crewai_tools import MCPServerAdapter`
- Remove `CREWAI_AVAILABLE` flag and all conditional logic
- Remove CrewAI processing code path
- Remove simulation mode fallback
- Keep only health/readiness endpoints (or remove entirely if not used)

**requirements.txt:**
- Remove `crewai>=0.201.0`
- Remove `crewai-tools[mcp]>=0.14.0`
- Remove `litellm>=1.74.9` (CrewAI dependency)
- Remove `mcp>=1.16.0` (CrewAI tool dependency)
- Remove `pdf2image>=1.17.0` (only used by CrewAI tools)
- Remove `Pillow>=11.3.0` (only used for PDF-to-image conversion)
- Keep Strands, boto3, fastapi, and other actively used dependencies

**Steering Files:**
- `.kiro/steering/tech.md` - Remove CrewAI from technology stack
- `.kiro/steering/structure.md` - Remove references to crew_fixed.py, agents.yaml, tasks.yaml

**Documentation:**
- Update any remaining CrewAI references to mark them as legacy/archived
- Ensure all documentation reflects Strands as the only implementation

**Hooks:**
- `.kiro/hooks/agentcore-mcp-guide.kiro.hook` - Remove CrewAI references

**Task Files:**
- `.kiro/specs/agentcore-migration/tasks.md` - Mark CrewAI parity tasks as not applicable

### Files to Archive

Create `legacy/crewai/` directory structure:

```
legacy/
└── crewai/
    ├── README.md (explanation of archived code)
    ├── crew_fixed.py
    ├── main.py
    ├── config/
    │   ├── agents.yaml
    │   └── tasks.yaml
    ├── tools/
    │   ├── custom_tool.py
    │   ├── ocr_tool.py
    │   ├── pdf_to_image.py
    │   └── trade_source_classifier.py (CrewAI version)
    └── tests/
        ├── test_property_1_functional_parity.py
        └── test_property_1_functional_parity_simple.py
```

### Files to Keep (No Changes)

**Production Strands Implementation:**
- All files in `deployment/` directory (unchanged)
- `deployment/swarm/trade_matching_swarm.py` (main entry point)
- All agent implementations in `deployment/*/`

**Supporting Modules:**
- `src/latest_trade_matching_agent/matching/` (used by deployment)
- `src/latest_trade_matching_agent/exception_handling/` (used by deployment)
- `src/latest_trade_matching_agent/orchestrator/` (used by deployment)
- `src/latest_trade_matching_agent/models/` (used by deployment)
- `src/latest_trade_matching_agent/tools/dynamodb_tool.py` (if not CrewAI-dependent)
- `src/latest_trade_matching_agent/tools/llm_extraction_tool.py` (if not CrewAI-dependent)

## Data Models

No data model changes - this is purely a code cleanup task.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Since this is a cleanup/removal task, most acceptance criteria are examples (checking specific files/states) rather than universal properties. However, we can define a few key properties:

**Property 1: CrewAI Import Absence**
*For any* Python file in the active codebase (excluding legacy/ directory), the file should not contain "from crewai" or "import crewai" statements
**Validates: Requirements 2.4, 2.5**

**Property 2: Dependency Consistency**
*For any* Python file in the active codebase (excluding legacy/ directory), if the file imports a module, then that module should be listed in requirements.txt or be a standard library module
**Validates: Requirements 1.1, 1.2**

**Property 3: System Functionality Preservation**
*For any* valid trade document input, processing the document with the Strands swarm after CrewAI removal should produce equivalent results to processing before removal
**Validates: Requirements 8.2, 8.5**

Note: Most acceptance criteria are examples (checking specific files exist/don't exist) rather than universal properties, so they will be validated through unit tests rather than property-based tests.

## Error Handling

### Potential Issues During Cleanup

1. **Import Errors**: Removing CrewAI may reveal hidden dependencies
   - **Mitigation**: Test imports after each file removal
   - **Recovery**: Check for indirect imports and update accordingly

2. **Tool Dependencies**: Some tools may have hidden CrewAI dependencies
   - **Mitigation**: Review all tool files for BaseTool inheritance
   - **Recovery**: Refactor tools to use plain Python classes or remove if unused

3. **Test Failures**: Removing files may break other tests
   - **Mitigation**: Run test suite after each major change
   - **Recovery**: Update or remove affected tests

4. **Documentation Links**: Documentation may link to removed files
   - **Mitigation**: Search for file references in documentation
   - **Recovery**: Update links to point to legacy/ or remove if not needed

### Validation Strategy

After each phase of removal:
1. Run `pip install -e .` to verify installation succeeds
2. Run `python -c "import src.latest_trade_matching_agent"` to verify imports
3. Run test suite to verify no broken tests
4. Run Strands swarm on a sample trade to verify functionality

## Testing Strategy

### Unit Tests

Unit tests will verify specific cleanup requirements:

1. **File Absence Tests**: Verify removed files don't exist
   - Test that crew_fixed.py is not in src/
   - Test that agents.yaml and tasks.yaml are not in config/
   - Test that CrewAI tool files are not in tools/

2. **File Presence Tests**: Verify archived files exist
   - Test that legacy/crewai/ directory exists
   - Test that legacy/crewai/README.md exists
   - Test that archived files are in legacy/crewai/

3. **Content Tests**: Verify file contents are clean
   - Test that requirements.txt doesn't contain crewai
   - Test that eks_main.py doesn't import crew_fixed
   - Test that steering files don't reference CrewAI as current tech

4. **Import Tests**: Verify imports work
   - Test that active modules import successfully
   - Test that no CrewAI imports exist in active code

5. **Installation Tests**: Verify system installs
   - Test that `pip install -e .` succeeds
   - Test that installed packages don't include crewai

### Property-Based Tests

Property-based tests will verify universal correctness properties:

1. **Property 1: CrewAI Import Absence**
   - Generate random Python files from active codebase
   - Verify none contain CrewAI imports
   - Run 100+ iterations across all Python files

2. **Property 2: Dependency Consistency**
   - Generate random Python files from active codebase
   - Extract all imports
   - Verify all imports are in requirements.txt or stdlib
   - Run 100+ iterations

3. **Property 3: System Functionality Preservation**
   - Use existing trade documents as test inputs
   - Process with Strands swarm
   - Verify results match expected outputs
   - This validates that removal didn't break functionality

### Integration Tests

Integration tests will verify end-to-end functionality:

1. **Strands Swarm Execution**: Run complete trade processing workflow
2. **Web Portal API**: Start API and verify it runs without errors
3. **Test Suite Execution**: Run full test suite and verify all pass

### Test Execution Order

1. Run unit tests after each file removal/modification
2. Run property tests after completing each requirement
3. Run integration tests after all cleanup is complete
4. Run final validation with real trade documents

## Implementation Phases

### Phase 1: Dependency Cleanup
- Update requirements.txt to remove CrewAI dependencies
- Update pyproject.toml if it exists
- Test installation succeeds

### Phase 2: Archive Legacy Code
- Create legacy/crewai/ directory structure
- Move CrewAI files to archive
- Create README.md explaining archived code
- Verify files are preserved

### Phase 3: Remove CrewAI Code
- Delete crew_fixed.py from src/
- Delete agents.yaml and tasks.yaml from config/
- Delete or refactor CrewAI-dependent tools
- Delete CrewAI parity tests
- Verify no CrewAI imports remain

### Phase 4: Update eks_main.py
- Remove CrewAI imports
- Remove CREWAI_AVAILABLE flag
- Remove CrewAI processing code path
- Remove simulation mode fallback
- Test API starts successfully

### Phase 5: Documentation Cleanup
- Update steering files (tech.md, structure.md)
- Update README.md and ARCHITECTURE.md
- Update task files to mark CrewAI tasks as not applicable
- Update hooks to remove CrewAI references
- Verify documentation is consistent

### Phase 6: Final Validation
- Run full test suite
- Run Strands swarm on sample trades
- Verify system functionality is preserved
- Verify no CrewAI references remain in active code

## Dependencies

### Removed Dependencies
- crewai>=0.201.0
- crewai-tools[mcp]>=0.14.0
- litellm>=1.74.9
- mcp>=1.16.0
- pdf2image>=1.17.0
- Pillow>=11.3.0

### Retained Dependencies
- strands>=0.1.0
- strands-tools>=0.1.0
- boto3>=1.40.0
- fastapi>=0.118.0
- uvicorn>=0.37.0
- python-dotenv>=1.1.0
- pydantic>=2.11.0
- structlog>=25.4.0
- hypothesis>=6.0.0 (for property testing)
- anthropic>=0.69.0

## Risks and Mitigations

### Risk 1: Breaking Production System
**Likelihood**: Low
**Impact**: High
**Mitigation**: 
- Production code in deployment/ is not modified
- Test Strands swarm after each phase
- Keep legacy code archived for reference

### Risk 2: Hidden Dependencies
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Review all imports before removal
- Test installation after dependency changes
- Run full test suite after each phase

### Risk 3: Documentation Inconsistency
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- Search for all CrewAI references
- Update documentation systematically
- Review documentation after cleanup

### Risk 4: Tool Refactoring Complexity
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Identify which tools are actually used by deployment/
- Remove unused tools entirely
- Refactor used tools to remove BaseTool dependency

## Success Criteria

1. No CrewAI dependencies in requirements.txt
2. No CrewAI imports in active codebase
3. Legacy code preserved in legacy/crewai/
4. All tests pass (except removed CrewAI parity tests)
5. Strands swarm processes trades successfully
6. Documentation reflects Strands-only implementation
7. System installs without errors
8. Web portal API starts without errors (if kept)

## Future Considerations

1. **eks_main.py Decision**: Determine if this file is still needed
   - If used for EKS deployment, keep and clean up
   - If not used, consider removing entirely

2. **Tool Consolidation**: Review which tools in src/tools/ are actually used
   - Remove unused tools
   - Consolidate similar functionality

3. **Directory Restructuring**: Consider flattening src/ structure
   - Move supporting modules closer to deployment/
   - Simplify import paths

4. **Legacy Code Retention**: Decide on long-term retention policy
   - Keep in repository for 6-12 months
   - Move to separate archive repository
   - Document in git history and remove
