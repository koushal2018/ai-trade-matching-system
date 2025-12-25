# Cleanup List for Public Release

Generated: December 25, 2025

This document lists all files to DELETE, KEEP, or SANITIZE before merging to public `main` branch.

## Summary
- **DELETE**: Internal docs, test scripts, sensitive configs, obsolete files
- **KEEP**: Core code, public documentation, example configs
- **SANITIZE**: Files with hardcoded AWS account IDs, ARNs, Cognito IDs

---

## ROOT LEVEL - DELETE

```
# Internal development logs
21dec_Changes.md
22dec_Changes.md
23dec_Changes.md
24dec_Changes.md
24dec_Session2_Changes.md

# Internal reports with sensitive data
AWS_RESOURCE_INVENTORY.md
AWS_SECURITY_ASSESSMENT_EXECUTION_ROLE_FIX_2025-12-21.md
AWS_SECURITY_ASSESSMENT_REPORT_2025-12-21.md
AGENTCORE_DEPLOYMENT_BUG_REPORT.md
AGENT_ISSUES_BUG_REPORT.md
BUG_REPORT_DUPLICATE_ORCHESTRATOR_INVOCATIONS.md
BUG_REPORT_FRONTEND_STATUS_NOT_UPDATING.md
DOCKERFILE_SECURITY_ASSESSMENT_2025-12-21.md
ROOT_CAUSE_ANALYSIS_DUPLICATE_ORCHESTRATOR.md
SECURITY_ASSESSMENT_MODEL_ID_CHANGE_2025-12-21.md
SECURITY_ASSESSMENT_REPORT.md
NEW_PROMPTS_IMPACT_ANALYSIS.md
impact_analysis_new_prompts.md
agent_review.md
fix-memory-permissions.md
featuresforfuture.md

# Internal scripts
cleanup_aws_resources.sh

# Generated/runtime files
registered_agents.json
task_agent_mapping.json

# Hidden folders (entire folders)
.claude/
.kiro/
.bedrock_agentcore/
.bedrock_agentcore.yaml

# Internal prompts folder
new_prompts/
```

## ROOT LEVEL - KEEP

```
# Public documentation
README.md
ARCHITECTURE.md
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
DEV_SETUP.md
LICENSE
PROJECT_OVERVIEW.md  # SANITIZE - has memory ID
RELEASE_NOTES_v1.0.0.md
SECURITY.md  # SANITIZE - has example ARNs (OK if generic)
VERSION

# Config files
.env.example
.gitignore
.gitlab-ci.yml
pyproject.toml
requirements.txt
setup.py
llm_config.json
aws-architecture.mmd
uv.lock
```

---

## DEPLOYMENT FOLDER

### deployment/ ROOT - DELETE
```
deployment/.DS_Store
deployment/.bedrock_agentcore.yaml.example  # Has real paths
```

### deployment/ ROOT - KEEP
```
deployment/README.md
deployment/QUICK_START.md
deployment/SETUP_GUIDE.md
deployment/DEPLOYMENT_CHECKLIST.md
deployment/deploy_all.sh
deployment/setup_memory.py
deployment/setup_prerequisites.sh
deployment/validate_deployment.sh
deployment/.env.memory.example
```

---

### deployment/exception_management/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.bedrock_agentcore.yaml  # Has real ARNs
source.zip
```

### deployment/exception_management/ - KEEP
```
exception_management_agent_strands.py
agentcore.yaml  # SANITIZE
requirements.txt
deploy.sh
.dockerignore
```

---

### deployment/orchestrator/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.bedrock_agentcore.yaml  # Has real ARNs
orchestrator_agent_strands_backup.py  # Backup file
```

### deployment/orchestrator/ - KEEP
```
orchestrator_agent_strands.py
orchestrator_agent_strands_goal_based.py
agentcore.yaml  # SANITIZE
requirements.txt
deploy.sh
.dockerignore
```

---

