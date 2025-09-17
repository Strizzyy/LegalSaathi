from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List
import time
import json
import re
from openai import OpenAI
from risk_classifier import RiskClassifier, classify_document_risk, RiskLevel as ClassifierRiskLevel

app = Flask(__name__)

# Initialize OpenAI client for vLLM server (adapting from integrate.py)
client = OpenAI(
    base_url="http://172.25.0.211:8002/v1",
    api_key="EMPTY",  # No API key needed for local vLLM
    timeout=5.0  # 5 second timeout for faster fallback
)

# Simple data models for document analysis results
@dataclass
class RiskLevel:
    level: str  # "RED", "YELLOW", "GREEN"
    score: float  # 0.0 to 1.0
    reasons: List[str]
    severity: str

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
    Analyze rental agreement using enhanced risk classification system
    Requirements: 2.1, 2.2, 4.1, 3.1, 3.2, 3.3, 3.4
    """
    start_time = time.time()
    
    try:
        # Use the new risk classification system
        risk_analysis = classify_document_risk(document_text)
        
        # Convert to our data model format
        overall_risk_data = risk_analysis['overall_risk']
        overall_risk = RiskLevel(
            level=overall_risk_data['level'],
            score=overall_risk_data['score'],
            reasons=[f"Overall document risk: {overall_risk_data['severity']}"],
            severity=overall_risk_data['severity']
        )
        
        analysis_results = []
        for clause_assessment in risk_analysis['clause_assessments']:
            assessment = clause_assessment['assessment']
            
            # Convert classifier risk level to our format
            risk_level = RiskLevel(
                level=assessment.level.value,
                score=assessment.score,
                reasons=assessment.reasons,
                severity=assessment.severity
            )
            
            # Generate plain language explanation based on risk level
            if assessment.level == ClassifierRiskLevel.RED:
                explanation = f"⚠️ HIGH RISK: This clause contains terms that could be unfair or problematic. {' '.join(assessment.reasons[:2])}"
                implications = ["This clause may put you at a disadvantage", "Consider negotiating or seeking legal advice"]
                recommendations = ["Request modification of this clause", "Consult with a legal professional", "Consider this a deal-breaker"]
            elif assessment.level == ClassifierRiskLevel.YELLOW:
                explanation = f"⚡ MODERATE CONCERN: This clause has some issues that could be improved. {' '.join(assessment.reasons[:2])}"
                implications = ["This clause could be more tenant-friendly", "May cause issues in certain situations"]
                recommendations = ["Try to negotiate better terms", "Understand the implications fully", "Consider alternatives"]
            else:
                explanation = f"✅ FAIR TERMS: This clause appears to be standard and reasonable. {' '.join(assessment.reasons[:1]) if assessment.reasons else 'No major concerns identified.'}"
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
        
        # Generate summary based on overall risk
        if overall_risk_data['level'] == 'RED':
            summary = f"🚨 HIGH RISK DOCUMENT: This rental agreement contains {len([c for c in risk_analysis['clause_assessments'] if c['assessment'].level == ClassifierRiskLevel.RED])} high-risk clauses that need immediate attention. We strongly recommend legal review before signing."
        elif overall_risk_data['level'] == 'YELLOW':
            summary = f"⚠️ MODERATE RISK: This agreement has some concerning clauses that could be improved. Review the highlighted issues and consider negotiating better terms."
        else:
            summary = f"✅ LOW RISK: This appears to be a fairly standard rental agreement with reasonable terms. Review the details but generally acceptable."
        
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
                severity=keyword_risk.severity
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
            severity=severity
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
            severity="Medium"
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
    """Document analysis endpoint with enhanced validation"""
    document_text = request.form.get('document_text', '')
    
    # Validate document input
    is_valid, error_message = validate_document_input(document_text)
    
    if not is_valid:
        return render_template('index.html', error=error_message, document_text=document_text)
    
    # Perform AI-powered rental agreement analysis
    try:
        analysis = analyze_rental_agreement_with_llm(document_text)
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        # Fallback to basic analysis on error
        analysis = create_fallback_analysis(document_text)
    
    return render_template('results.html', analysis=analysis)

if __name__ == '__main__':
    app.run(debug=True)