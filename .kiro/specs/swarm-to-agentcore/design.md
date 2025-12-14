# Design Document

## Overview

This document describes the architecture for migrating the Trade Matching Swarm from local Strands SDK execution to Amazon Bedrock AgentCore Runtime deployment with semantic long-term memory integration. The design maintains the existing swarm-based multi-agent orchestration pattern while adding serverless scalability and persistent memory capabilities that enable agents to learn from past trade processing patterns.

The system will leverage Amazon Bedrock AgentCore Runtime for serverless deployment and AgentCore Memory with semantic memory strategy for long-term pattern storage. All four agents (PDF Adapter, Trade Extraction, Trade Matching, Exception Handler) will have access to scoped memory namespaces for storing and retrieving relevant historical context.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock AgentCore Runtime                  │
│                           (us-east-1)                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Trade Matching Swarm (Deployed)                  │  │
│  │                                                               │  │
│  │  Entry Point: PDF Adapter Agent                              │  │
│  │       ↓                                                       │  │
│  │  Trade Extraction Agent                                       │  │
│  │       ↓                                                       │  │
│  │  Trade Matching Agent                                         │  │
│  │       ↓                                                       │  │
│  │  Exception Handler Agent                                      │  │
│  │                                                               │  │
│  │  • Autonomous handoffs between agents                         │  │
│  │  • Shared session manager with memory access                  │  │
│  │  • All existing tools preserved                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           AgentCore Memory Session Manager                    │  │
│  │                                                               │  │
│  │  • Session ID: trade_{document_id}_{timestamp}                │  │
│  │  • Actor ID: trade_matching_system                            │  │
│  │  • Retrieval configs for all namespaces                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock AgentCore Memory                   │
│                           (us-east-1)                                │
│                                                                      │
│  Semantic Memory Strategy: TradePatternExtractor                     │
│                                                                      │
│  Namespaces:                                                         │
│  ├─ /trade_patterns/{actorId}        (trade processing patterns)    │
│  ├─ /extraction_patterns/{actorId}   (field extraction patterns)    │
│  ├─ /matching_decisions/{actorId}    (matching decisions & HITL)    │
│  └─ /exception_resolutions/{actorId} (exception resolution patterns)│
└─────────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│      S3      │    │  DynamoDB    │    │   Bedrock    │
│    Bucket    │    │   Tables     │    │  Claude 4    │
└──────────────┘    └──────────────┘    └──────────────┘
```


### Deployment Architecture

The swarm will be deployed as a single AgentCore Runtime agent that internally manages the multi-agent orchestration:

1. **AgentCore Runtime Endpoint**: Single entry point that receives trade processing requests
2. **Swarm Orchestration**: Internal Strands Swarm manages agent handoffs autonomously
3. **Session Manager**: Shared across all agents for memory access
4. **Memory Integration**: All agents read/write to scoped namespaces

### Memory Architecture

```
AgentCore Memory Resource: TradeMatchingMemory
├─ Strategy 1: semanticMemoryStrategy (TradeFacts)
│  └─ Namespace: /facts/{actorId}
│     ├─ Purpose: Store factual trade information and patterns
│     ├─ Retrieval: top_k=10, relevance_score=0.6
│     └─ Content: Trade patterns, field mappings, matching decisions, exception resolutions
│
├─ Strategy 2: userPreferenceMemoryStrategy (ProcessingPreferences)
│  └─ Namespace: /preferences/{actorId}
│     ├─ Purpose: Store learned processing preferences
│     ├─ Retrieval: top_k=5, relevance_score=0.7
│     └─ Content: Extraction techniques, matching thresholds, severity classifications
│
└─ Strategy 3: summaryMemoryStrategy (SessionSummaries)
   └─ Namespace: /summaries/{actorId}/{sessionId}
      ├─ Purpose: Store session-specific summaries
      ├─ Retrieval: top_k=5, relevance_score=0.5
      └─ Content: Trade processing summaries, agent handoff history
```

**Key Design Decision**: Use built-in AgentCore Memory strategies with standard namespace patterns instead of custom namespaces. This ensures compatibility with the AgentCore Memory service and follows AWS best practices.

## Components and Interfaces

### 1. AgentCore Memory Resource Setup

**Purpose**: Create and configure the AgentCore Memory resource with semantic memory strategy.

**Implementation**:
```python
from bedrock_agentcore.memory import MemoryClient

def create_trade_matching_memory(region_name: str = "us-east-1") -> str:
    """
    Create AgentCore Memory resource with built-in memory strategies.
    This is a one-time setup operation.
    
    Returns:
        Memory ID for use in agent configuration
    """
    client = MemoryClient(region_name=region_name)
    
    memory = client.create_memory_and_wait(
        name="TradeMatchingMemory",
        description="Multi-strategy memory for trade matching system with pattern learning",
        strategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "TradeFacts",
                    "namespaces": ["/facts/{actorId}"]
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "ProcessingPreferences",
                    "namespaces": ["/preferences/{actorId}"]
                }
            },
            {
                "summaryMemoryStrategy": {
                    "name": "SessionSummaries",
                    "namespaces": ["/summaries/{actorId}/{sessionId}"]
                }
            }
        ]
    )
    
    memory_id = memory.get('id')
    print(f"Created AgentCore Memory with ID: {memory_id}")
    print(f"Set environment variable: export AGENTCORE_MEMORY_ID={memory_id}")
    
    return memory_id