### deployment/pdf_adapter/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.bedrock_agentcore.yaml  # Has real ARNs
2025-12-21-this-session-is-being-continued-from-a-previous-co.txt
test_local.py
```

### deployment/pdf_adapter/ - KEEP
```
pdf_adapter_agent_strands.py
agentcore.yaml  # SANITIZE
requirements.txt
deploy.sh
Dockerfile
.dockerignore
```

---

### deployment/swarm/ - DELETE ENTIRE FOLDER
```
# Legacy folder - replaced by swarm_agentcore
deployment/swarm/  (entire folder)
```

---

### deployment/swarm_agentcore/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.venv/
.DS_Store
.bedrock_agentcore.yaml  # Has real ARNs
.env  # Has real credentials!
uv.lock

# Internal documentation
CRITICAL_FIXES_DEC24.md
DEPLOYMENT_INSTRUCTIONS.md
FRONTEND_TESTING_GUIDE.md
LOGGING_IMPROVEMENTS.md
ORCHESTRATOR_IMPROVEMENTS.md
PRE_DEPLOYMENT_CHECKLIST.md
SECURITY_ASSESSMENT_REPORT.md
SECURITY_IMPLEMENTATION_CHECKLIST.md
SECURITY_QUICK_FIXES.md
SECURITY_SUMMARY.md
SESSION_ID_FIX.md
STATUS_TRACKING_FIXES.md
STATUS_TRACKING_IMPLEMENTATION.md
STATUS_WRITER_IMPLEMENTATION.md
TABLE_NAME_FIXES.md

# Test/debug scripts
check_table_schema.py
test_imports.py
test_local_orchestrator.py
test_status_tracking.py
test_status_tracking_local.py
test_table_write.py
test_with_fixes.sh
verify_status.sh
http_orchestrator_agent_strands.py  # Empty file
```

### deployment/swarm_agentcore/ - KEEP
```
http_agent_orchestrator.py  # SANITIZE
trade_matching_swarm_agentcore_http.py
status_tracker.py
status_writer.py
idempotency.py
Dockerfile
agentcore.yaml  # SANITIZE
requirements.txt
pyproject.toml
.dockerignore
.env.example
```

---

### deployment/trade_extraction/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.venv/
.DS_Store
.bedrock_agentcore.yaml  # Has real ARNs
uv.lock

# Internal docs
SECURITY_ASSESSMENT_SYSTEM_PROMPT_2025-12-21.md
SECURITY_SUMMARY_PROMPT_CHANGES.md
log-queries.md
trade_extraction_sop.md

# Test/debug scripts
add_agent_permissions.sh
deploy_agentcore.sh
deploy_with_cloudformation.sh
dev.sh
test_agent.sh
test_data_models.py
test_dev.py
test_invoke.py
test_local.py
validate_cloudformation.sh
validate_deployment.py
validate_security.sh
register_agent_deployment.py

# Obsolete/duplicate files
agentcore_memory_integration.py
agentcore_observability_enhancement.py
agentcore_policy_integration.py
aws_resources.py
core_interfaces.py
models.py
monitoring-dashboard.json
security-rules.guard
tool_resources_config.json
requirements_agentcore.txt
requirements-dev.txt
```

### deployment/trade_extraction/ - KEEP
```
agent.py  # SANITIZE
data_models.py
agent_registry.py
http_interface.py
logging_config.py
sop_workflow.py
table_router.py
trade_data_validator.py
agentcore.yaml  # SANITIZE
requirements.txt
deploy.sh
pyproject.toml
.dockerignore
SECURITY.md
```

---

### deployment/trade_matching/ - DELETE
```
__pycache__/
.bedrock_agentcore/
.venv/
.DS_Store
.bedrock_agentcore.yaml  # Has real ARNs
uv.lock

# Policy files with real ARNs
agentcore_memory_policy.json
codebuild_policy.json

# Fix scripts (internal)
fix_codebuild_ecr_permissions.sh
fix_execution_role.py
fix_execution_role.sh
fix_execution_role_20251221_193137.log
update_memory_docs.sh

# Test scripts
test_memory_integration.py
test_production_invoke.sh
INTEGRATION_EXAMPLE.py

