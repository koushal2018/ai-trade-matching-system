# AgentCore Memory Integration Checklist

## ✅ Pre-Integration (Complete)

- [x] AgentCore Memory resource created
  - Memory ID: `trade_matching_agent_mem-SxPFir3bbF`
  - ARN: `arn:aws:bedrock-agentcore:us-east-1:401552979575:memory/trade_matching_agent_mem-SxPFir3bbF`
  - Region: `us-east-1`

- [x] Memory integration module created (`memory_integration.py`)
- [x] Agent updated with memory support (`trade_matching_agent_strands.py`)
- [x] Configuration files created (`.env.memory`)
- [x] Test script created (`test_memory_integration.py`)
- [x] Documentation complete (4 guides)

## 🔄 Testing & Validation (Do This Now)

### Step 1: Test Memory Connection
```bash
cd deployment/trade_matching
source .env.memory
python test_memory_integration.py
```

**Expected Output:**
```
✓ Memory session manager initialized successfully
✓ Test memory session created successfully
✓ Test decision stored in memory
✓ Retrieved 1 turn(s) from memory
✅ All memory integration tests passed!
```

- [ ] Test passes without errors
- [ ] Memory connection successful
- [ ] Can store test data
- [ ] Can retrieve test data

### Step 2: Verify IAM Permissions

Check agent's IAM role has these permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:GetMemory",
    "bedrock-agentcore:CreateMemorySession",
    "bedrock-agentcore:AddMemoryTurns",
    "bedrock-agentcore:SearchMemory",
    "bedrock-agentcore:GetMemorySession",
    "bedrock-agentcore:ListMemorySessions"
  ],
  "Resource": "arn:aws:bedrock-agentcore:us-east-1:401552979575:memory/trade_matching_agent_mem-SxPFir3bbF"
}
```

- [ ] IAM permissions verified
- [ ] Agent can access memory resource
- [ ] No permission errors in logs

### Step 3: Deploy Agent

```bash
# Option 1: AgentCore Runtime
agentcore launch --config agentcore.yaml

# Option 2: Local testing
python trade_matching_agent_strands.py
```

- [ ] Agent deploys successfully
- [ ] Logs show "AgentCore Memory initialized"
- [ ] No memory initialization errors

### Step 4: Process Test Trade

Run a matching operation and verify memory storage:

```bash
# Invoke agent with test trade
agentcore invoke trade-matching-agent \
  --payload '{"trade_id": "TEST_001", "source_type": "BANK", "correlation_id": "test_corr_001"}'
```

**Check logs for:**
```
INFO - Stored matching decision in memory: trade_id=TEST_001, classification=MATCHED, confidence=92%
```

- [ ] Trade processed successfully
- [ ] Memory storage logged
- [ ] No storage errors

### Step 5: Verify Memory Storage

Query memory to confirm data was stored:

```python
from bedrock_agentcore.memory.session import MemorySessionManager

session_manager = MemorySessionManager(
    memory_id="trade_matching_agent_mem-SxPFir3bbF",
    region_name="us-east-1"
)

session = session_manager.create_memory_session(
    actor_id="trade-matching-agent",
    session_id="verify_session"
)

# Search for test trade
results = session.search_long_term_memories(
    query="TEST_001",
    namespace_prefix="/",
    top_k=5
)

print(f"Found {len(results)} results")
for result in results:
    print(result['content'][:200])
```

- [ ] Can query memory successfully
- [ ] Test trade found in results
- [ ] Data format looks correct

## 📊 Monitoring Setup (Do This Next)

### CloudWatch Alarms

Create alarms for memory health:

```bash
# Memory storage usage alarm
aws cloudwatch put-metric-alarm \
  --alarm-name trade-matching-memory-storage-high \
  --alarm-description "Memory storage usage is high" \
  --metric-name MemoryStorageUsed \
  --namespace AWS/BedrockAgent \
  --statistic Average \
  --period 3600 \
  --evaluation-periods 1 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=MemoryId,Value=trade_matching_agent_mem-SxPFir3bbF \
  --region us-east-1