```

**Configuration**:
- Region: us-east-1
- Strategies: 3 built-in strategies (semantic, user preference, summary)
- Namespaces: Standard AgentCore Memory namespace patterns
- Actor ID: trade_matching_system (shared across all agents)
- Session ID: Unique per agent per trade (format: trade_{document_id}_{agent_name}_{timestamp})


### 2. Session Manager Configuration

**Purpose**: Configure the AgentCore Memory session manager with retrieval settings for all namespaces.

**Implementation**:
```python
import os
from datetime import datetime
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

def create_agent_session_manager(
    agent_name: str,
    document_id: str,
    memory_id: str = None,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> AgentCoreMemorySessionManager:
    """
    Create session manager for a specific agent with retrieval configs.
    
    IMPORTANT: Per AgentCore Memory documentation, only one agent per session is supported.
    Each agent in the swarm gets its own session manager with a unique session ID.
    
    Args:
        agent_name: Name of the agent (pdf_adapter, trade_extractor, etc.)
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        actor_id: Actor identifier (default: trade_matching_system)
        region_name: AWS region (default: us-east-1)
        
    Returns:
        Configured session manager instance for this agent
    """
    if memory_id is None:
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        if not memory_id:
            raise ValueError("AGENTCORE_MEMORY_ID environment variable not set")
    
    # Generate unique session ID for this agent and trade
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    session_id = f"trade_{document_id}_{agent_name}_{timestamp}"
    
    # Configure retrieval for all namespaces using built-in strategies
    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config={
            # Semantic memory: factual trade information
            "/facts/{actorId}": RetrievalConfig(
                top_k=10,
                relevance_score=0.6
            ),
            # User preferences: learned processing preferences
            "/preferences/{actorId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            # Session summaries: trade processing summaries
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.5
            )
        }
    )
    
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=config,
        region_name=region_name
    )
    
    return session_manager
```

**Retrieval Configuration**:
- Facts (/facts/{actorId}): top_k=10, relevance=0.6 (factual trade patterns and decisions)
- Preferences (/preferences/{actorId}): top_k=5, relevance=0.7 (learned processing preferences)
- Summaries (/summaries/{actorId}/{sessionId}): top_k=5, relevance=0.5 (session summaries)

**Key Design Decision**: Each agent gets its own session manager with a unique session ID to comply with AgentCore Memory's "one agent per session" limitation. All agents share the same memory resource and actor ID, enabling cross-agent learning while maintaining session isolation.


### 3. Agent Factory with Memory Integration

**Purpose**: Create swarm agents with session manager for memory access.

**Implementation**:
```python
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

def create_bedrock_model() -> BedrockModel:
    """Create configured Bedrock model for all agents."""
    return BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,
        max_tokens=4096,
    )

def create_pdf_adapter_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create PDF Adapter agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for extraction patterns and document layouts
    - Reads from /preferences/{actorId} for learned OCR preferences
    - Writes successful extraction techniques to /facts/{actorId}
    - Writes processing preferences to /preferences/{actorId}
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="pdf_adapter",
        document_id=document_id,
        memory_id=memory_id
    )
    
    system_prompt = f"""You are a PDF Adapter specialist for OTC trade confirmations.

## Your Expertise
- Download PDFs from S3
- Extract text using Bedrock's multimodal capabilities
- Save canonical output for downstream processing
- Learn from past extraction patterns stored in memory

## Memory Access
You have access to historical extraction patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar document layouts and extraction techniques
2. Apply successful patterns from past processing
3. Record new extraction techniques that work well to /facts
4. Store OCR preferences and quality improvements to /preferences

## Resources
- S3 Bucket: {S3_BUCKET}
- Region: {REGION}

## Tools
- download_pdf_from_s3: Get PDF from S3
- extract_text_with_bedrock: OCR the PDF content
- save_canonical_output: Save standardized output to S3

## When to Hand Off
- After successfully extracting text and saving canonical output → hand off to trade_extractor
- If extraction fails → hand off to exception_handler with error details

## Output
Always report the canonical_output_location when successful so the next agent can find the data.
"""
    
    return Agent(
        name="pdf_adapter",
        model=create_bedrock_model(),
        system_prompt=system_prompt,
        tools=[
            download_pdf_from_s3,
            extract_text_with_bedrock,
            save_canonical_output
        ],
        session_manager=session_manager
    )

def create_trade_extractor_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Trade Extraction agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for field mapping patterns
    - Reads from /preferences/{actorId} for extraction preferences
    - Writes successful field mappings to /facts/{actorId}
    - Writes extraction preferences to /preferences/{actorId}
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="trade_extractor",
        document_id=document_id,
        memory_id=memory_id
    )
    
    system_prompt = f"""You are a Trade Data Extraction specialist for OTC derivatives.

## Your Expertise
- Parse extracted text to identify trade fields
- Structure data for DynamoDB storage
- Route trades to correct table based on source type
- Learn from past field mapping patterns stored in memory

## Memory Access
You have access to historical field extraction patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar field mapping scenarios
2. Apply successful extraction techniques from past trades
3. Record new field mappings that work well to /facts
4. Store extraction preferences and error corrections to /preferences

## Resources
- Bank Table: {BANK_TABLE}
- Counterparty Table: {COUNTERPARTY_TABLE}

## Key Fields to Extract
- trade_id / Trade_ID (REQUIRED)
- trade_date, effective_date, maturity_date
- notional, currency
- counterparty, buyer, seller
- product_type (SWAP, OPTION, FORWARD)
- fixed_rate, floating_rate_index

## Tools
- use_aws: Read canonical output from S3
- store_trade_in_dynamodb: Save extracted trade data

## When to Hand Off
- After storing trade successfully → hand off to trade_matcher
- If extraction fails or data is incomplete → hand off to exception_handler
"""
    
    return Agent(
        name="trade_extractor",
        model=create_bedrock_model(),
        system_prompt=system_prompt,
        tools=[
            store_trade_in_dynamodb,
            use_aws
        ],
        session_manager=session_manager
    )