# Obsolete
trade_matching_agent.py  # Old version
memory_integration.py
```

### deployment/trade_matching/ - KEEP
```
trade_matching_agent_strands.py  # SANITIZE
agentcore.yaml  # SANITIZE
requirements.txt
deploy.sh
pyproject.toml
.dockerignore
```

---

## SCRIPTS FOLDER - DELETE
```
scripts/fix_agentcore_memory_permissions.py  # Has real account ID
scripts/add_agentcore_policies.sh  # Has real ARNs
scripts/add_agentcore_permissions.sh  # Has real ARNs
scripts/attach_agentcore_policies.sh  # Has real ARNs
scripts/tag_aws_resources.sh  # Has real ARNs
scripts/verify_resource_tags.sh  # Has real ARNs
scripts/enable_cloudwatch_transaction_search.sh
```

## SCRIPTS FOLDER - KEEP
```
scripts/verify_production_connection.py  # SANITIZE
# Keep other utility scripts that don't have hardcoded values
```

---

## TERRAFORM FOLDER - DELETE
```
terraform/agentcore/ORCHESTRATOR_STATUS_TABLE_DEPLOYMENT.md
terraform/agentcore/QUICK_DEPLOY_STATUS_TABLE.md
terraform/agentcore/STATUS_TABLE_IMPLEMENTATION_SUMMARY.md
terraform/agentcore/scripts/  # Internal deployment scripts
terraform/agentcore/configs/*.json  # May have real values
terraform/agentcore/configs/*_README.md  # Has real Cognito IDs
```

## TERRAFORM FOLDER - KEEP (SANITIZE ALL)
```
terraform/  # Keep structure but sanitize all .tf files
# Replace account IDs, ARNs with placeholders
```

---

## WEB-PORTAL FOLDER - DELETE
```
web-portal/TASK_*.md  # All task completion docs
web-portal/CHECKPOINT_*.md  # All checkpoint docs
web-portal/COMPILATION_ERRORS_FIXED.md
web-portal/KEYBOARD_NAVIGATION_VERIFICATION.md
web-portal/SCREEN_READER_VERIFICATION.md
web-portal/.env  # Has real Cognito IDs!
```

## WEB-PORTAL FOLDER - KEEP
```
web-portal/src/  # All source code
web-portal/public/
web-portal/package.json
web-portal/package-lock.json
web-portal/vite.config.ts
web-portal/vitest.config.ts
web-portal/tsconfig.json
web-portal/docs/  # Public docs
web-portal/verify-hooks.ts
```

## WEB-PORTAL - SANITIZE
```
web-portal/src/contexts/AuthContext.tsx  # Has Cognito IDs
```

---

## WEB-PORTAL-API FOLDER - DELETE
```
web-portal-api/COGNITO_AUTH_FIX.md  # Has real Cognito IDs
web-portal-api/TASK_*.md
web-portal-api/WORKFLOW_STATUS_IMPLEMENTATION.md
web-portal-api/test_*.sh  # Test scripts
web-portal-api/=3.0.0  # Junk file
```

## WEB-PORTAL-API FOLDER - KEEP
```
web-portal-api/app/  # All source code - SANITIZE auth.py
web-portal-api/tests/
web-portal-api/requirements.txt
```

## WEB-PORTAL-API - SANITIZE
```
web-portal-api/app/auth.py  # Has hardcoded Cognito IDs
```

---

## TESTS FOLDER - KEEP ALL
```
tests/  # Keep all test files
```

---

## DOCS FOLDER - KEEP
```
docs/  # Keep all documentation
```

---

## FILES REQUIRING SANITIZATION

Replace these values with placeholders:

| Current Value | Replace With |
|--------------|--------------|
| `401552979575` | `YOUR_AWS_ACCOUNT_ID` |
| `us-east-1_uQ2lN39dT` | `YOUR_COGNITO_USER_POOL_ID` |
| `78daptta2m4lb6k5jm3n2hd8oc` | `YOUR_COGNITO_CLIENT_ID` |
| `trade_matching_decisions-Z3tG4b4Xsd` | `YOUR_AGENTCORE_MEMORY_ID` |
| `arn:aws:iam::401552979575:role/...` | `arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/...` |
| `arn:aws:resource-groups:us-east-1:401552979575:...` | `arn:aws:resource-groups:us-east-1:YOUR_AWS_ACCOUNT_ID:...` |

---

## EXECUTION ORDER

1. First, commit current state of dev (backup)
2. Delete all files marked DELETE
3. Sanitize all files marked SANITIZE
4. Update .gitignore to prevent re-adding sensitive files
5. Commit cleanup to dev
6. Create release branch from cleaned dev
7. Merge release branch to main

