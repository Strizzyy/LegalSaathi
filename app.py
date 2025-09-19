from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List
import time
import json
import re
from openai import OpenAI
from risk_classifier import RiskClassifier, classify_document_risk, RiskLevel as ClassifierRiskLevel, MockTranslationService, MockVertexAIService
from file_processor import FileProcessor
from document_classifier import DocumentClassifier, DocumentType

app = Flask(__name__)

# Configure file upload settings
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Initialize services including enhanced AI services
file_processor = FileProcessor()
document_classifier = DocumentClassifier()
translation_service = MockTranslationService()
ai_clarification_service = MockVertexAIService()

# Initialize OpenAI client for vLLM server (adapting from integrate.py)
client = OpenAI(
    base_url="http://172.25.0.211:8002/v1",
    api_key="EMPTY",  # No API key needed for local vLLM
    timeout=5.0  # 5 second timeout for faster fallback
)

# Enhanced data models for document analysis results with confidence and categories
@dataclass
class RiskLevel:
    level: str  # "RED", "YELLOW", "GREEN"
    score: float  # 0.0 to 1.0
    reasons: List[str]
    severity: str
    confidence_percentage: int  # 0-100%
    risk_categories: dict  # financial, legal, operational
    low_confidence_warning: bool

@dataclass
class AnalysisResult:
    clause_id: str
    risk_level: RiskLevel
    plain_explanation: str
    legal_implications: List[str]
    recommendations: List[str]

@dataclass
class DocumentAnalysis:
    document_id: str
    analysis_results: List[AnalysisResult]
    overall_risk: RiskLevel
    summary: str
    processing_time: float

# Routes
@app.route('/')
def home():
    """Home page with document input interface"""
    return render_template('index.html')

def validate_document_input(document_text):
    """
    Validate document input according to requirements 1.1, 1.2, 1.3
    Returns tuple (is_valid, error_message)
    """
    if not document_text or not document_text.strip():
        return False, "Please provide a valid rental agreement text."
    
    text = document_text.strip()
    length = len(text)
    
    # Check length restrictions (Requirement 1.3)
    if length < 100:
        return False, "Document text must be at least 100 characters long for meaningful analysis."
    
    if length > 50000:
        return False, "Document text exceeds maximum length of 50,000 characters. Please shorten your document."
    
    # Basic content validation - check for rental agreement keywords (Requirement 1.2)
    legal_keywords = [
        'rent', 'lease', 'tenant', 'landlord', 'property', 'agreement',
        'deposit', 'term', 'month', 'payment', 'premises', 'rental'
    ]
    
    text_lower = text.lower()
    found_keywords = [keyword for keyword in legal_keywords if keyword in text_lower]
    
    if len(found_keywords) < 3:
        return False, "This doesn't appear to be a rental agreement. Please ensure you've pasted the correct legal document."
    
    return True, None