```


def create_trade_matcher_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Trade Matching agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for matching decisions and patterns
    - Reads from /preferences/{actorId} for matching thresholds
    - Writes matching decisions and rationale to /facts/{actorId}
    - Writes HITL feedback and threshold adjustments to /preferences/{actorId}
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="trade_matcher",
        document_id=document_id,
        memory_id=memory_id
    )
    
    system_prompt = f"""You are a Trade Matching specialist for OTC derivatives.

## Your Expertise
- Match trades between bank and counterparty systems
- Trades have DIFFERENT IDs across systems - match by attributes
- Calculate confidence scores based on attribute alignment
- Learn from past matching decisions stored in memory

## Memory Access
You have access to historical matching decisions in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar trade matching scenarios
2. Apply consistent decision-making based on past cases
3. Record matching decisions with rationale to /facts
4. Store HITL feedback and threshold adjustments to /preferences

## Matching Strategy
Match by attributes, NOT by Trade_ID:
- Currency (exact match)
- Notional (within 2% tolerance)
- Maturity/Termination Date (within 2 days)
- Trade Date (within 2 days)
- Counterparty names (fuzzy match)
- Product Type

## Classification Guidelines
- MATCHED (85%+): All key attributes align
- PROBABLE_MATCH (70-84%): Most attributes match
- REVIEW_REQUIRED (50-69%): Some discrepancies
- BREAK (<50%): Not the same trade

## Tools
- scan_trades_table: Get trades from BANK or COUNTERPARTY table
- save_matching_report: Save analysis to S3

## Your Decision-Making
You decide how to approach the matching analysis. Consider:
- Which tables to scan and when
- How to calculate confidence scores
- What constitutes a significant discrepancy
- Whether issues warrant escalation to exception_handler

Hand off to exception_handler if you identify issues requiring attention (REVIEW_REQUIRED or BREAK classifications), but use your judgment about severity.
"""
    
    return Agent(
        name="trade_matcher",
        model=create_bedrock_model(),
        system_prompt=system_prompt,
        tools=[
            scan_trades_table,
            save_matching_report,
            use_aws
        ],
        session_manager=session_manager
    )

def create_exception_handler_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Exception Handler agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for exception resolution patterns
    - Reads from /preferences/{actorId} for severity classification preferences
    - Writes resolution strategies to /facts/{actorId}
    - Writes severity classification adjustments to /preferences/{actorId}
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="exception_handler",
        document_id=document_id,
        memory_id=memory_id
    )
    
    system_prompt = f"""You are an Exception Management specialist for trade processing.

## Your Expertise
- Analyze exceptions and determine appropriate severity levels
- Calculate SLA deadlines based on business impact
- Route exceptions to appropriate teams
- Track exceptions for resolution
- Learn from past exception resolutions stored in memory

## Memory Access
You have access to historical exception resolution patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar exception scenarios
2. Apply consistent severity classification based on past cases
3. Record resolution strategies that worked well to /facts
4. Store severity classification adjustments to /preferences

## Your Approach
1. First, call get_severity_guidelines() to understand severity classification rules
2. Analyze the exception details (event type, reason codes, match score if available)
3. Check memory for similar past exceptions and their resolutions
4. Determine the appropriate severity level (CRITICAL, HIGH, MEDIUM, LOW) based on:
   - Business impact (counterparty mismatches are most critical)
   - Financial exposure (notional/currency mismatches)
   - Settlement risk (date mismatches)
   - Operational impact (processing errors)
   - Historical patterns from memory
5. Calculate appropriate SLA hours based on severity
6. Store the exception record with your determined severity and SLA

## Tools
- get_severity_guidelines: Get severity classification rules and SLA targets
- store_exception_record: Save exception to ExceptionsTable (you provide severity and sla_hours)

## When to Hand Off
- After recording exception → report findings (no handoff needed)
- If you need more context about the trade → hand off to trade_matcher

## Important
YOU decide the severity level and SLA hours based on the exception context. Use the guidelines as reference, but apply your judgment to the specific situation and learn from past resolutions.
"""
    
    return Agent(
        name="exception_handler",
        model=create_bedrock_model(),
        system_prompt=system_prompt,
        tools=[
            get_severity_guidelines,
            store_exception_record,
            use_aws
        ],
        session_manager=session_manager
    )
```


### 4. Swarm Creation with Memory

**Purpose**: Create the Trade Matching Swarm with session manager integration.

