# LLM Integration for Rental Agreement Analysis

## Overview

This implementation adapts the existing vLLM setup to provide AI-powered rental agreement analysis. The system uses a local vLLM server running Llama-3.1-8B-Instruct model for intelligent document analysis.

## Features Implemented

### 1. vLLM Integration
- **Server Configuration**: Connects to vLLM server at `http://172.25.0.211:8002/v1`
- **Model**: Uses `meta-llama/Llama-3.1-8B-Instruct` for analysis
- **Timeout Handling**: 10-second timeout to prevent hanging
- **Fallback System**: Graceful degradation when LLM is unavailable

### 2. Rental Agreement Analysis Prompt
- **Structured Analysis**: JSON-formatted output for consistent parsing
- **Risk Assessment**: Three-tier system (RED/YELLOW/GREEN)
- **Clause-by-Clause Analysis**: Detailed breakdown of rental terms
- **Plain Language Explanations**: Converts legal jargon to everyday language

### 3. Risk Categories Analyzed
- Excessive security deposits
- Unfair termination clauses
- Maintenance responsibility shifts
- Rent increase limitations
- Privacy and entry rights
- Subletting restrictions
- Pet policies
- Late fee structures

## Usage

### Running the Application
```bash
# Install dependencies
uv sync

# Run the Flask application
python app.py

# Test the LLM integration
python test_llm_integration.py
```

### API Integration
The LLM analysis is automatically triggered when users submit rental agreements through the web interface at `/analyze`.

## Configuration

### vLLM Server Setup
The system expects a vLLM server running at:
- **URL**: `http://172.25.0.211:8002/v1`
- **Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **API Format**: OpenAI-compatible

### Fallback Behavior
When the vLLM server is unavailable:
1. System automatically falls back to keyword-based analysis
2. Provides basic risk assessment using predefined patterns
3. Maintains user experience with reduced functionality
4. Displays clear messaging about limited analysis

## Sample Analysis Output

```json
{
    "overall_risk": {
        "level": "RED",
        "score": 0.8,
        "reasons": ["Non-refundable security deposit", "Unfair termination clause"],
        "severity": "High"
    },
    "clause_analyses": [
        {
            "clause_text": "Tenant must pay a non-refundable security deposit",
            "clause_type": "security_deposit",
            "risk_level": "RED",
            "plain_explanation": "This clause means you cannot get your security deposit back, which is unfair and potentially illegal in many jurisdictions.",
            "legal_implications": ["Violates tenant protection laws", "Unfair financial burden"],
            "recommendations": ["Request refundable deposit", "Check local tenant laws"]
        }
    ],
    "summary": "This rental agreement contains several high-risk clauses that heavily favor the landlord."
}
```

## Requirements Satisfied

- **Requirement 2.1**: ✅ AI analyzes documents against fair rental practices
- **Requirement 2.2**: ✅ Categorizes clauses by risk level with detailed explanations  
- **Requirement 4.1**: ✅ Provides plain-language explanations of legal terms

## Testing

The `test_llm_integration.py` script verifies:
- LLM server connectivity
- Prompt template functionality
- Fallback analysis capability
- JSON response parsing
- Risk assessment accuracy

## Next Steps

1. **vLLM Server Setup**: Ensure the vLLM server is running for full functionality
2. **Prompt Optimization**: Fine-tune prompts based on real rental agreement testing
3. **Knowledge Base Integration**: Add legal standards database for enhanced analysis
4. **Performance Monitoring**: Track analysis accuracy and response times