# Memory query latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name trade-matching-memory-latency-high \
  --alarm-description "Memory query latency is high" \
  --metric-name MemoryQueryLatency \
  --namespace AWS/BedrockAgent \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=MemoryId,Value=trade_matching_agent_mem-SxPFir3bbF \
  --region us-east-1
```

- [ ] Storage usage alarm created
- [ ] Query latency alarm created
- [ ] SNS topic configured for alerts

### Dashboard

Create CloudWatch dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name trade-matching-memory \
  --dashboard-body file://memory_dashboard.json \
  --region us-east-1
```

- [ ] Dashboard created
- [ ] Metrics visible
- [ ] Graphs showing data

## 🎯 Production Readiness (Before Go-Live)

### Performance Testing

- [ ] Process 100 trades and verify memory storage
- [ ] Measure memory query latency (should be <500ms)
- [ ] Check storage growth rate
- [ ] Verify no memory leaks

### Cost Estimation

- [ ] Calculate storage costs ($/GB/month)
- [ ] Estimate query costs ($/1000 queries)
- [ ] Project monthly costs based on volume
- [ ] Set up billing alerts

### Documentation Review

- [ ] Team trained on memory features
- [ ] Runbooks updated with memory troubleshooting
- [ ] Monitoring procedures documented
- [ ] Escalation paths defined

### Backup & Recovery

- [ ] Memory backup strategy defined
- [ ] Recovery procedures tested
- [ ] Data retention policy documented
- [ ] Archive strategy for old data

## 🚀 Go-Live Checklist

### Pre-Launch

- [ ] All tests passing
- [ ] IAM permissions verified
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation complete
- [ ] Team trained

### Launch Day

- [ ] Deploy agent with memory enabled
- [ ] Monitor first 10 trades closely
- [ ] Verify memory storage working
- [ ] Check CloudWatch metrics
- [ ] Review logs for errors
- [ ] Confirm no performance degradation

### Post-Launch (First Week)

- [ ] Daily memory usage review
- [ ] Query performance monitoring
- [ ] Storage growth tracking
- [ ] Cost monitoring
- [ ] Error rate analysis
- [ ] Accuracy measurement baseline

## 📈 Success Metrics

Track these metrics to measure memory effectiveness:

### Week 1
- [ ] 100% of decisions stored successfully
- [ ] Memory query latency <500ms
- [ ] No storage errors
- [ ] Baseline accuracy established

### Month 1
- [ ] Accuracy improvement measured
- [ ] Pattern recognition working
- [ ] Cost within budget
- [ ] No operational issues

### Quarter 1
- [ ] 5%+ accuracy improvement
- [ ] Consistent matching patterns
- [ ] HITL feedback integrated
- [ ] ROI positive

## 🆘 Troubleshooting Quick Reference

### Memory Not Initializing
```bash
# Check memory exists
aws bedrock-agentcore get-memory \
  --memory-id trade_matching_agent_mem-SxPFir3bbF \
  --region us-east-1

# Check IAM permissions
aws iam get-role-policy \
  --role-name <agent-role-name> \
  --policy-name <policy-name>
```

### Storage Failing
```bash
# Check agent logs
grep "Failed to store matching decision" agent.log

# Verify memory status
agentcore memory status trade_matching_agent_mem-SxPFir3bbF
```

### High Costs
```bash
# Check storage usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryStorageUsed \
  --dimensions Name=MemoryId,Value=trade_matching_agent_mem-SxPFir3bbF \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average \
  --region us-east-1
```

## 📞 Support Contacts

- **AWS Support**: For memory resource issues
- **AgentCore Docs**: https://aws.github.io/bedrock-agentcore-starter-toolkit/
- **Team Lead**: For operational issues
- **On-Call**: For production incidents

---

**Current Status**: ✅ Integration Complete - Ready for Testing

**Next Action**: Run `python test_memory_integration.py`