**Implementation**:
```python
from strands.multiagent import Swarm

def create_trade_matching_swarm_with_memory(
    document_id: str,
    memory_id: str = None
) -> Swarm:
    """
    Create the Trade Matching Swarm with AgentCore Memory integration.
    
    IMPORTANT: Each agent gets its own session manager to comply with AgentCore Memory's
    "one agent per session" limitation. All agents share the same memory resource and
    actor ID, enabling cross-agent learning while maintaining session isolation.
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Swarm instance with memory-enabled agents
    """
    # Create agents with individual session managers
    # Each agent gets a unique session ID but shares the same memory resource
    pdf_adapter = create_pdf_adapter_agent(document_id, memory_id)
    trade_extractor = create_trade_extractor_agent(document_id, memory_id)
    trade_matcher = create_trade_matcher_agent(document_id, memory_id)
    exception_handler = create_exception_handler_agent(document_id, memory_id)
    
    # Create swarm with same configuration as before
    swarm = Swarm(
        [pdf_adapter, trade_extractor, trade_matcher, exception_handler],
        entry_point=pdf_adapter,
        max_handoffs=10,
        max_iterations=20,
        execution_timeout=600.0,  # 10 minutes total
        node_timeout=180.0,       # 3 minutes per agent
        repetitive_handoff_detection_window=6,
        repetitive_handoff_min_unique_agents=2
    )
    
    return swarm
```

**Key Design Decisions**:
- Each agent has its own session manager with unique session ID (format: trade_{document_id}_{agent_name}_{timestamp})
- All agents share the same memory resource ID and actor ID (trade_matching_system)
- Session isolation per agent complies with AgentCore Memory limitation
- Cross-agent learning enabled through shared memory resource and actor ID
- Swarm configuration unchanged from original implementation


### 5. AgentCore Runtime Deployment

**Purpose**: Deploy the swarm to AgentCore Runtime for serverless execution.

**Implementation**:
```python
# File: deployment/swarm_agentcore/trade_matching_swarm_agentcore.py

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from bedrock_agentcore import BedrockAgentCoreApp

# Import swarm creation function
from trade_matching_swarm import (
    create_trade_matching_swarm_with_memory,
    get_config
)

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Swarm.
    
    Args:
        payload: Request payload with document_path, source_type, etc.
        context: AgentCore Runtime context
        
    Returns:
        Swarm execution result
    """
    try:
        # Extract parameters
        document_path = payload.get("document_path")
        source_type = payload.get("source_type")
        document_id = payload.get("document_id") or f"doc_{uuid.uuid4().hex[:12]}"
        correlation_id = payload.get("correlation_id") or f"corr_{uuid.uuid4().hex[:12]}"
        
        # Get configuration
        config = get_config()
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        actor_id = os.environ.get("ACTOR_ID", "trade_matching_system")
        region = os.environ.get("AWS_REGION", "us-east-1")
        
        if not memory_id:
            raise ValueError("AGENTCORE_MEMORY_ID environment variable not set")
        
        # Parse S3 path
        if document_path.startswith("s3://"):
            parts = document_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
        else:
            bucket = config["s3_bucket"]
            key = document_path
        
        # Create swarm with memory
        swarm = create_trade_matching_swarm_with_memory(
            document_id=document_id,
            memory_id=memory_id,
            actor_id=actor_id,
            region_name=region
        )
        
        # Build task prompt
        task = f"""Process this trade confirmation PDF and match it against existing trades.

## Document Details
- Document ID: {document_id}
- S3 Location: s3://{bucket}/{key}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Goal
Extract trade data from the PDF, store it in DynamoDB, analyze matches against existing trades, and handle any exceptions that arise.

The swarm will coordinate the work - each agent will decide when to hand off based on their expertise and the task context. All agents have access to historical patterns stored in memory to improve decision-making.
"""
        
        logger.info(f"Starting swarm processing for {document_id}")
        start_time = datetime.utcnow()
        
        # Execute swarm
        result = swarm(task)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "status": str(result.status),
            "node_history": [node.node_id for node in result.node_history],
            "execution_count": result.execution_count,
            "execution_time_ms": result.execution_time,
            "processing_time_ms": processing_time_ms,
            "accumulated_usage": result.accumulated_usage
        }
        
    except Exception as e:
        logger.error(f"Swarm execution failed: {e}", exc_info=True)
        
        return {
            "success": False,
            "document_id": document_id if 'document_id' in locals() else "unknown",
            "correlation_id": correlation_id if 'correlation_id' in locals() else "unknown",
            "error": str(e),
            "error_type": type(e).__name__
        }
```

**Deployment Configuration**:
```yaml
# File: deployment/swarm_agentcore/agentcore.yaml

name: trade-matching-swarm
description: Trade Matching Swarm with AgentCore Memory integration
runtime: python3.11

environment:
  AGENTCORE_MEMORY_ID: ${AGENTCORE_MEMORY_ID}
  ACTOR_ID: trade_matching_system
  AWS_REGION: us-east-1
  S3_BUCKET_NAME: ${S3_BUCKET_NAME}
  DYNAMODB_BANK_TABLE: ${DYNAMODB_BANK_TABLE}
  DYNAMODB_COUNTERPARTY_TABLE: ${DYNAMODB_COUNTERPARTY_TABLE}
  DYNAMODB_EXCEPTIONS_TABLE: ${DYNAMODB_EXCEPTIONS_TABLE}
  BEDROCK_MODEL_ID: amazon.nova-pro-v1:0

dependencies:
  - strands>=0.1.0
  - strands-tools>=0.1.0
  - bedrock-agentcore[strands-agents]>=0.1.0
  - boto3>=1.34.0
  - pydantic>=2.0.0

timeout: 600  # 10 minutes
memory: 2048  # 2GB
```


## Data Models