def analyze_rental_agreement_with_llm(document_text: str) -> DocumentAnalysis:
    """
    Analyze rental agreement using enhanced risk classification system with improved error handling
    Requirements: 2.1, 2.2, 4.1, 3.1, 3.2, 3.3, 3.4, 7.2 (Add try-catch blocks for LLM service failures)
    """
    start_time = time.time()
    
    try:
        # Use the new risk classification system with error handling
        risk_analysis = classify_document_risk(document_text)
        
        # Convert to our enhanced data model format with confidence and categories
        overall_risk_data = risk_analysis['overall_risk']
        overall_risk = RiskLevel(
            level=overall_risk_data['level'],
            score=overall_risk_data['score'],
            reasons=[f"Overall document risk: {overall_risk_data['severity']}"],
            severity=overall_risk_data['severity'],
            confidence_percentage=overall_risk_data['confidence_percentage'],
            risk_categories=overall_risk_data['risk_categories'],
            low_confidence_warning=overall_risk_data['low_confidence_warning']
        )
        
        analysis_results = []
        for clause_assessment in risk_analysis['clause_assessments']:
            assessment = clause_assessment['assessment']
            
            # Convert classifier risk level to our enhanced format
            risk_level = RiskLevel(
                level=assessment.level.value,
                score=assessment.score,
                reasons=assessment.reasons,
                severity=assessment.severity,
                confidence_percentage=assessment.confidence_percentage,
                risk_categories=assessment.risk_categories,
                low_confidence_warning=assessment.low_confidence_warning
            )
            
            # Generate enhanced plain language explanation with confidence indicators
            confidence_indicator = ""
            if assessment.low_confidence_warning:
                confidence_indicator = f" (⚠️ Low Confidence: {assessment.confidence_percentage}%)"
            
            if assessment.level == ClassifierRiskLevel.RED:
                explanation = f"🚨 HIGH RISK{confidence_indicator}: This clause contains terms that could be unfair or problematic. {' '.join(assessment.reasons[:2])}"
                implications = ["This clause may put you at a disadvantage", "Consider negotiating or seeking legal advice"]
                recommendations = ["Request modification of this clause", "Consult with a legal professional", "Consider this a deal-breaker"]
            elif assessment.level == ClassifierRiskLevel.YELLOW:
                explanation = f"⚠️ MODERATE CONCERN{confidence_indicator}: This clause has some issues that could be improved. {' '.join(assessment.reasons[:2])}"
                implications = ["This clause could be more tenant-friendly", "May cause issues in certain situations"]
                recommendations = ["Try to negotiate better terms", "Understand the implications fully", "Consider alternatives"]
            else:
                explanation = f"✅ FAIR TERMS{confidence_indicator}: This clause appears to be standard and reasonable. {' '.join(assessment.reasons[:1]) if assessment.reasons else 'No major concerns identified.'}"
                implications = ["This clause follows standard rental practices", "Generally fair to both parties"]
                recommendations = ["This clause is acceptable as written"]
            
            analysis_result = AnalysisResult(
                clause_id=clause_assessment['clause_id'],
                risk_level=risk_level,
                plain_explanation=explanation,
                legal_implications=implications,
                recommendations=recommendations
            )
            analysis_results.append(analysis_result)
        
        # Generate enhanced summary with confidence and category information
        red_clauses = len([c for c in risk_analysis['clause_assessments'] if c['assessment'].level == ClassifierRiskLevel.RED])
        yellow_clauses = len([c for c in risk_analysis['clause_assessments'] if c['assessment'].level == ClassifierRiskLevel.YELLOW])
        
        confidence_note = ""
        if overall_risk_data['low_confidence_warning']:
            confidence_note = f" (Analysis Confidence: {overall_risk_data['confidence_percentage']}% - Consider professional review)"
        
        # Category breakdown
        categories = overall_risk_data['risk_categories']
        high_risk_categories = [cat for cat, score in categories.items() if score > 0.6]
        category_note = f" Primary concerns: {', '.join(high_risk_categories)}" if high_risk_categories else ""
        
        if overall_risk_data['level'] == 'RED':
            summary = f"🚨 HIGH RISK DOCUMENT{confidence_note}: This rental agreement contains {red_clauses} high-risk clauses that need immediate attention.{category_note} We strongly recommend legal review before signing."
        elif overall_risk_data['level'] == 'YELLOW':
            summary = f"⚠️ MODERATE RISK{confidence_note}: This agreement has {yellow_clauses} concerning clauses that could be improved.{category_note} Review the highlighted issues and consider negotiating better terms."
        else:
            summary = f"✅ LOW RISK{confidence_note}: This appears to be a fairly standard rental agreement with reasonable terms.{category_note} Review the details but generally acceptable."
        
        processing_time = time.time() - start_time
        
        return DocumentAnalysis(
            document_id=f"doc_{int(time.time())}",
            analysis_results=analysis_results,
            overall_risk=overall_risk,
            summary=summary,
            processing_time=processing_time
        )
        
    except Exception as e:
        print(f"Error in enhanced risk analysis: {str(e)}")
        # Enhanced error handling with specific error messages
        error_msg = str(e).lower()
        
        if "connection" in error_msg or "timeout" in error_msg:
            print("LLM service connection issue - using fallback analysis")
        elif "api" in error_msg or "key" in error_msg:
            print("LLM service API issue - using fallback analysis")
        elif "memory" in error_msg or "resource" in error_msg:
            print("LLM service resource issue - using fallback analysis")
        else:
            print(f"Unexpected LLM service error: {str(e)} - using fallback analysis")
        
        # Fallback to basic analysis on error
        return create_fallback_analysis(document_text)

