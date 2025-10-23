# LegalSaathi Enhancement Implementation Plan

- [x] 1. Migrate AI Service from Groq to Gemini API with Minimal Vertex AI Integration


















  - Replace Groq client with Google Gemini API as primary AI service (90% usage) in services/ai_service.py
  - Add minimal Vertex AI integration only for document embeddings, comparison features and semantic searching
  - Implement comprehensive caching system to avoid repeat API calls and protect quotas
  - Add quota monitoring, usage tracking, and automatic fallbacks to prevent API exhaustion
  - use the test_ai_service_migration.py script to examine the changes and fix error and issues 
  - Create robust error handling and intelligent fallback mechanisms for both services
  - Add request/response logging and debugging capabilities for troubleshooting
  - use uv sync for package synv not pip 
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement Experience Level Personalization System








  - Create PersonalizationEngine class for adaptive response generation
  - Enhance AI service to generate beginner/intermediate/expert level responses
  - Fix frontend experience level handling to properly influence AI responses
  - Ensure experience level context is maintained throughout user sessions
  -document summary feature is not woking properly also fix that it does not have the context of response given by llm 
  -in clause view summary has similar issue it is not working properly does not have the context of the clause for llm to process it 
  - use uv sync for package sync not pip 
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Build Functional Document Comparison with Advanced Analysis














  - Implement working document comparison service using minimal Vertex AI embeddings for semantic analysis
  - Create side-by-side comparison interface with visual difference highlighting
  - Add risk differential analysis and change impact assessment using cached embeddings
  - Build export functionality for comparison reports (PDF/Word)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Enhance Natural Language AI with Actionable Insights





  - Replace basic metrics display with advanced legal insights engine
  - Implement conflict detection, bias analysis, and negotiation point identification
  - Add entity relationship mapping and compliance checking features
  - Create interactive insights interface for exploring document intelligence
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Fix Document Summary and Clause Summary Context Issues





  - Fix generic AI responses like "This clause creates financial disadvantages for you. Main issues: The security deposit amount is high and could be restricted by local laws" - these are too vague and unhelpful
  - Improve AI service to generate detailed, specific, actionable responses with concrete examples, exact negotiation language, and specific dollar amounts/timeframes
  - Fix frontend context collection to pass complete document analysis results including clause texts, risk scores, confidence levels, and full analysis data
  - Ensure document summary receives comprehensive context: document type, overall risk, clause-by-clause data, risk breakdown, confidence levels, and analysis metadata
  - Fix clause summary to pass complete clause context: full clause text, risk score, severity, confidence percentage, existing analysis, implications, and recommendations
  - Implement strict response quality validation to reject generic responses and force AI to provide specific, detailed guidance
  - Fix incorrect timestamp display showing wrong generation dates in summary components
  - Enhance AI prompts to demand specific examples like "Change 'at landlord's sole discretion' to 'for documented damages exceeding normal wear and tear'"
  - Add retry logic with enhanced prompts when AI gives generic responses to ensure high-quality, actionable summaries
  - Prevent fallback to keyword-based responses - always use Gemini/Groq APIs with proper context validation
  - Test both document and clause summaries to ensure they provide specific, actionable, contextual responses instead of generic advice



  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 6. Fix Critical Document Analysis and Summary Issues








  - **Fix clause extraction to capture ALL clauses** - Currently only extracting 2 clauses from documents with 15+ clauses, implement proper clause parsing to extract every numbered clause
  - **Fix Document Summary context issues** - Summary showing generic responses with no document context, implement proper context passing with full document analysis data
  - **Fix Clause Summary context issues** - Individual clause summaries have no context about the specific clause being analyzed, pass complete clause text and analysis data
  - **Fix API endpoint errors** - Document summary refresh failing with 422 errors from /api/ai/clarify endpoint, implement proper error handling and fallback mechanisms
  - **Remove hardcoded timestamps** - Summary showing old dates (9/20/2025) instead of current date, use real-time timestamp generation
  - **Improve clause parsing algorithm** - Implement robust regex patterns to identify all numbered clauses (1., 2., 3., etc.) and extract complete clause text including sub-points
  - **Fix AI service response quality** - Eliminate generic responses like "This clause creates financial disadvantages" and force specific, actionable advice with concrete examples
  - **Implement proper context validation** - Ensure AI service receives complete clause text, risk scores, confidence levels, and analysis metadata before generating summaries
  - **Fix frontend error handling** - Handle API failures gracefully and provide meaningful error messages instead of console errors
  - **Test with multi-clause documents** - Verify that documents with 10+ clauses are properly parsed and all clauses are extracted and analyzed
  - **Validate summary quality** - Ensure both document and clause summaries provide specific, contextual, actionable guidance instead of generic advice
  - **Improve summary formatting and presentation** - Replace markdown formatting (**text**) with proper styled components and improve visual presentation with better typography and spacing
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_