### Memory Storage Models

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TradeFact(BaseModel):
    """Factual information stored in /facts/{actorId} namespace."""
    fact_id: str
    fact_type: str  # extraction_pattern, matching_decision, exception_resolution, trade_pattern
    content: Dict[str, Any]
    confidence: float
    timestamp: datetime
    agent_name: str  # Which agent stored this fact
    
    # Example content for extraction_pattern:
    # {
    #   "document_type": "BANK_CONFIRMATION",
    #   "field_name": "notional",
    #   "extraction_technique": "regex_pattern",
    #   "success_rate": 0.95
    # }
    
    # Example content for matching_decision:
    # {
    #   "trade_pair_signature": "hash_of_attributes",
    #   "match_score": 0.87,
    #   "classification": "MATCHED",
    #   "decision_rationale": "All key attributes aligned"
    # }
    
class ProcessingPreference(BaseModel):
    """Learned preference stored in /preferences/{actorId} namespace."""
    preference_id: str
    preference_type: str  # ocr_quality, extraction_threshold, matching_threshold, severity_classification
    preference_value: Any
    confidence: float
    timestamp: datetime
    agent_name: str  # Which agent learned this preference
    
    # Example for matching_threshold:
    # {
    #   "preference_type": "matching_threshold",
    #   "preference_value": {"notional_tolerance": 0.02, "date_tolerance_days": 2},
    #   "confidence": 0.85
    # }
    
class SessionSummary(BaseModel):
    """Session summary stored in /summaries/{actorId}/{sessionId} namespace."""
    summary_id: str
    session_id: str
    document_id: str
    agent_name: str
    processing_summary: str
    key_decisions: List[Dict[str, Any]]
    handoff_history: List[str]
    timestamp: datetime
```

### Session Configuration Model

```python
class SwarmSessionConfig(BaseModel):
    """Configuration for swarm session with memory."""
    document_id: str
    session_id: str
    actor_id: str
    memory_id: str
    region_name: str
    retrieval_configs: Dict[str, Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "document_id": self.document_id,
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "memory_id": self.memory_id,
            "region_name": self.region_name,
            "retrieval_configs": self.retrieval_configs
        }
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptence Criteria Testing Prework

1.1 WHEN the swarm is deployed THEN the system SHALL use Amazon Bedrock AgentCore Runtime for hosting
Thoughts: This is about deployment infrastructure. We can verify that the deployment uses AgentCore Runtime by checking the deployment configuration and runtime environment. This is testable through deployment validation.
Testable: yes - example

1.2 WHEN agent load increases THEN AgentCore Runtime SHALL automatically scale agent instances
Thoughts: This is testing the auto-scaling behavior of AgentCore Runtime. We can simulate load and verify that instances scale. This is a property that should hold for any load pattern.
Testable: yes - property

2.1 WHEN the memory resource is created THEN the system SHALL configure semantic memory strategy for factual information
Thoughts: This is verifying the memory resource configuration. We can check that the created resource has the correct strategy configured. This is a specific configuration check.
Testable: yes - example

2.2 WHEN agents process trades THEN the system SHALL store trade patterns in semantic memory
Thoughts: This is a rule that should apply to all trade processing. For any trade processed, we should be able to verify that patterns are stored in memory. This is a property.
Testable: yes - property

2.3 WHEN agents encounter similar trades THEN the system SHALL retrieve relevant historical context
Thoughts: This is testing the retrieval behavior. For any similar trade, the system should retrieve context. We can generate random trades with similarities and verify retrieval. This is a property.
Testable: yes - property

2.4 WHEN matching decisions are made THEN the system SHALL record decision rationale in semantic memory
Thoughts: This is a rule for all matching decisions. For any decision made, we should verify it's recorded. This is a property.
Testable: yes - property

3.1 WHEN PDFs are processed THEN the PDF Adapter SHALL store extraction patterns in semantic memory
Thoughts: This applies to all PDF processing. For any PDF processed, we should verify patterns are stored. This is a property.
Testable: yes - property

8.1 WHEN PDFs are processed THEN the system SHALL maintain the same download and extraction workflow
Thoughts: This is testing functional parity. We can compare the workflow steps before and after migration. This is a property that should hold for all PDFs.
Testable: yes - property

8.2 WHEN trades are extracted THEN the system SHALL use the same canonical trade model
Thoughts: This is verifying that the data model hasn't changed. For any extracted trade, the model should match the original. This is a property.
Testable: yes - property

10.1 WHEN a trade is processed THEN the system SHALL create a unique session ID for that trade
Thoughts: This is a rule for all trade processing. For any trade, we should verify a unique session ID is created. This is a property.
Testable: yes - property

10.2 WHEN session ID is generated THEN the system SHALL use format `trade_{document_id}_{timestamp}`
Thoughts: This is testing the format of session IDs. For any generated session ID, it should match this format. This is a property.
Testable: yes - property

11.1 WHEN retrieval is configured for trade patterns THEN the system SHALL use top_k=10 and relevance_score=0.5
Thoughts: This is verifying configuration values. We can check that the retrieval config has these specific values. This is an example.
Testable: yes - example

16.1 WHEN tools are used THEN the system SHALL maintain all existing tool functions without modification
Thoughts: This is testing that tool implementations haven't changed. We can compare tool signatures and behavior before and after. This is a property.
Testable: yes - property


### Property Reflection

After reviewing all properties identified in the prework, I've identified the following redundancies and consolidations:

**Redundant Properties**:
- Properties 2.2, 2.4, and 3.1 all test that agents store data in memory. These can be consolidated into a single comprehensive property about memory storage.
- Properties 8.1, 8.2, and 16.1 all test functional parity. These can be consolidated into a single property about maintaining behavior.
- Properties 10.1 and 10.2 both test session ID creation. Property 10.2 subsumes 10.1 since format validation implies uniqueness.