def create_fallback_analysis(document_text: str) -> DocumentAnalysis:
    """
    Create a basic fallback analysis when enhanced AI services are unavailable
    Uses keyword-based detection as backup
    """
    try:
        # Try to use at least the keyword-based risk classifier
        classifier = RiskClassifier()
        
        # Simple clause extraction for fallback
        clauses = re.split(r'[.!?]+', document_text)
        clauses = [clause.strip() for clause in clauses if len(clause.strip()) > 20]
        
        analysis_results = []
        risk_scores = []
        
        for i, clause in enumerate(clauses[:5]):  # Limit to 5 clauses for fallback
            # Use only keyword detection (no AI)
            keyword_risk = classifier._detect_keyword_red_flags(clause)
            
            risk_level = RiskLevel(
                level=keyword_risk.level.value,
                score=keyword_risk.score,
                reasons=keyword_risk.reasons,
                severity=keyword_risk.severity,
                confidence_percentage=keyword_risk.confidence_percentage,
                risk_categories=keyword_risk.risk_categories,
                low_confidence_warning=keyword_risk.low_confidence_warning
            )
            
            analysis_result = AnalysisResult(
                clause_id=f"fallback_clause_{i+1}",
                risk_level=risk_level,
                plain_explanation=f"Keyword-based analysis: {keyword_risk.severity} risk detected.",
                legal_implications=["Limited analysis - AI services unavailable"],
                recommendations=["Manual review recommended", "Consider professional legal advice"]
            )
            analysis_results.append(analysis_result)
            risk_scores.append(keyword_risk.score)
        
        # Calculate overall risk
        if risk_scores:
            avg_score = sum(risk_scores) / len(risk_scores)
            max_score = max(risk_scores)
            overall_score = (avg_score * 0.6) + (max_score * 0.4)
        else:
            overall_score = 0.5
        
        if overall_score > 0.7:
            overall_level = "RED"
            severity = "High"
            summary = "⚠️ Potential high-risk terms detected. Full AI analysis unavailable - manual review strongly recommended."
        elif overall_score > 0.4:
            overall_level = "YELLOW"
            severity = "Medium"
            summary = "Some concerning terms detected. Limited analysis available - consider professional review."
        else:
            overall_level = "GREEN"
            severity = "Low"
            summary = "No major red flags detected in basic analysis. Full AI analysis unavailable."
        
        overall_risk = RiskLevel(
            level=overall_level,
            score=overall_score,
            reasons=[f"Fallback analysis completed - {len(analysis_results)} clauses checked"],
            severity=severity,
            confidence_percentage=60,  # Medium confidence for fallback
            risk_categories={'financial': 0.3, 'legal': 0.3, 'operational': 0.3},
            low_confidence_warning=True
        )
        
        classifier.close()
        
        return DocumentAnalysis(
            document_id=f"fallback_{int(time.time())}",
            analysis_results=analysis_results,
            overall_risk=overall_risk,
            summary=summary,
            processing_time=0.2
        )
        
    except Exception as e:
        print(f"Fallback analysis error: {e}")
        
        # Ultimate fallback - very basic analysis
        overall_risk = RiskLevel(
            level="YELLOW",
            score=0.5,
            reasons=["Analysis services unavailable"],
            severity="Medium",
            confidence_percentage=20,
            risk_categories={'financial': 0.5, 'legal': 0.5, 'operational': 0.5},
            low_confidence_warning=True
        )
        
        basic_analysis = AnalysisResult(
            clause_id="basic_fallback",
            risk_level=overall_risk,
            plain_explanation="Analysis services are currently unavailable. Please try again later or consult a legal professional.",
            legal_implications=["Unable to perform automated analysis"],
            recommendations=["Try again later", "Consult with a legal professional", "Review document manually"]
        )
        
        return DocumentAnalysis(
            document_id=f"basic_fallback_{int(time.time())}",
            analysis_results=[basic_analysis],
            overall_risk=overall_risk,
            summary="Analysis services temporarily unavailable. Manual review recommended.",
            processing_time=0.1
        )

