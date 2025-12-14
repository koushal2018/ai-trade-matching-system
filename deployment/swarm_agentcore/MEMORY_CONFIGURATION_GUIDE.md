# AgentCore Memory Configuration Guide

This guide explains how to configure and optimize AgentCore Memory for the Trade Matching Swarm, including memory strategies, namespace patterns, and retrieval configuration.

## Table of Contents

1. [Memory Architecture Overview](#memory-architecture-overview)
2. [Memory Strategies](#memory-strategies)
3. [Namespace Patterns](#namespace-patterns)
4. [Retrieval Configuration](#retrieval-configuration)
5. [Session Management](#session-management)
6. [Configuration Examples](#configuration-examples)
7. [Best Practices](#best-practices)
8. [Performance Tuning](#performance-tuning)

## Memory Architecture Overview

The Trade Matching Swarm uses Amazon Bedrock AgentCore Memory to enable persistent learning across trade processing sessions. The memory system stores patterns, decisions, and preferences that improve agent performance over time.

### Key Concepts

- **Memory Resource**: A persistent storage container for agent knowledge
- **Memory Strategy**: A built-in pattern for organizing and retrieving information
- **Namespace**: A scoped storage location within a strategy
- **Actor ID**: A unique identifier for the user or system (shared across agents)
- **Session ID**: A unique identifier for a specific trade processing session (unique per agent)
- **Session Manager**: Component that manages memory access and retrieval

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              AgentCore Memory Resource                       │
│              (TradeMatchingMemory)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Strategy 1: Semantic Memory (TradeFacts)          │    │
│  │  Namespace: /facts/{actorId}                       │    │
│  │  - Trade patterns                                  │    │
│  │  - Field mappings                                  │    │
│  │  - Matching decisions                              │    │
│  │  - Exception resolutions                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Strategy 2: User Preference (ProcessingPreferences)│    │
│  │  Namespace: /preferences/{actorId}                 │    │
│  │  - Extraction techniques                           │    │
│  │  - Matching thresholds                             │    │
│  │  - Severity classifications                        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Strategy 3: Summary Memory (SessionSummaries)     │    │
│  │  Namespace: /summaries/{actorId}/{sessionId}       │    │
│  │  - Trade processing summaries                      │    │
│  │  - Agent handoff history                           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Memory Strategies

AgentCore Memory provides three built-in strategies, each optimized for different types of information.

### 1. Semantic Memory Strategy

**Purpose**: Store factual information and patterns that should persist long-term.

**Configuration**:
```python
{
    "semanticMemoryStrategy": {
        "name": "TradeFacts",
        "namespaces": ["/facts/{actorId}"]
    }
}
```

**Use Cases**:
- Trade processing patterns (e.g., "Bank confirmations typically have notional in section 3")
- Field extraction mappings (e.g., "Trade_ID field maps to 'Reference Number' in counterparty docs")
- Matching decisions with rationale (e.g., "Trades with 2% notional difference classified as MATCHED")
- Exception resolution strategies (e.g., "Date mismatches > 5 days require HITL review")

**Characteristics**:
- Long-term persistence (survives across sessions)
- Semantic search enabled (finds conceptually similar information)
- Automatic fact extraction from agent conversations
- Relevance-based retrieval

**Example Storage**:
```python
# Agent stores a fact during processing
"I learned that when processing Bank of America confirmations, 
the notional amount is always in the 'Transaction Details' section 
with the label 'Notional Amount (USD)'. This pattern has worked 
successfully in 15 out of 15 cases."
```

### 2. User Preference Memory Strategy

**Purpose**: Store learned preferences and configuration adjustments.

**Configuration**:
```python
{
    "userPreferenceMemoryStrategy": {
        "name": "ProcessingPreferences",
        "namespaces": ["/preferences/{actorId}"]
    }
}
```

**Use Cases**:
- OCR quality preferences (e.g., "Use higher DPI for scanned documents")
- Extraction thresholds (e.g., "Confidence threshold for field extraction: 0.85")
- Matching tolerance adjustments (e.g., "Notional tolerance increased to 3% for FX swaps")
- Severity classification preferences (e.g., "Counterparty mismatches always CRITICAL")

**Characteristics**:
- Preference-specific storage
- Optimized for configuration values
- Supports preference updates and overrides
- Fast retrieval for decision-making

**Example Storage**:
```python
# Agent stores a preference
"For trade matching, I prefer to use a 3% notional tolerance 
for FX swaps instead of the default 2%, based on feedback 
from 5 HITL reviews that indicated this threshold reduces 
false positives."
```

### 3. Summary Memory Strategy

**Purpose**: Store session-specific summaries and context.

**Configuration**:
```python
{
    "summaryMemoryStrategy": {
        "name": "SessionSummaries",
        "namespaces": ["/summaries/{actorId}/{sessionId}"]
    }
}
```

**Use Cases**:
- Trade processing summaries (e.g., "Processed FAB_26933659: MATCHED with 92% confidence")
- Agent handoff history (e.g., "pdf_adapter → trade_extractor → trade_matcher")
- Session-specific context (e.g., "Document had poor OCR quality, required manual review")
- Processing metrics (e.g., "Extraction took 15s, matching took 12s")

**Characteristics**:
- Session-scoped (isolated per trade processing session)
- Automatic summarization of agent conversations
- Useful for debugging and audit trails
- Can be queried for similar past sessions

**Example Storage**:
```python
# Agent stores a session summary
"Trade FAB_26933659 processed successfully. PDF Adapter extracted 
text in 12s, Trade Extractor identified 18 fields with 95% confidence, 
Trade Matcher found exact match with counterparty trade GCS381315 
(92% confidence). No exceptions raised."
```

## Namespace Patterns

Namespaces provide scoped storage within each memory strategy. The Trade Matching Swarm uses standard AgentCore namespace patterns.

### Namespace Structure

```
/facts/{actorId}
/preferences/{actorId}
/summaries/{actorId}/{sessionId}
```

### Variable Substitution

- `{actorId}`: Replaced with the configured actor ID (default: `trade_matching_system`)
- `{sessionId}`: Replaced with the unique session ID for each agent (format: `trade_{document_id}_{agent_name}_{timestamp}`)

### Namespace Isolation

**Actor-Level Isolation**:
- All agents share the same `actorId` (trade_matching_system)
- Enables cross-agent learning (PDF Adapter learns from Trade Matcher's decisions)
- Facts and preferences are shared across all agents

**Session-Level Isolation**:
- Each agent gets a unique `sessionId` per trade
- Summaries are isolated per agent per trade
- Prevents session data leakage between concurrent processing

### Example Namespace Resolution

For a trade processed by the PDF Adapter:

```python
document_id = "FAB_26933659"
agent_name = "pdf_adapter"
timestamp = "20231215_143022"
actor_id = "trade_matching_system"

# Resolved namespaces:
facts_namespace = "/facts/trade_matching_system"
preferences_namespace = "/preferences/trade_matching_system"
summaries_namespace = "/summaries/trade_matching_system/trade_FAB_26933659_pdf_adapter_20231215_143022"
```

## Retrieval Configuration

Retrieval configuration controls how agents query memory for relevant information.

### Configuration Parameters

Each namespace can have its own retrieval configuration:

```python
RetrievalConfig(
    top_k=10,              # Maximum number of results to return
    relevance_score=0.6    # Minimum relevance threshold (0.0-1.0)
)
```

### Default Configuration

The Trade Matching Swarm uses these retrieval settings:

```python
retrieval_config = {
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
```

### Retrieval Strategy by Namespace

#### Facts Namespace (`/facts/{actorId}`)

- **top_k=10**: Retrieve up to 10 relevant facts
- **relevance_score=0.6**: Moderate threshold (60% similarity)
- **Rationale**: Cast a wider net for factual patterns; agents can filter further

**Example Query**:
```
"How should I extract the notional field from a Bank of America confirmation?"

Retrieved Facts:
1. [0.87] Bank of America confirmations have notional in 'Transaction Details'
2. [0.82] Notional field labeled as 'Notional Amount (USD)' in BoA docs
3. [0.75] Use regex pattern '\$[\d,]+\.\d{2}' for USD notional extraction
4. [0.68] BoA confirmations use consistent formatting across all products
5. [0.62] Notional appears on page 1, section 3 in 95% of BoA docs
```

#### Preferences Namespace (`/preferences/{actorId}`)

- **top_k=5**: Retrieve up to 5 relevant preferences
- **relevance_score=0.7**: Higher threshold (70% similarity)
- **Rationale**: Preferences should be highly relevant; fewer results needed

**Example Query**:
```
"What notional tolerance should I use for FX swap matching?"

Retrieved Preferences:
1. [0.89] FX swaps: use 3% notional tolerance (updated from 2%)
2. [0.78] Interest rate swaps: use 2% notional tolerance
3. [0.72] Options: use 5% notional tolerance due to premium variations
```

#### Summaries Namespace (`/summaries/{actorId}/{sessionId}`)

- **top_k=5**: Retrieve up to 5 relevant summaries
- **relevance_score=0.5**: Lower threshold (50% similarity)
- **Rationale**: Summaries provide context; cast wider net for similar sessions

**Example Query**:
```
"Have we processed similar trades from this counterparty before?"

Retrieved Summaries:
1. [0.78] Trade GCS381315: Same counterparty, similar notional, MATCHED
2. [0.65] Trade GCS381200: Same counterparty, different product, MATCHED
3. [0.58] Trade GCS380950: Same counterparty, date mismatch, REVIEW_REQUIRED
4. [0.52] Trade GCS380800: Same counterparty, notional mismatch, BREAK
```

### Tuning Retrieval Parameters

#### Increasing Precision (Fewer, More Relevant Results)

```python
# Higher relevance threshold, fewer results
RetrievalConfig(
    top_k=3,
    relevance_score=0.8
)
```

**Use When**:
- Agent needs highly confident information
- False positives are costly
- Processing time is critical

#### Increasing Recall (More Results, Lower Threshold)

```python
# Lower relevance threshold, more results
RetrievalConfig(
    top_k=20,
    relevance_score=0.4
)
```

**Use When**:
- Agent needs comprehensive context
- False negatives are costly
- Agent can filter results effectively

## Session Management

Each agent in the swarm gets its own session manager with a unique session ID.

### Session Manager Creation

```python
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
    memory_id: str,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> AgentCoreMemorySessionManager:
    """Create session manager for a specific agent."""
    
    # Generate unique session ID
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    session_id = f"trade_{document_id}_{agent_name}_{timestamp}"
    
    # Configure retrieval for all namespaces
    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config={
            "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.6),
            "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=5, relevance_score=0.5)
        }
    )
    
    return AgentCoreMemorySessionManager(
        agentcore_memory_config=config,
        region_name=region_name
    )
```

### Session ID Format

```
trade_{document_id}_{agent_name}_{timestamp}
```

**Components**:
- `trade_`: Prefix indicating trade processing session
- `{document_id}`: Unique document identifier (e.g., FAB_26933659)
- `{agent_name}`: Agent name (pdf_adapter, trade_extractor, trade_matcher, exception_handler)
- `{timestamp}`: UTC timestamp in format YYYYMMDD_HHMMSS

**Examples**:
```
trade_FAB_26933659_pdf_adapter_20231215_143022
trade_FAB_26933659_trade_extractor_20231215_143045
trade_FAB_26933659_trade_matcher_20231215_143112
trade_FAB_26933659_exception_handler_20231215_143145
```

### Why Unique Session IDs Per Agent?

AgentCore Memory has a limitation: **one agent per session**. To comply with this:

- Each agent gets its own session manager
- Each session manager has a unique session ID
- All agents share the same memory resource ID and actor ID
- This enables cross-agent learning while maintaining session isolation

## Configuration Examples

### Example 1: Basic Memory Setup

```python
from bedrock_agentcore.memory import MemoryClient

def create_trade_matching_memory(region_name: str = "us-east-1") -> str:
    """Create AgentCore Memory resource with built-in strategies."""
    
    client = MemoryClient(region_name=region_name)
    
    memory = client.create_memory_and_wait(
        name="TradeMatchingMemory",
        description="Multi-strategy memory for trade matching system",
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
    
    return memory.get('id')
```

### Example 2: Agent with Memory

```python
from strands import Agent
from strands.models import BedrockModel

def create_pdf_adapter_agent(document_id: str, memory_id: str) -> Agent:
    """Create PDF Adapter agent with memory integration."""
    
    # Create session manager
    session_manager = create_agent_session_manager(
        agent_name="pdf_adapter",
        document_id=document_id,
        memory_id=memory_id
    )
    
    # Create agent with session manager
    return Agent(
        name="pdf_adapter",
        model=BedrockModel(
            model_id="amazon.nova-pro-v1:0",
            region_name="us-east-1",
            temperature=0.1,
            max_tokens=4096
        ),
        system_prompt="""You are a PDF Adapter specialist.
        
        You have access to historical extraction patterns in memory.
        Check memory for similar document layouts before processing.""",
        tools=[download_pdf_from_s3, extract_text_with_bedrock, save_canonical_output],
        session_manager=session_manager
    )
```

### Example 3: Custom Retrieval Configuration

```python
# High-precision configuration for critical decisions
high_precision_config = {
    "/facts/{actorId}": RetrievalConfig(
        top_k=3,
        relevance_score=0.85
    ),
    "/preferences/{actorId}": RetrievalConfig(
        top_k=2,
        relevance_score=0.90
    ),
    "/summaries/{actorId}/{sessionId}": RetrievalConfig(
        top_k=3,
        relevance_score=0.75
    )
}

# High-recall configuration for exploratory analysis
high_recall_config = {
    "/facts/{actorId}": RetrievalConfig(
        top_k=20,
        relevance_score=0.4
    ),
    "/preferences/{actorId}": RetrievalConfig(
        top_k=10,
        relevance_score=0.5
    ),
    "/summaries/{actorId}/{sessionId}": RetrievalConfig(
        top_k=15,
        relevance_score=0.3
    )
}
```

## Best Practices

### 1. Memory Storage

**DO**:
- Store factual, verifiable information in semantic memory
- Store configuration values and thresholds in preference memory
- Store session context and summaries in summary memory
- Include confidence scores with stored facts
- Reference specific examples when storing patterns

**DON'T**:
- Store sensitive information (PII, credentials) in memory
- Store temporary or transient data in semantic memory
- Store large binary data (use S3 references instead)
- Store duplicate information across namespaces

### 2. Retrieval Optimization

**DO**:
- Use higher relevance thresholds for critical decisions
- Use lower relevance thresholds for exploratory queries
- Adjust top_k based on expected result diversity
- Monitor retrieval latency and adjust as needed
- Test retrieval configurations with real queries

**DON'T**:
- Set relevance_score too low (< 0.3) - too many irrelevant results
- Set relevance_score too high (> 0.9) - too few results
- Set top_k too high (> 50) - performance impact
- Use same configuration for all namespaces

### 3. Session Management

**DO**:
- Create unique session IDs per agent per trade
- Use consistent actor ID across all agents
- Clean up old session data periodically
- Log session IDs for debugging
- Include timestamp in session IDs

**DON'T**:
- Reuse session IDs across different trades
- Use different actor IDs for the same system
- Create session managers without error handling
- Forget to pass session manager to agents

### 4. Memory Maintenance

**DO**:
- Monitor memory usage and growth
- Archive old session summaries periodically
- Review and update preferences based on feedback
- Validate stored facts for accuracy
- Set up alerts for memory errors

**DON'T**:
- Let memory grow unbounded
- Store outdated or incorrect information
- Ignore memory retrieval failures
- Skip memory validation in testing

## Performance Tuning

### Latency Optimization

**Target**: Memory retrieval < 500ms

**Strategies**:
1. **Reduce top_k**: Fewer results = faster retrieval
2. **Increase relevance_score**: Higher threshold = fewer candidates to score
3. **Optimize queries**: More specific queries = better semantic matching
4. **Cache frequent queries**: Store common results in application cache

### Memory Size Optimization

**Target**: Keep memory resource under 10GB

**Strategies**:
1. **Archive old summaries**: Move session data > 30 days to S3
2. **Deduplicate facts**: Remove redundant or similar facts
3. **Compress preferences**: Consolidate similar preferences
4. **Set retention policies**: Auto-delete old data

### Retrieval Quality Optimization

**Target**: > 80% of retrieved results are relevant

**Strategies**:
1. **Tune relevance thresholds**: Test with real queries
2. **Improve fact quality**: Store more specific, detailed facts
3. **Add context to queries**: Include relevant metadata
4. **Monitor relevance scores**: Track distribution over time

### Example Monitoring Query

```python
import boto3
from datetime import datetime, timedelta

def monitor_memory_performance(memory_id: str, region: str = "us-east-1"):
    """Monitor memory retrieval performance."""
    
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    # Get retrieval latency metrics
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/BedrockAgentCore/Memory',
        MetricName='RetrievalLatency',
        Dimensions=[{'Name': 'MemoryId', 'Value': memory_id}],
        StartTime=datetime.utcnow() - timedelta(hours=24),
        EndTime=datetime.utcnow(),
        Period=3600,
        Statistics=['Average', 'Maximum', 'Minimum']
    )
    
    for datapoint in response['Datapoints']:
        print(f"Time: {datapoint['Timestamp']}")
        print(f"  Avg: {datapoint['Average']:.2f}ms")
        print(f"  Max: {datapoint['Maximum']:.2f}ms")
        print(f"  Min: {datapoint['Minimum']:.2f}ms")
```

---

**Memory Configuration Complete!** Your Trade Matching Swarm is now configured with optimized memory strategies for persistent learning.