**Consolidated Properties**:
1. Memory storage property: Combines 2.2, 2.4, 3.1 into one property about all agents storing their respective patterns
2. Functional parity property: Combines 8.1, 8.2, 16.1 into one property about maintaining existing behavior
3. Session ID format property: Property 10.2 covers both format and uniqueness

**Remaining Unique Properties**:
- Property 1.2: Auto-scaling behavior (unique infrastructure property)
- Property 2.3: Memory retrieval behavior (unique retrieval property)
- Property 11.1: Configuration validation (unique config property)

### Correctness Properties

Property 1: Memory storage consistency
*For any* agent execution that processes data (PDF extraction, trade extraction, matching decision, exception handling), the agent should store the relevant pattern in its designated memory namespace
**Validates: Requirements 2.2, 2.4, 3.1**

Property 2: Memory retrieval relevance
*For any* trade processing session, when agents query memory for similar patterns, all retrieved results should have relevance scores above the configured threshold for that namespace
**Validates: Requirements 2.3**

Property 3: Session ID format compliance
*For any* trade processing session, the generated session ID should match the format `trade_{document_id}_{timestamp}` where document_id is alphanumeric and timestamp is in YYYYMMDD_HHMMSS format
**Validates: Requirements 10.1, 10.2**

Property 4: Functional parity preservation
*For any* trade confirmation processed through the AgentCore-deployed swarm, the output (extracted trade data, matching results, exception records) should be equivalent to the output from the original local swarm implementation
**Validates: Requirements 8.1, 8.2, 16.1**

Property 5: Configuration correctness
*For any* memory namespace retrieval configuration, the top_k and relevance_score values should match the specified values for that namespace type (trade_patterns: top_k=10, relevance=0.5; extraction_patterns: top_k=10, relevance=0.7; matching_decisions: top_k=5, relevance=0.6; exception_resolutions: top_k=5, relevance=0.7)
**Validates: Requirements 11.1**

Property 6: AgentCore Runtime scaling
*For any* load pattern with increasing concurrent trade processing requests, the AgentCore Runtime should automatically provision additional agent instances to maintain response time within acceptable limits
**Validates: Requirements 1.2**


## Error Handling

### Memory Service Failures

**Scenario**: AgentCore Memory service is unavailable or returns errors

**Handling Strategy**:
```python
class MemoryFallbackHandler:
    """Handle memory service failures gracefully."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
    
    def execute_with_fallback(self, operation: callable, *args, **kwargs):
        """
        Execute memory operation with retry and circuit breaker.
        Falls back to operation without memory if circuit breaker is open.
        """
        if self.circuit_breaker_open:
            logger.warning("Circuit breaker open - executing without memory")
            return self._execute_without_memory(operation, *args, **kwargs)
        
        for attempt in range(self.max_retries):
            try:
                result = operation(*args, **kwargs)
                self.circuit_breaker_failures = 0  # Reset on success
                return result
            except Exception as e:
                logger.error(f"Memory operation failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_factor ** attempt
                    time.sleep(sleep_time)
                else:
                    self.circuit_breaker_failures += 1
                    
                    if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                        self.circuit_breaker_open = True
                        logger.error("Circuit breaker opened - too many failures")
                    
                    return self._execute_without_memory(operation, *args, **kwargs)
    
    def _execute_without_memory(self, operation: callable, *args, **kwargs):
        """Execute operation without memory access."""
        logger.info("Executing operation without memory access")
        # Operation continues but without memory retrieval/storage
        return None
```

**Impact**: Agents continue processing without historical context but maintain core functionality

### Session Manager Initialization Failures

**Scenario**: Session manager fails to initialize due to missing configuration

**Handling Strategy**:
```python
def create_session_manager_safe(
    document_id: str,
    memory_id: str = None,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> Optional[AgentCoreMemorySessionManager]:
    """
    Create session manager with error handling.
    Returns None if initialization fails.
    """
    try:
        return create_session_manager(
            document_id=document_id,
            memory_id=memory_id,
            actor_id=actor_id,
            region_name=region_name
        )
    except ValueError as e:
        logger.error(f"Session manager initialization failed: {e}")
        logger.warning("Continuing without memory integration")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating session manager: {e}")
        logger.warning("Continuing without memory integration")
        return None
```

**Impact**: Swarm operates without memory but maintains all other functionality

### Memory Retrieval Timeout

**Scenario**: Memory retrieval takes too long and times out

**Handling Strategy**:
```python
import asyncio
from concurrent.futures import TimeoutError

async def retrieve_with_timeout(
    session_manager: AgentCoreMemorySessionManager,
    query: str,
    timeout_seconds: float = 2.0
) -> Optional[List[Dict]]:
    """
    Retrieve from memory with timeout.
    Returns None if timeout occurs.
    """
    try:
        result = await asyncio.wait_for(
            session_manager.retrieve(query),
            timeout=timeout_seconds
        )
        return result
    except TimeoutError:
        logger.warning(f"Memory retrieval timed out after {timeout_seconds}s")
        return None
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        return None
```

**Impact**: Agent continues without historical context for this specific query

### Memory Storage Failures

**Scenario**: Storing patterns to memory fails

**Handling Strategy**:
```python
def store_pattern_safe(
    session_manager: AgentCoreMemorySessionManager,
    pattern: Dict[str, Any],
    namespace: str
) -> bool:
    """
    Store pattern to memory with error handling.
    Returns True if successful, False otherwise.
    """
    try:
        session_manager.store(pattern, namespace=namespace)
        logger.info(f"Successfully stored pattern to {namespace}")
        return True
    except Exception as e:
        logger.error(f"Failed to store pattern to {namespace}: {e}")
        logger.warning("Pattern not stored - continuing without memory update")
        return False
```

