# Requirements & Amendments for AI OTC Trade Reconciliation Solution

## 1. Technical Environment Constraints

### Critical Blocker:
- **Bedrock Unavailability**: Current solution relies on AWS Bedrock, which is not available in FAB's UAE environment and lacks GSO team approval, so change it to use Sagemaker AI Jumpstart models or Huggingface models that can be used in me-central-1 region 
- **Required Change**: change it to use Sagemaker AI Jumpstart models or Huggingface models that can be used in me-central-1 region 

### Approved Alternative:
- **Sagemaker with GPT**: Already approved in UAE region and can be used as an alternative implementation
- **Action Required**: Specify exact model configuration and Sagemaker requirements

## 2. Solution Architecture Requirements

### Core Functionality:
- **Contextual Understanding**: Solution must leverage LLMs to understand trade context rather than relying on hardcoded attribute matching
- **Intelligent Field Recognition**: System should automatically identify required fields for comparison based on transaction type
- **Semantic Matching**: Must recognize semantically equivalent terms (e.g., "settlement date" vs. "maturity date")
- **Format Flexibility**: Handle different formatting conventions and naming variations, especially for commodities trading

### Implementation Balance:
- Find middle ground between completely flexible LLM usage and deterministic attribute matching
- Balance between flexibility and producing consistent, deterministic output

## 3. Output Format Requirements

Solution must generate structured output containing:
1. Clear listing of trade attributes extracted from both documents
2. Matching status for each attribute (matched/mismatched)
3. Detailed reasoning for any mismatches
4. Overall matching percentage or score
5. Clear conclusion with recommendation (matched/unmatched)

## 4. Performance & Scalability

- Current approach of matching "everything with everything" won't scale for large volumes
- Solution must be optimized for performance with potentially large numbers of PDFs (concern expressed about handling 100,000+ PDFs)

## 5. Extension Roadmap

Solution design should accommodate future expansion to:
1. **Pre-validation reconciliation**: Compare trading platform data with back-office system data
2. **Multiple input formats**: Support for emails, electronic trading data, exchange confirmations, and SWIFT messages

## 6. Deployment Options

- **Interim Solution**: Consider developing a temporary standalone solution while integration issues are resolved
- **VDI Compatibility**: Verify compatibility with FAB's VDI environment or laptop deployment using Stunnel/UV

## 7. Financial Domain Expertise

- Solution must demonstrate understanding of OTC trade terminology, especially for commodities where naming conventions vary widely
- Handle non-standardized market terminology that differs between trading parties

## 8. User Experience

- Output must be easily understandable by operations team members
- Provide clear explanations that support human decision-making

## Action Items for Development Team

1. **Immediate**: Design alternative implementation using Sagemaker with GPT
2. **Near-term**: Modify solution architecture to work with approved services in FAB's environment
3. **Ongoing**: Refine approach to balance between flexibility and deterministic output
4. **Design**: Ensure architecture supports future expansion to additional reconciliation types and formats