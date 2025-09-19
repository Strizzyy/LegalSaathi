from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List, Dict, Any
import time
import json
import re
from openai import OpenAI
from risk_classifier import RiskClassifier, classify_document_risk, RiskLevel as ClassifierRiskLevel, UserExpertiseDetector, EnhancedRiskCategories
from google_translate_service import GoogleTranslateService
from file_processor import FileProcessor
from document_classifier import DocumentClassifier, DocumentType

app = Flask(__name__)

# Configure file upload settings
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Initialize services including enhanced AI services
file_processor = FileProcessor()
document_classifier = DocumentClassifier()
translation_service = GoogleTranslateService()
expertise_detector = UserExpertiseDetector()
risk_categories = EnhancedRiskCategories()

# Initialize OpenAI client for vLLM server (adapting from integrate.py)
client = OpenAI(
    base_url="http://172.25.0.211:8002/v1",
    api_key="EMPTY",  # No API key needed for local vLLM
    timeout=5.0  # 5 second timeout for faster fallback
)

# Real AI clarification service using OpenAI client
class RealAIService:
    """Real AI service for document clarification using vLLM/OpenAI"""
    
    def __init__(self, client):
        self.client = client
        self.conversation_history = []
    
    def ask_clarification(self, question: str, context: Dict = None) -> Dict[str, Any]:
        """Real AI-powered conversational clarification"""
        try:
            # Build context from document analysis if available
            context_text = ""
            if context:
                risk_level = context.get('risk_level', 'unknown')
                summary = context.get('summary', '')
                context_text = f"Document Risk Level: {risk_level}\nDocument Summary: {summary}\n\n"
            
            # Create prompt for AI clarification
            prompt = f"""You are a legal document advisor helping users understand their legal documents. 
            
{context_text}User Question: {question}

Please provide a clear, helpful explanation that:
1. Directly answers the user's question
2. Uses simple, non-legal language when possible
3. Provides practical advice if relevant
4. Mentions if they should consult a lawyer for complex issues

Keep your response concise but informative."""

            # Make API call to vLLM server
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3.1-8B-Instruct",
                messages=[
                    {"role": "system", "content": "You are a helpful legal document advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Store in conversation history
            self.conversation_history.append({
                'question': question,
                'response': ai_response,
                'timestamp': time.time()
            })
            
            return {
                'success': True,
                'response': ai_response,
                'conversation_id': len(self.conversation_history)
            }
            
        except Exception as e:
            print(f"AI clarification error: {e}")
            # Fallback to basic response
            return {
                'success': True,
                'response': f"I understand you're asking about your legal document. While I'm having trouble accessing my full AI capabilities right now, I'd recommend reviewing the specific clause you're concerned about and considering consultation with a legal professional if you have serious concerns.",
                'fallback': True
            }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation history"""
        return {
            'success': True,
            'total_questions': len(self.conversation_history),
            'recent_questions': [item['question'] for item in self.conversation_history[-5:]]
        }

# Initialize AI clarification service after class definition
ai_clarification_service = RealAIService(client)

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
    Validate document input for universal legal document analysis
    Returns tuple (is_valid, error_message)
    """
    if not document_text or not document_text.strip():
        return False, "Please provide a valid legal document text."
    
    text = document_text.strip()
    length = len(text)
    
    # Check length restrictions
    if length < 100:
        return False, "Document text must be at least 100 characters long for meaningful analysis."
    
    if length > 50000:
        return False, "Document text exceeds maximum length of 50,000 characters. Please shorten your document."
    
    # Basic content validation - check for general legal document keywords
    legal_keywords = [
        'agreement', 'contract', 'party', 'parties', 'terms', 'conditions',
        'shall', 'hereby', 'whereas', 'therefore', 'obligations', 'rights',
        'liability', 'breach', 'termination', 'effective', 'binding', 'legal'
    ]
    
    text_lower = text.lower()
    found_keywords = [keyword for keyword in legal_keywords if keyword in text_lower]
    
    if len(found_keywords) < 2:
        return False, "This doesn't appear to be a legal document. Please ensure you've pasted the correct document text."
    
    return True, None

def _get_document_context(document_type: DocumentType) -> Dict[str, str]:
    """Get context-specific terms for different document types"""
    contexts = {
        DocumentType.RENTAL_AGREEMENT: {
            'party_disadvantage': 'tenant disadvantage',
            'other_party': 'landlord',
            'protection_laws': 'tenant protection statutes',
            'legal_area': 'rental/housing'
        },
        DocumentType.EMPLOYMENT_CONTRACT: {
            'party_disadvantage': 'employee disadvantage',
            'other_party': 'employer',
            'protection_laws': 'employment protection laws',
            'legal_area': 'employment'
        },
        DocumentType.NDA: {
            'party_disadvantage': 'receiving party disadvantage',
            'other_party': 'disclosing party',
            'protection_laws': 'confidentiality regulations',
            'legal_area': 'intellectual property'
        },
        DocumentType.LOAN_AGREEMENT: {
            'party_disadvantage': 'borrower disadvantage',
            'other_party': 'lender',
            'protection_laws': 'consumer lending laws',
            'legal_area': 'financial/lending'
        },
        DocumentType.PARTNERSHIP_AGREEMENT: {
            'party_disadvantage': 'partner disadvantage',
            'other_party': 'other partners',
            'protection_laws': 'partnership regulations',
            'legal_area': 'business/corporate'
        }
    }
    
    return contexts.get(document_type, {
        'party_disadvantage': 'party disadvantage',
        'other_party': 'other party',
        'protection_laws': 'applicable regulations',
        'legal_area': 'relevant legal'
    })

def analyze_legal_document_with_llm(document_text: str, document_type: DocumentType, expertise_profile: Dict = None) -> DocumentAnalysis:
    """
    Analyze legal document using enhanced risk classification system with improved error handling
    Supports multiple document types: rental, employment, NDA, terms of service, loans, partnerships
    Requirements: 2.1, 2.2, 4.1, 3.1, 3.2, 3.3, 3.4, 7.2 (Add try-catch blocks for LLM service failures)
    """
    start_time = time.time()
    
    try:
        # Use the new risk classification system with error handling
        risk_analysis = classify_document_risk(document_text, document_type)
        
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
            
            # Generate adaptive explanations based on user expertise
            confidence_indicator = ""
            if assessment.low_confidence_warning:
                confidence_indicator = f" (⚠️ Low Confidence: {assessment.confidence_percentage}%)"
            
            # Adapt explanation style based on expertise level and document type
            doc_context = _get_document_context(document_type)
            
            if expertise_profile and expertise_profile['level'] == 'expert':
                # Technical explanations for experts
                if assessment.level == ClassifierRiskLevel.RED:
                    explanation = f"🚨 HIGH RISK{confidence_indicator}: Legal analysis indicates significant {doc_context['party_disadvantage']}. Risk categories: {', '.join([k for k, v in assessment.risk_categories.items() if v > 0.6])}. {' '.join(assessment.reasons[:2])}"
                    implications = [f"Potential legal liability exposure", f"Contractual imbalance favoring {doc_context['other_party']}", f"May violate {doc_context['protection_laws']}"]
                    recommendations = ["Seek legal counsel for clause modification", f"Review relevant {doc_context['legal_area']} laws", "Consider contract renegotiation or withdrawal"]
                elif assessment.level == ClassifierRiskLevel.YELLOW:
                    explanation = f"⚠️ MODERATE RISK{confidence_indicator}: Analysis shows suboptimal terms with negotiation potential. {' '.join(assessment.reasons[:2])}"
                    implications = ["Terms deviate from market standards", f"Potential for improved {doc_context['party_disadvantage'].split()[0]} protections"]
                    recommendations = ["Negotiate more balanced terms", f"Reference {doc_context['legal_area']} market standards", "Document any agreed modifications"]
                else:
                    explanation = f"✅ ACCEPTABLE TERMS{confidence_indicator}: Clause aligns with standard {doc_context['legal_area']} practices. {' '.join(assessment.reasons[:1]) if assessment.reasons else 'No significant legal concerns identified.'}"
                    implications = ["Terms within acceptable legal parameters", "Standard market practice"]
                    recommendations = ["Terms are legally sound as written"]
            
            elif expertise_profile and expertise_profile['level'] == 'intermediate':
                # Balanced explanations for intermediate users
                if assessment.level == ClassifierRiskLevel.RED:
                    explanation = f"🚨 HIGH RISK{confidence_indicator}: This clause is unfavorable and should be addressed. Main concerns: {', '.join(assessment.reasons[:2])}"
                    implications = ["This puts you at a significant disadvantage", "Could lead to financial or legal problems", f"Not typical in fair {doc_context['legal_area']} agreements"]
                    recommendations = ["Negotiate to change this clause", "Get legal advice before signing", f"Consider this a red flag for the {doc_context['other_party']}"]
                elif assessment.level == ClassifierRiskLevel.YELLOW:
                    explanation = f"⚠️ MODERATE CONCERN{confidence_indicator}: This clause could be more balanced. Issues: {' '.join(assessment.reasons[:2])}"
                    implications = ["Terms are somewhat one-sided", f"May cause issues during the {doc_context['legal_area']} relationship", "Room for improvement through negotiation"]
                    recommendations = ["Try to negotiate better terms", "Understand what you're agreeing to", f"Compare with other {doc_context['legal_area']} options"]
                else:
                    explanation = f"✅ FAIR TERMS{confidence_indicator}: This appears to be a reasonable and standard clause. {' '.join(assessment.reasons[:1]) if assessment.reasons else 'No major concerns identified.'}"
                    implications = ["Terms are balanced and fair", f"Follows standard {doc_context['legal_area']} practices"]
                    recommendations = ["This clause is acceptable"]
            
            else:
                # Simple explanations for beginners (default)
                if assessment.level == ClassifierRiskLevel.RED:
                    explanation = f"🚨 DANGER{confidence_indicator}: This part of the contract is bad for you! It means: {' '.join(assessment.reasons[:1])}"
                    implications = ["This could cost you money or cause problems", "You might lose important rights", f"This is not fair in {doc_context['legal_area']} agreements"]
                    recommendations = [f"Ask the {doc_context['other_party']} to change this", f"Get help from someone who knows about {doc_context['legal_area']}", "Don't sign if they won't change it"]
                elif assessment.level == ClassifierRiskLevel.YELLOW:
                    explanation = f"⚠️ BE CAREFUL{confidence_indicator}: This part could be better for you. Problem: {' '.join(assessment.reasons[:1])}"
                    implications = ["This might cause problems later", "It's not the worst, but not great either"]
                    recommendations = ["Ask if this can be changed", "Make sure you understand what this means", "Think about whether you're okay with this"]
                else:
                    explanation = f"✅ LOOKS GOOD{confidence_indicator}: This part seems fair and normal. {' '.join(assessment.reasons[:1]) if assessment.reasons else 'Nothing to worry about here.'}"
                    implications = [f"This is typical for {doc_context['legal_area']} contracts", f"This part protects both parties involved"]
                    recommendations = ["This part is fine to agree to"]
            
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
        
        doc_type_name = document_type.value.replace('_', ' ').title() if document_type != DocumentType.UNKNOWN else "legal document"
        
        if overall_risk_data['level'] == 'RED':
            summary = f"🚨 HIGH RISK DOCUMENT{confidence_note}: This {doc_type_name.lower()} contains {red_clauses} high-risk clauses that need immediate attention.{category_note} We strongly recommend legal review before signing."
        elif overall_risk_data['level'] == 'YELLOW':
            summary = f"⚠️ MODERATE RISK{confidence_note}: This {doc_type_name.lower()} has {yellow_clauses} concerning clauses that could be improved.{category_note} Review the highlighted issues and consider negotiating better terms."
        else:
            summary = f"✅ LOW RISK{confidence_note}: This appears to be a fairly standard {doc_type_name.lower()} with reasonable terms.{category_note} Review the details but generally acceptable."
        
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
        
        # Add classification info for all document types
        if classification.confidence > 0.7:
            warnings.append(classification_message)
        elif classification.confidence > 0.3:
            warnings.append(classification_message)
            warnings.append("Document type detection has moderate confidence - analysis may vary")
        else:
            warnings.append("Document type unclear - using general legal document analysis")
        
        # Detect user expertise level for adaptive explanations
        user_questions = request.form.get('user_questions', '')
        expertise_level = request.form.get('expertise_level', 'beginner')
        
        # Use form selection or detect from questions
        if expertise_level in ['beginner', 'intermediate', 'expert']:
            expertise_profile = expertise_detector._get_expertise_profile(expertise_level)
        else:
            expertise_profile = expertise_detector.detect_expertise(user_questions, 'medium')
        
        # Perform AI-powered legal document analysis with enhanced error handling
        try:
            analysis = analyze_legal_document_with_llm(document_text, classification.document_type, expertise_profile)
            
            # Add enhanced risk category analysis
            category_analysis = risk_categories.analyze_risk_categories(document_text)
            severity_indicators = risk_categories.get_severity_indicators(category_analysis)
            
            # Add file info and warnings to analysis
            if hasattr(analysis, 'file_info'):
                analysis.file_info = file_info
            if hasattr(analysis, 'warnings'):
                analysis.warnings = warnings
            if hasattr(analysis, 'classification'):
                analysis.classification = classification
            if hasattr(analysis, 'expertise_profile'):
                analysis.expertise_profile = expertise_profile
            if hasattr(analysis, 'category_analysis'):
                analysis.category_analysis = category_analysis
            if hasattr(analysis, 'severity_indicators'):
                analysis.severity_indicators = severity_indicators
                
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
    API endpoint for text translation using Google Translate service
    Requirements: Integrate Google Translate API using provided key for English/Hindi translation
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_language = data.get('target_language', 'hi')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        result = translation_service.translate_text(text, target_language)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translate-assessment', methods=['POST'])
def translate_risk_assessment():
    """
    API endpoint for translating entire risk assessment results
    """
    try:
        data = request.get_json()
        assessment = data.get('assessment', {})
        target_language = data.get('target_language', 'hi')
        
        if not assessment:
            return jsonify({'success': False, 'error': 'No assessment provided'})
        
        result = translation_service.translate_risk_assessment(assessment, target_language)
        return jsonify({'success': True, 'translated_assessment': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clarify', methods=['POST'])
def ask_clarification():
    """
    API endpoint for AI clarification using real vLLM/OpenAI service
    Requirements: Real AI integration for conversational clarification
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