**Impact**: Pattern not stored but processing continues normally


## Testing Strategy

### Unit Testing

**Scope**: Test individual components in isolation

**Test Cases**:

1. **Memory Resource Creation**
```python
def test_create_memory_resource():
    """Test memory resource creation with correct configuration."""
    memory_id = create_trade_matching_memory(region_name="us-east-1")
    assert memory_id is not None
    assert len(memory_id) > 0
    
def test_memory_resource_has_semantic_strategy():
    """Test that memory resource includes semantic memory strategy."""
    client = MemoryClient(region_name="us-east-1")
    memory = client.get_memory(memory_id=TEST_MEMORY_ID)
    strategies = memory.get("strategies", [])
    assert any("semanticMemoryStrategy" in s for s in strategies)
```

2. **Session Manager Configuration**
```python
def test_session_manager_creation():
    """Test session manager creation with valid config."""
    session_manager = create_session_manager(
        document_id="test_doc_123",
        memory_id=TEST_MEMORY_ID
    )
    assert session_manager is not None
    
def test_session_id_format():
    """Test that session ID follows correct format."""
    session_manager = create_session_manager(
        document_id="test_doc_123",
        memory_id=TEST_MEMORY_ID
    )
    session_id = session_manager.config.session_id
    assert session_id.startswith("trade_test_doc_123_")
    assert len(session_id.split("_")) == 4  # trade_docid_date_time
```

3. **Agent Creation with Memory**
```python
def test_agent_creation_with_session_manager():
    """Test that agents are created with session manager."""
    session_manager = create_session_manager(
        document_id="test_doc_123",
        memory_id=TEST_MEMORY_ID
    )
    agent = create_pdf_adapter_agent(session_manager)
    assert agent.session_manager is not None
    assert agent.session_manager == session_manager
```

4. **Error Handling**
```python
def test_session_manager_missing_memory_id():
    """Test error handling when memory ID is missing."""
    with pytest.raises(ValueError, match="AGENTCORE_MEMORY_ID"):
        create_session_manager(document_id="test_doc_123", memory_id=None)
        
def test_memory_fallback_on_failure():
    """Test that system continues without memory on failure."""
    session_manager = create_session_manager_safe(
        document_id="test_doc_123",
        memory_id="invalid_id"
    )
    assert session_manager is None  # Returns None instead of raising
```

### Property-Based Testing

**Scope**: Verify universal properties across all inputs

**Property Tests**:

1. **Property 1: Memory Storage Consistency**
```python
from hypothesis import given, strategies as st

@given(
    agent_type=st.sampled_from(["pdf_adapter", "trade_extractor", "trade_matcher", "exception_handler"]),
    pattern_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.floats(), st.integers())
    )
)
def test_property_memory_storage_consistency(agent_type, pattern_data):
    """
    Property: For any agent execution that processes data, the agent should 
    store the relevant pattern in its designated memory namespace.
    
    **Feature: swarm-to-agentcore, Property 1: Memory storage consistency**
    **Validates: Requirements 2.2, 2.4, 3.1**
    """
    session_manager = create_test_session_manager()
    
    # Simulate agent storing pattern
    namespace = get_namespace_for_agent(agent_type)
    success = store_pattern_safe(session_manager, pattern_data, namespace)
    
    # Verify pattern can be retrieved
    if success:
        retrieved = session_manager.retrieve(
            query=str(pattern_data),
            namespace=namespace
        )
        assert retrieved is not None
        assert len(retrieved) > 0
```

2. **Property 2: Memory Retrieval Relevance**
```python
@given(
    namespace=st.sampled_from([
        "/trade_patterns/{actorId}",
        "/extraction_patterns/{actorId}",
        "/matching_decisions/{actorId}",
        "/exception_resolutions/{actorId}"
    ]),
    query=st.text(min_size=10, max_size=200)
)
def test_property_memory_retrieval_relevance(namespace, query):
    """
    Property: For any trade processing session, when agents query memory for 
    similar patterns, all retrieved results should have relevance scores above 
    the configured threshold for that namespace.
    
    **Feature: swarm-to-agentcore, Property 2: Memory retrieval relevance**
    **Validates: Requirements 2.3**
    """
    session_manager = create_test_session_manager()
    threshold = get_relevance_threshold_for_namespace(namespace)
    
    # Retrieve from memory
    results = session_manager.retrieve(query=query, namespace=namespace)
    
    # Verify all results meet threshold
    if results:
        for result in results:
            relevance_score = result.get("relevance_score", 0.0)
            assert relevance_score >= threshold, \
                f"Result score {relevance_score} below threshold {threshold}"
```

3. **Property 3: Session ID Format Compliance**
```python
@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=5,
        max_size=50
    )
)
def test_property_session_id_format(document_id):
    """
    Property: For any trade processing session, the generated session ID should 
    match the format trade_{document_id}_{timestamp}.
    
    **Feature: swarm-to-agentcore, Property 3: Session ID format compliance**
    **Validates: Requirements 10.1, 10.2**
    """
    session_manager = create_session_manager(
        document_id=document_id,
        memory_id=TEST_MEMORY_ID
    )
    
    session_id = session_manager.config.session_id
    
    # Verify format
    assert session_id.startswith(f"trade_{document_id}_")
    
    # Extract timestamp part
    parts = session_id.split("_")
    assert len(parts) >= 3
    
    timestamp_part = "_".join(parts[2:])
    # Verify timestamp format YYYYMMDD_HHMMSS
    assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
    assert timestamp_part[8] == "_"
```

