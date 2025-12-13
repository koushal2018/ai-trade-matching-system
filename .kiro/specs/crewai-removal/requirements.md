# Requirements Document

## Introduction

This specification defines the requirements for removing all CrewAI-related code, dependencies, and references from the AI Trade Matching System. The system has fully migrated to Strands SDK with AWS Bedrock AgentCore, making CrewAI code obsolete and confusing. This cleanup will improve code clarity, reduce dependencies, and eliminate legacy code that is no longer used in production.

## Glossary

- **CrewAI**: Legacy multi-agent framework that was previously used but has been replaced by Strands SDK
- **Strands SDK**: Current multi-agent swarm framework used in production
- **AgentCore**: AWS Bedrock service for deploying and managing agents
- **Legacy Code**: Code that is no longer used in production but remains in the codebase
- **Production System**: The current Strands-based implementation in `deployment/` directory

## Requirements

### Requirement 1

**User Story:** As a developer, I want all CrewAI dependencies removed from the project, so that the dependency tree is clean and only contains actively used packages.

#### Acceptance Criteria

1. WHEN the requirements.txt file is examined THEN the system SHALL NOT contain any crewai or crewai-tools dependencies
2. WHEN the pyproject.toml file is examined THEN the system SHALL NOT contain any crewai or crewai-tools dependencies
3. WHEN pip list is executed in the virtual environment THEN the system SHALL NOT show crewai or crewai-tools packages installed
4. WHEN the project is installed THEN the system SHALL install successfully without CrewAI dependencies

### Requirement 2

**User Story:** As a developer, I want all CrewAI-based code files removed, so that the codebase only contains the active Strands implementation.

#### Acceptance Criteria

1. WHEN the src/latest_trade_matching_agent directory is examined THEN the system SHALL NOT contain crew_fixed.py
2. WHEN the src/latest_trade_matching_agent/config directory is examined THEN the system SHALL NOT contain agents.yaml or tasks.yaml files
3. WHEN the src/latest_trade_matching_agent/tools directory is examined THEN the system SHALL NOT contain CrewAI BaseTool imports
4. WHEN the codebase is searched for "from crewai" THEN the system SHALL return zero results
5. WHEN the codebase is searched for "import crewai" THEN the system SHALL return zero results

### Requirement 3

**User Story:** As a developer, I want the eks_main.py file updated to remove CrewAI fallback logic, so that the API only uses the Strands implementation.

#### Acceptance Criteria

1. WHEN eks_main.py is examined THEN the system SHALL NOT import crew_fixed module
2. WHEN eks_main.py is examined THEN the system SHALL NOT import crewai_tools
3. WHEN eks_main.py is examined THEN the system SHALL NOT contain CREWAI_AVAILABLE flag
4. WHEN the API processes a trade THEN the system SHALL use only the Strands swarm implementation
5. WHEN CrewAI is not available THEN the system SHALL NOT fall back to simulation mode

### Requirement 4

**User Story:** As a developer, I want all documentation and steering files updated to remove CrewAI references, so that documentation accurately reflects the current implementation.

#### Acceptance Criteria

1. WHEN README.md is examined THEN the system SHALL NOT reference CrewAI
2. WHEN ARCHITECTURE.md is examined THEN the system SHALL NOT reference CrewAI
3. WHEN .kiro/steering/ files are examined THEN the system SHALL NOT reference CrewAI as a current technology
4. WHEN .kiro/steering/tech.md is examined THEN the system SHALL NOT list crewai in dependencies
5. WHEN .kiro/steering/structure.md is examined THEN the system SHALL NOT reference crew_fixed.py or CrewAI configs
6. WHEN task files are examined THEN the system SHALL mark CrewAI-related tasks as deprecated or completed
7. WHEN documentation mentions legacy systems THEN the system SHALL clearly mark them as archived

### Requirement 5

**User Story:** As a developer, I want legacy CrewAI code moved to an archive directory, so that it's preserved for reference but clearly separated from active code.

#### Acceptance Criteria

1. WHEN the project root is examined THEN the system SHALL contain a legacy/ directory
2. WHEN legacy CrewAI files are moved THEN the system SHALL preserve them in legacy/crewai/
3. WHEN the src/ directory is examined THEN the system SHALL NOT contain crew_fixed.py
4. WHEN the legacy/ directory is examined THEN the system SHALL contain a README explaining the archived code
5. WHERE legacy code is referenced THEN the system SHALL include clear warnings that it is not used in production

### Requirement 6

**User Story:** As a developer, I want property tests updated to remove CrewAI parity tests, so that tests only validate the current Strands implementation.

#### Acceptance Criteria

1. WHEN test files are examined THEN the system SHALL NOT contain test_property_1_functional_parity.py
2. WHEN test files are examined THEN the system SHALL NOT test for CrewAI parity
3. WHEN the test suite is run THEN the system SHALL execute only tests relevant to the Strands implementation
4. WHEN tasks.md is examined THEN the system SHALL mark Property 1 (CrewAI parity) as not applicable

### Requirement 7

**User Story:** As a developer, I want hooks and automation updated to remove CrewAI references, so that automated workflows reflect the current architecture.

#### Acceptance Criteria

1. WHEN .kiro/hooks/ is examined THEN the system SHALL NOT reference CrewAI in active hooks
2. WHEN hook descriptions mention frameworks THEN the system SHALL reference only Strands SDK and AgentCore
3. WHEN hooks are triggered THEN the system SHALL execute workflows based on the Strands implementation

### Requirement 8

**User Story:** As a developer, I want the project to build and run successfully after CrewAI removal, so that the cleanup doesn't break the production system.

#### Acceptance Criteria

1. WHEN dependencies are installed THEN the system SHALL complete without errors
2. WHEN the Strands swarm is executed THEN the system SHALL process trades successfully
3. WHEN tests are run THEN the system SHALL pass all non-CrewAI tests
4. WHEN the web portal API is started THEN the system SHALL start without import errors
5. WHEN a trade is processed end-to-end THEN the system SHALL produce correct results
