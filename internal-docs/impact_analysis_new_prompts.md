# Impact Analysis: New Prompts Integration

## Executive Summary
The new prompts represent a significant enhancement to the current system, providing more detailed specifications for OTC derivatives reconciliation. They introduce structured workflows, explicit success criteria, and comprehensive field mappings aligned with ISDA standards.

## Key Findings

### 1. PDF Adapter Agent
**Current State:** Basic text extraction with minimal UTI focus
**New Prompt Enhancements:**
- ✅ **UTI Extraction Priority**: Explicit patterns and validation rules for UTI (critical for 100% match certainty)
- ✅ **Source Detection Logic**: Clear criteria for BANK vs COUNTERPARTY classification
- ✅ **Canonical Output Format**: Structured JSON schema with metadata
- ✅ **Error Handling**: Comprehensive scenarios for PDF corruption, ambiguous sources

**Impact:**
- **HIGH** - Requires adding UTI-specific extraction logic
- **Code Changes Needed:**
  - Add UTI pattern matching (lines 36-55 in new prompt)
  - Implement source detection rules (lines 16-31)
  - Enhance canonical output structure (line 77)

### 2. Trade Extraction Agent
**Current State:** LLM-driven extraction with basic field mapping
**New Prompt Enhancements:**
- ✅ **Critical Fields Definition**: Comprehensive list of required fields by product type
- ✅ **Product-Specific Fields**: Detailed mappings for Commodity/IRS/FX/CCS products
- ✅ **CDM Integration**: ISDA Common Domain Model field mappings
- ✅ **Field Label Variations**: Common synonyms for field recognition
- ✅ **Confidence Scoring**: HIGH/MEDIUM/LOW classification logic

**Impact:**
- **VERY HIGH** - Most significant changes required
- **Code Changes Needed:**
  - Expand field extraction to cover all product types (lines 35-66)
  - Implement normalization rules (lines 72-96)
  - Add CDM structure mapping (lines 166-178)
  - Integrate confidence scoring system (lines 111-120)

### 3. Trade Matching Agent
**Current State:** Basic attribute matching with confidence scoring
**New Prompt Enhancements:**
- ✅ **UTI Priority Matching**: UTI-first strategy (100% certainty when matched)
- ✅ **Weighted Attribute Scoring**: Detailed scoring framework with tolerances
- ✅ **Classification Framework**: MATCHED/PROBABLEMATCH/REVIEWREQUIRED/BREAK tiers
- ✅ **Special Scenarios**: One-to-many, date boundaries, currency conversion handling

**Impact:**
- **MEDIUM** - Core logic exists, needs refinement
- **Code Changes Needed:**
  - Implement UTI-first matching priority (lines 11-18)
  - Refine tolerance levels per attribute (lines 35-54)
  - Add classification tiers (lines 59-63)
  - Handle special scenarios (lines 85-101)

### 4. Exception Management Agent
**Current State:** Basic triage with severity analysis
**New Prompt Enhancements:**
- ✅ **SLA Framework**: Time-based severity levels (CRITICAL: 2hr, HIGH: 4hr, etc.)
- ✅ **Routing Logic**: Detailed team assignments (AUTO_RESOLVE, OPS_DESK, etc.)
- ✅ **Pattern Recognition**: Historical exception analysis for auto-resolution
- ✅ **Recommendations Generation**: Structured approach to resolution guidance
- ✅ **Escalation Triggers**: Specific conditions for escalation

**Impact:**
- **HIGH** - Significant enhancement to current capabilities
- **Code Changes Needed:**
  - Implement SLA tracking (lines 16-24)
  - Add routing decision matrix (lines 26-36)
  - Develop pattern recognition queries (lines 52-61)
  - Create recommendation templates (lines 63-72)

## Integration Points & Dependencies

### 1. Database Schema Updates
- **BankTradeData/CounterpartyTradeData Tables:**
  - Add `uti` field as primary matching key
  - Add product-specific fields for all derivatives types
  - Add `cdm_structure` JSONB field for CDM compatibility
  - Add `confidence_score` and `confidence_classification` fields

### 2. S3 Structure Changes
- **Canonical Output Format:**
  - Standardized JSON structure with metadata
  - Separate folders for BANK/COUNTERPARTY documents
  - UTI-based indexing for quick retrieval

### 3. Inter-Agent Communication
- **PDF Adapter → Trade Extraction:**
  - Must pass UTI and source_type in canonical output
  - Include extraction_quality metrics

- **Trade Extraction → Trade Matching:**
  - Provide confidence scores with extracted data
  - Include CDM structure when available

- **All Agents → Exception Management:**
  - Standardized exception format with severity indicators
  - Include historical context for pattern matching

### 4. New Environment Variables
```python
# UTI Configuration
UTI_VALIDATION_ENABLED = True
UTI_MAX_LENGTH = 52
UTI_PATTERN = r'^[A-Za-z0-9]{1,52}$'

# SLA Configuration
SLA_CRITICAL_HOURS = 2
SLA_HIGH_HOURS = 4
SLA_MEDIUM_HOURS = 8
SLA_LOW_HOURS = 24

# CDM Integration
CDM_MAPPING_ENABLED = True
CDM_VERSION = "2.0"

# Pattern Recognition
PATTERN_MATCH_THRESHOLD = 0.85
AUTO_RESOLVE_CONFIDENCE = 0.95
```

## Implementation Recommendations

### Phase 1: Core Enhancements (Week 1-2)
1. **Update System Prompts**: Replace current prompts with new versions
2. **Add UTI Support**: Implement UTI extraction and matching logic
3. **Expand Field Mappings**: Add all product-specific fields

### Phase 2: Advanced Features (Week 3-4)
1. **CDM Integration**: Implement ISDA CDM field mappings
2. **Pattern Recognition**: Build historical exception analysis
3. **SLA Tracking**: Implement time-based monitoring

### Phase 3: Testing & Optimization (Week 5-6)
1. **End-to-End Testing**: Validate all agent interactions
2. **Performance Tuning**: Optimize for <30s processing
3. **Accuracy Validation**: Ensure >95% field extraction accuracy

## Risk Assessment

### High Risk Items
1. **Data Migration**: Existing trades lack UTI fields
   - **Mitigation**: Implement backward compatibility mode

2. **Performance Impact**: Expanded field extraction may slow processing
   - **Mitigation**: Implement parallel processing for large documents

3. **Integration Complexity**: Multiple agents need synchronized updates
   - **Mitigation**: Deploy in stages with feature flags

### Medium Risk Items
1. **CDM Compatibility**: Not all counterparties use CDM standards
   - **Mitigation**: Make CDM optional with fallback to legacy format

2. **SLA Compliance**: Meeting aggressive time targets
   - **Mitigation**: Implement priority queuing and auto-escalation

## Success Metrics

### Immediate Goals
- ✅ UTI extraction accuracy: >95%
- ✅ Trade matching confidence: >90%
- ✅ Processing time: <30 seconds per document
- ✅ SLA compliance: >90% within target

### Long-term Goals
- ✅ Auto-resolution rate: >30% for LOW severity
- ✅ False positive rate: <2%
- ✅ CDM adoption: >50% of trades
- ✅ Pattern recognition accuracy: >85%

## Conclusion

The new prompts provide a comprehensive framework for enhancing the OTC derivatives reconciliation system. While implementation requires significant updates across all agents, the improvements in accuracy, speed, and automation justify the investment. The phased approach minimizes risk while delivering incremental value.

**Recommendation**: Proceed with implementation starting with Phase 1 (Core Enhancements), focusing on UTI support and expanded field mappings as these provide immediate value with minimal disruption.