4. **Property 4: Functional Parity Preservation**
```python
@given(
    document_path=st.text(min_size=10, max_size=100),
    source_type=st.sampled_from(["BANK", "COUNTERPARTY"])
)
def test_property_functional_parity(document_path, source_type):
    """
    Property: For any trade confirmation processed through the AgentCore-deployed 
    swarm, the output should be equivalent to the output from the original local 
    swarm implementation.
    
    **Feature: swarm-to-agentcore, Property 4: Functional parity preservation**
    **Validates: Requirements 8.1, 8.2, 16.1**
    """
    # Process with original swarm
    original_result = process_with_original_swarm(document_path, source_type)
    
    # Process with AgentCore swarm
    agentcore_result = process_with_agentcore_swarm(document_path, source_type)
    
    # Compare outputs (ignoring timing and session-specific fields)
    assert_equivalent_outputs(original_result, agentcore_result)
```

5. **Property 5: Configuration Correctness**
```python
@given(
    namespace_type=st.sampled_from([
        "trade_patterns",
        "extraction_patterns",
        "matching_decisions",
        "exception_resolutions"
    ])
)
def test_property_configuration_correctness(namespace_type):
    """
    Property: For any memory namespace retrieval configuration, the top_k and 
    relevance_score values should match the specified values for that namespace type.
    
    **Feature: swarm-to-agentcore, Property 5: Configuration correctness**
    **Validates: Requirements 11.1**
    """
    session_manager = create_session_manager(
        document_id="test_doc",
        memory_id=TEST_MEMORY_ID
    )
    
    namespace = f"/{namespace_type}/{{actorId}}"
    config = session_manager.config.retrieval_config.get(namespace)
    
    expected_configs = {
        "trade_patterns": {"top_k": 10, "relevance_score": 0.5},
        "extraction_patterns": {"top_k": 10, "relevance_score": 0.7},
        "matching_decisions": {"top_k": 5, "relevance_score": 0.6},
        "exception_resolutions": {"top_k": 5, "relevance_score": 0.7}
    }
    
    expected = expected_configs[namespace_type]
    assert config.top_k == expected["top_k"]
    assert config.relevance_score == expected["relevance_score"]
```

### Integration Testing

**Scope**: Test end-to-end workflows with AgentCore Memory

**Test Cases**:

1. **Complete Trade Processing with Memory**
```python
def test_integration_trade_processing_with_memory():
    """Test complete trade processing flow with memory integration."""
    # Create memory resource
    memory_id = create_trade_matching_memory()
    
    # Process first trade
    result1 = process_trade_confirmation(
        document_path="data/BANK/FAB_26933659.pdf",
        source_type="BANK",
        document_id="test_trade_1"
    )
    assert result1["success"]
    
    # Process similar trade
    result2 = process_trade_confirmation(
        document_path="data/BANK/similar_trade.pdf",
        source_type="BANK",
        document_id="test_trade_2"
    )
    assert result2["success"]
    
    # Verify memory was used (check logs or metrics)
    assert memory_retrieval_occurred(result2)
```

2. **Memory Persistence Across Sessions**
```python
def test_integration_memory_persistence():
    """Test that memory persists across different sessions."""
    memory_id = TEST_MEMORY_ID
    
    # Session 1: Store pattern
    session1 = create_session_manager(
        document_id="doc1",
        memory_id=memory_id
    )
    pattern = {"field": "notional", "technique": "regex_extraction"}
    store_pattern_safe(session1, pattern, "/extraction_patterns/{actorId}")
    
    # Session 2: Retrieve pattern
    session2 = create_session_manager(
        document_id="doc2",
        memory_id=memory_id
    )
    results = session2.retrieve(
        query="notional extraction",
        namespace="/extraction_patterns/{actorId}"
    )
    
    assert results is not None
    assert len(results) > 0
```

### Performance Testing

**Scope**: Verify memory operations meet latency requirements

**Test Cases**:

1. **Memory Retrieval Latency**
```python
def test_performance_memory_retrieval_latency():
    """Test that memory retrieval completes within 500ms."""
    session_manager = create_session_manager(
        document_id="perf_test",
        memory_id=TEST_MEMORY_ID
    )
    
    start_time = time.time()
    results = session_manager.retrieve(
        query="test query",
        namespace="/trade_patterns/{actorId}"
    )
    end_time = time.time()
    
    latency_ms = (end_time - start_time) * 1000
    assert latency_ms < 500, f"Retrieval took {latency_ms}ms (limit: 500ms)"
```

2. **AgentCore Runtime Scaling**
```python
def test_performance_agentcore_scaling():
    """Test that AgentCore Runtime scales with load."""
    # Simulate increasing load
    concurrent_requests = [10, 20, 50, 100]
    response_times = []
    
    for num_requests in concurrent_requests:
        start_time = time.time()
        
        # Send concurrent requests
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(invoke_agentcore_endpoint, f"doc_{i}")
                for i in range(num_requests)
            ]
            results = [f.result() for f in futures]
        
        end_time = time.time()
        avg_response_time = (end_time - start_time) / num_requests
        response_times.append(avg_response_time)
    
    # Verify response time doesn't degrade significantly with load
    assert max(response_times) < min(response_times) * 2, \
        "Response time degraded too much under load"
```