@app.route('/analyze', methods=['POST'])
def analyze_document():
    """
    Enhanced document analysis endpoint with file upload support and improved error handling
    Requirements: 7.2 - Implement drag-and-drop file upload with basic validation
    """
    document_text = ""
    file_info = None
    warnings = []
    
    try:
        # Check if file was uploaded
        if 'document_file' in request.files and request.files['document_file'].filename:
            file = request.files['document_file']
            
            # Process uploaded file
            file_result = file_processor.process_uploaded_file(file)
            
            if not file_result.success:
                return render_template('index.html', 
                                     error=file_result.error_message,
                                     document_text=request.form.get('document_text', ''))
            
            document_text = file_result.text_content
            file_info = file_result.file_info
            warnings.extend(file_result.warnings)
            
        else:
            # Use text input from form
            document_text = request.form.get('document_text', '')
        
        # Validate document input
        is_valid, error_message = validate_document_input(document_text)
        
        if not is_valid:
            return render_template('index.html', 
                                 error=error_message, 
                                 document_text=document_text,
                                 file_info=file_info)
        
        # Classify document type
        classification = document_classifier.classify_document(document_text)
        classification_message = document_classifier.get_analysis_message(classification)
        
        # Add classification warning if not a rental agreement
        if classification.document_type != DocumentType.RENTAL_AGREEMENT:
            warnings.append(classification_message)
            if classification.confidence < 0.5:
                warnings.append("Document type unclear - analysis may be limited")
        
        # Perform AI-powered rental agreement analysis with enhanced error handling
        try:
            analysis = analyze_rental_agreement_with_llm(document_text)
            
            # Add file info and warnings to analysis
            if hasattr(analysis, 'file_info'):
                analysis.file_info = file_info
            if hasattr(analysis, 'warnings'):
                analysis.warnings = warnings
            if hasattr(analysis, 'classification'):
                analysis.classification = classification
                
        except ConnectionError as e:
            error_msg = "Unable to connect to AI analysis service. Please try again in a few moments."
            return render_template('index.html', 
                                 error=error_msg, 
                                 document_text=document_text,
                                 file_info=file_info)
        
        except TimeoutError as e:
            error_msg = "Analysis service timed out. Please try again with a shorter document or try again later."
            return render_template('index.html', 
                                 error=error_msg, 
                                 document_text=document_text,
                                 file_info=file_info)
        
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            # Enhanced error handling with user-friendly messages
            error_type = type(e).__name__
            
            if "memory" in str(e).lower() or "resource" in str(e).lower():
                error_msg = "Analysis service is currently overloaded. Please try again in a few minutes."
            elif "api" in str(e).lower() or "key" in str(e).lower():
                error_msg = "Analysis service configuration issue. Using basic analysis instead."
                # Fallback to basic analysis
                analysis = create_fallback_analysis(document_text)
            else:
                error_msg = "An unexpected error occurred during analysis. Using basic analysis instead."
                # Fallback to basic analysis
                analysis = create_fallback_analysis(document_text)
            
            # If we couldn't create fallback analysis, show error
            if 'analysis' not in locals():
                return render_template('index.html', 
                                     error=error_msg, 
                                     document_text=document_text,
                                     file_info=file_info)
        
        return render_template('results.html', 
                             analysis=analysis, 
                             file_info=file_info,
                             warnings=warnings,
                             classification=classification,
                             translation_service=translation_service,
                             ai_clarification_service=ai_clarification_service)
    
    except Exception as e:
        # Catch-all error handler
        print(f"Unexpected error in analyze_document: {str(e)}")
        error_msg = "An unexpected error occurred. Please try again or contact support if the problem persists."
        return render_template('index.html', 
                             error=error_msg, 
                             document_text=request.form.get('document_text', ''))

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """
    API endpoint for text translation using mock Google Translate service
    Requirements: Add mock Google Translate API integration for multilingual support
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_language = data.get('target_language', 'es')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        result = translation_service.translate_text(text, target_language)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clarify', methods=['POST'])
def ask_clarification():
    """
    API endpoint for AI clarification using mock Vertex AI service
    Requirements: Add mock Vertex AI Generative AI integration for conversational clarification
    """
    try:
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', {})
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'})
        
        result = ai_clarification_service.ask_clarification(question, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/conversation-summary')
def get_conversation_summary():
    """Get conversation summary from AI clarification service"""
    try:
        summary = ai_clarification_service.get_conversation_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)