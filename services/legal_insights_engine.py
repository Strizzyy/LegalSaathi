"""
Advanced Legal Insights Engine for Natural Language AI Enhancement
Provides conflict detection, bias analysis, negotiation point identification, 
entity relationship mapping, and compliance checking features.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from models.document_models import ClauseAnalysis, RiskLevel
from services.google_natural_language_service import natural_language_service

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    CONFLICT = "conflict"
    BIAS = "bias"
    NEGOTIATION_POINT = "negotiation_point"
    ENTITY_RELATIONSHIP = "entity_relationship"
    COMPLIANCE_FLAG = "compliance_flag"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EntityRelationship:
    """Represents a relationship between legal entities"""
    entity1: str
    entity2: str
    relationship_type: str
    description: str
    legal_significance: str
    confidence: float


@dataclass
class ConflictAnalysis:
    """Represents a detected conflict within the document"""
    conflict_id: str
    clause_ids: List[str]
    conflict_type: str
    description: str
    severity: SeverityLevel
    resolution_suggestions: List[str]
    confidence: float


@dataclass
class BiasIndicator:
    """Represents detected bias in document language"""
    bias_type: str
    clause_id: str
    biased_language: str
    explanation: str
    suggested_alternative: str
    severity: SeverityLevel
    confidence: float


@dataclass
class NegotiationPoint:
    """Represents a specific negotiation opportunity"""
    clause_id: str
    negotiation_type: str
    current_language: str
    suggested_language: str
    rationale: str
    priority: SeverityLevel
    potential_impact: str
    confidence: float


@dataclass
class ComplianceFlag:
    """Represents a potential compliance issue"""
    regulation_type: str
    clause_id: str
    issue_description: str
    compliance_risk: str
    recommended_action: str
    severity: SeverityLevel
    confidence: float


@dataclass
class ActionableInsights:
    """Complete actionable insights for a document"""
    entity_relationships: List[EntityRelationship]
    conflict_analysis: List[ConflictAnalysis]
    bias_indicators: List[BiasIndicator]
    negotiation_points: List[NegotiationPoint]
    compliance_flags: List[ComplianceFlag]
    overall_intelligence_score: float
    generation_timestamp: datetime


class LegalInsightsEngine:
    """Advanced legal insights engine for comprehensive document intelligence"""
    
    def __init__(self):
        self.bias_patterns = self._load_bias_patterns()
        self.negotiation_patterns = self._load_negotiation_patterns()
        self.compliance_patterns = self._load_compliance_patterns()
        self.entity_patterns = self._load_entity_patterns()
        
    async def generate_actionable_insights(
        self, 
        document_text: str, 
        clause_analyses: List[ClauseAnalysis],
        document_type: str = "general_contract"
    ) -> ActionableInsights:
        """Generate comprehensive actionable insights for a legal document"""
        
        logger.info(f"Generating actionable insights for {len(clause_analyses)} clauses")
        
        try:
            # Extract entity relationships
            entity_relationships = await self._extract_entity_relationships(document_text, clause_analyses)
            
            # Detect conflicts between clauses
            conflict_analysis = await self._detect_document_conflicts(clause_analyses)
            
            # Analyze bias in language
            bias_indicators = await self._analyze_bias_patterns(clause_analyses)
            
            # Identify negotiation opportunities
            negotiation_points = await self._identify_negotiation_points(clause_analyses, document_type)
            
            # Check compliance issues
            compliance_flags = await self._check_compliance_issues(clause_analyses, document_type)
            
            # Calculate overall intelligence score
            intelligence_score = self._calculate_intelligence_score(
                entity_relationships, conflict_analysis, bias_indicators, 
                negotiation_points, compliance_flags
            )
            
            insights = ActionableInsights(
                entity_relationships=entity_relationships,
                conflict_analysis=conflict_analysis,
                bias_indicators=bias_indicators,
                negotiation_points=negotiation_points,
                compliance_flags=compliance_flags,
                overall_intelligence_score=intelligence_score,
                generation_timestamp=datetime.now()
            )
            
            logger.info(f"Generated insights: {len(entity_relationships)} relationships, "
                       f"{len(conflict_analysis)} conflicts, {len(bias_indicators)} bias indicators, "
                       f"{len(negotiation_points)} negotiation points, {len(compliance_flags)} compliance flags")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate actionable insights: {e}")
            # Return empty insights structure on failure
            return ActionableInsights(
                entity_relationships=[],
                conflict_analysis=[],
                bias_indicators=[],
                negotiation_points=[],
                compliance_flags=[],
                overall_intelligence_score=0.0,
                generation_timestamp=datetime.now()
            )
    
    async def _extract_entity_relationships(
        self, 
        document_text: str, 
        clause_analyses: List[ClauseAnalysis]
    ) -> List[EntityRelationship]:
        """Extract and analyze relationships between legal entities"""
        
        relationships = []
        
        try:
            # Use Google Natural Language AI for entity extraction if available
            if natural_language_service.enabled:
                nl_analysis = natural_language_service.analyze_legal_document(document_text)
                entities = nl_analysis.get('entities', [])
                
                # Analyze relationships between high-relevance entities
                high_relevance_entities = [
                    e for e in entities 
                    if e.get('legal_relevance') in ['high', 'medium'] and e.get('salience', 0) > 0.1
                ]
                
                for i, entity1 in enumerate(high_relevance_entities):
                    for entity2 in high_relevance_entities[i+1:]:
                        relationship = self._analyze_entity_relationship(
                            entity1, entity2, document_text, clause_analyses
                        )
                        if relationship:
                            relationships.append(relationship)
            
            # Fallback: Pattern-based entity extraction
            else:
                entities = self._extract_entities_pattern_based(document_text)
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        relationship = self._analyze_entity_relationship_simple(
                            entity1, entity2, document_text
                        )
                        if relationship:
                            relationships.append(relationship)
            
            # Sort by legal significance and confidence
            relationships.sort(key=lambda x: (x.confidence, len(x.legal_significance)), reverse=True)
            
            return relationships[:10]  # Return top 10 most significant relationships
            
        except Exception as e:
            logger.error(f"Entity relationship extraction failed: {e}")
            return []
    
    async def _detect_document_conflicts(self, clause_analyses: List[ClauseAnalysis]) -> List[ConflictAnalysis]:
        """Detect conflicts and contradictions between clauses"""
        
        conflicts = []
        
        try:
            # Check for contradictory terms
            conflicts.extend(self._detect_contradictory_terms(clause_analyses))
            
            # Check for inconsistent obligations
            conflicts.extend(self._detect_inconsistent_obligations(clause_analyses))
            
            # Check for conflicting timelines
            conflicts.extend(self._detect_timeline_conflicts(clause_analyses))
            
            # Check for jurisdiction conflicts
            conflicts.extend(self._detect_jurisdiction_conflicts(clause_analyses))
            
            # Sort by severity and confidence
            conflicts.sort(key=lambda x: (x.severity.value, x.confidence), reverse=True)
            
            return conflicts[:15]  # Return top 15 most critical conflicts
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return []
    
    async def _analyze_bias_patterns(self, clause_analyses: List[ClauseAnalysis]) -> List[BiasIndicator]:
        """Analyze document language for bias patterns"""
        
        bias_indicators = []
        
        try:
            logger.info(f"Analyzing bias patterns in {len(clause_analyses)} clauses")
            
            for clause in clause_analyses:
                clause_text = clause.clause_text
                logger.info(f"🔍 Analyzing clause {clause.clause_id} (length: {len(clause_text)})")
                logger.info(f"📝 Clause text preview: {clause_text[:200]}...")
                
                # Check for various bias patterns
                for bias_type, patterns in self.bias_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern['regex'], clause_text, re.IGNORECASE):
                            logger.info(f"✅ Found {bias_type} bias in clause {clause.clause_id}: {pattern['regex']}")
                            bias_indicator = BiasIndicator(
                                bias_type=bias_type,
                                clause_id=clause.clause_id,
                                biased_language=pattern['example'],
                                explanation=pattern['explanation'],
                                suggested_alternative=pattern['alternative'],
                                severity=SeverityLevel(pattern['severity']),
                                confidence=pattern['confidence']
                            )
                            bias_indicators.append(bias_indicator)
                        else:
                            logger.debug(f"❌ No match for {bias_type} pattern '{pattern['regex']}' in clause {clause.clause_id}")
            
            # Remove duplicates and sort by severity
            unique_indicators = self._deduplicate_bias_indicators(bias_indicators)
            unique_indicators.sort(key=lambda x: (x.severity.value, x.confidence), reverse=True)
            
            return unique_indicators[:20]  # Return top 20 bias indicators
            
        except Exception as e:
            logger.error(f"Bias analysis failed: {e}")
            return []
    
    async def _identify_negotiation_points(
        self, 
        clause_analyses: List[ClauseAnalysis], 
        document_type: str
    ) -> List[NegotiationPoint]:
        """Identify specific negotiation opportunities"""
        
        negotiation_points = []
        
        try:
            logger.info(f"Identifying negotiation points in {len(clause_analyses)} clauses")
            
            for clause in clause_analyses:
                clause_text = clause.clause_text
                logger.debug(f"Checking negotiation patterns in clause {clause.clause_id}")
                
                # High-risk clauses are prime negotiation candidates
                if clause.risk_assessment.level == RiskLevel.RED:
                    points = self._extract_high_risk_negotiation_points(clause, document_type)
                    negotiation_points.extend(points)
                    logger.info(f"Found {len(points)} high-risk negotiation points in clause {clause.clause_id}")
                
                # Medium-risk clauses may have improvement opportunities
                elif clause.risk_assessment.level == RiskLevel.YELLOW:
                    points = self._extract_medium_risk_negotiation_points(clause, document_type)
                    negotiation_points.extend(points)
                    logger.info(f"Found {len(points)} medium-risk negotiation points in clause {clause.clause_id}")
                
                # Check for specific negotiation patterns
                for pattern_type, patterns in self.negotiation_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern['regex'], clause_text, re.IGNORECASE):
                            logger.info(f"Found {pattern_type} negotiation pattern in clause {clause.clause_id}: {pattern['regex']}")
                            negotiation_point = NegotiationPoint(
                                clause_id=clause.clause_id,
                                negotiation_type=pattern_type,
                                current_language=pattern['current_example'],
                                suggested_language=pattern['suggested_language'],
                                rationale=pattern['rationale'],
                                priority=SeverityLevel(pattern['priority']),
                                potential_impact=pattern['impact'],
                                confidence=pattern['confidence']
                            )
                            negotiation_points.append(negotiation_point)
            
            # Sort by priority and potential impact
            negotiation_points.sort(key=lambda x: (x.priority.value, x.confidence), reverse=True)
            
            return negotiation_points[:25]  # Return top 25 negotiation opportunities
            
        except Exception as e:
            logger.error(f"Negotiation point identification failed: {e}")
            return []
    
    async def _check_compliance_issues(
        self, 
        clause_analyses: List[ClauseAnalysis], 
        document_type: str
    ) -> List[ComplianceFlag]:
        """Check for potential compliance issues"""
        
        compliance_flags = []
        
        try:
            for clause in clause_analyses:
                clause_text = clause.clause_text.lower()
                
                # Check document-type specific compliance patterns
                relevant_patterns = self.compliance_patterns.get(document_type, {})
                general_patterns = self.compliance_patterns.get('general', {})
                
                all_patterns = {**general_patterns, **relevant_patterns}
                
                for regulation_type, patterns in all_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern['regex'], clause_text, re.IGNORECASE):
                            compliance_flag = ComplianceFlag(
                                regulation_type=regulation_type,
                                clause_id=clause.clause_id,
                                issue_description=pattern['issue'],
                                compliance_risk=pattern['risk'],
                                recommended_action=pattern['action'],
                                severity=SeverityLevel(pattern['severity']),
                                confidence=pattern['confidence']
                            )
                            compliance_flags.append(compliance_flag)
            
            # Sort by severity and confidence
            compliance_flags.sort(key=lambda x: (x.severity.value, x.confidence), reverse=True)
            
            return compliance_flags[:15]  # Return top 15 compliance issues
            
        except Exception as e:
            logger.error(f"Compliance checking failed: {e}")
            return []
    
    def _analyze_entity_relationship(
        self, 
        entity1: Dict, 
        entity2: Dict, 
        document_text: str, 
        clause_analyses: List[ClauseAnalysis]
    ) -> Optional[EntityRelationship]:
        """Analyze relationship between two entities using NLP data"""
        
        try:
            name1, name2 = entity1['name'], entity2['name']
            type1, type2 = entity1['type'], entity2['type']
            
            # Skip if entities are too similar or irrelevant
            if name1.lower() == name2.lower() or len(name1) < 3 or len(name2) < 3:
                return None
            
            # Determine relationship type based on entity types and context
            relationship_type = self._determine_relationship_type(type1, type2, document_text)
            
            if relationship_type:
                # Extract legal significance
                legal_significance = self._assess_legal_significance(
                    name1, name2, relationship_type, clause_analyses
                )
                
                # Calculate confidence based on entity salience and co-occurrence
                confidence = min(
                    (entity1.get('salience', 0) + entity2.get('salience', 0)) / 2,
                    self._calculate_co_occurrence_confidence(name1, name2, document_text)
                )
                
                if confidence > 0.3:  # Only return high-confidence relationships
                    return EntityRelationship(
                        entity1=name1,
                        entity2=name2,
                        relationship_type=relationship_type,
                        description=f"{name1} has a {relationship_type} relationship with {name2}",
                        legal_significance=legal_significance,
                        confidence=confidence
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Entity relationship analysis failed: {e}")
            return None
    
    def _detect_contradictory_terms(self, clause_analyses: List[ClauseAnalysis]) -> List[ConflictAnalysis]:
        """Detect contradictory terms between clauses"""
        
        conflicts = []
        
        # Define contradiction patterns
        contradiction_patterns = [
            {
                'pattern1': r'shall not.*terminate',
                'pattern2': r'may.*terminate',
                'type': 'termination_contradiction',
                'description': 'Conflicting termination rights'
            },
            {
                'pattern1': r'exclusive.*rights?',
                'pattern2': r'non-exclusive.*rights?',
                'type': 'exclusivity_contradiction',
                'description': 'Conflicting exclusivity terms'
            },
            {
                'pattern1': r'confidential',
                'pattern2': r'public.*disclosure',
                'type': 'confidentiality_contradiction',
                'description': 'Conflicting confidentiality requirements'
            }
        ]
        
        for i, clause1 in enumerate(clause_analyses):
            for j, clause2 in enumerate(clause_analyses[i+1:], i+1):
                for pattern in contradiction_patterns:
                    if (re.search(pattern['pattern1'], clause1.clause_text, re.IGNORECASE) and
                        re.search(pattern['pattern2'], clause2.clause_text, re.IGNORECASE)):
                        
                        conflict = ConflictAnalysis(
                            conflict_id=f"conflict_{i}_{j}_{pattern['type']}",
                            clause_ids=[clause1.clause_id, clause2.clause_id],
                            conflict_type=pattern['type'],
                            description=pattern['description'],
                            severity=SeverityLevel.HIGH,
                            resolution_suggestions=[
                                f"Clarify which clause takes precedence",
                                f"Modify one clause to align with the other",
                                f"Add exception language to resolve the conflict"
                            ],
                            confidence=0.8
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_inconsistent_obligations(self, clause_analyses: List[ClauseAnalysis]) -> List[ConflictAnalysis]:
        """Detect inconsistent obligations between clauses"""
        
        conflicts = []
        
        # Look for conflicting obligation patterns
        obligation_patterns = [
            {
                'positive': r'shall.*provide',
                'negative': r'not.*required.*provide',
                'type': 'provision_obligation_conflict'
            },
            {
                'positive': r'must.*maintain',
                'negative': r'no.*obligation.*maintain',
                'type': 'maintenance_obligation_conflict'
            }
        ]
        
        for i, clause1 in enumerate(clause_analyses):
            for j, clause2 in enumerate(clause_analyses[i+1:], i+1):
                for pattern in obligation_patterns:
                    if (re.search(pattern['positive'], clause1.clause_text, re.IGNORECASE) and
                        re.search(pattern['negative'], clause2.clause_text, re.IGNORECASE)):
                        
                        conflict = ConflictAnalysis(
                            conflict_id=f"obligation_conflict_{i}_{j}",
                            clause_ids=[clause1.clause_id, clause2.clause_id],
                            conflict_type=pattern['type'],
                            description="Inconsistent obligation requirements between clauses",
                            severity=SeverityLevel.MEDIUM,
                            resolution_suggestions=[
                                "Clarify the scope of obligations",
                                "Define exceptions clearly",
                                "Establish hierarchy of obligations"
                            ],
                            confidence=0.7
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_timeline_conflicts(self, clause_analyses: List[ClauseAnalysis]) -> List[ConflictAnalysis]:
        """Detect conflicting timelines between clauses"""
        
        conflicts = []
        
        # Extract timeline information from clauses
        timeline_pattern = r'(\d+)\s*(days?|weeks?|months?|years?)'
        
        clause_timelines = []
        for clause in clause_analyses:
            matches = re.findall(timeline_pattern, clause.clause_text, re.IGNORECASE)
            if matches:
                clause_timelines.append({
                    'clause': clause,
                    'timelines': matches
                })
        
        # Check for conflicting timelines for similar obligations
        conflict_keywords = ['notice', 'termination', 'payment', 'delivery', 'completion']
        
        for keyword in conflict_keywords:
            relevant_clauses = [
                ct for ct in clause_timelines 
                if keyword in ct['clause'].clause_text.lower()
            ]
            
            if len(relevant_clauses) > 1:
                # Check if timelines are significantly different
                for i, ct1 in enumerate(relevant_clauses):
                    for ct2 in relevant_clauses[i+1:]:
                        if self._timelines_conflict(ct1['timelines'], ct2['timelines']):
                            conflict = ConflictAnalysis(
                                conflict_id=f"timeline_conflict_{ct1['clause'].clause_id}_{ct2['clause'].clause_id}",
                                clause_ids=[ct1['clause'].clause_id, ct2['clause'].clause_id],
                                conflict_type="timeline_inconsistency",
                                description=f"Conflicting {keyword} timelines between clauses",
                                severity=SeverityLevel.MEDIUM,
                                resolution_suggestions=[
                                    f"Standardize {keyword} timeline across document",
                                    "Clarify which timeline applies in different scenarios",
                                    "Add priority rules for conflicting timelines"
                                ],
                                confidence=0.6
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_jurisdiction_conflicts(self, clause_analyses: List[ClauseAnalysis]) -> List[ConflictAnalysis]:
        """Detect conflicting jurisdiction clauses"""
        
        conflicts = []
        
        # Look for jurisdiction-related clauses
        jurisdiction_clauses = []
        for clause in clause_analyses:
            clause_text = clause.clause_text.lower()
            if any(term in clause_text for term in ['jurisdiction', 'governing law', 'court', 'venue']):
                jurisdiction_clauses.append(clause)
        
        # Check for conflicts between jurisdiction clauses
        if len(jurisdiction_clauses) > 1:
            for i, clause1 in enumerate(jurisdiction_clauses):
                for clause2 in jurisdiction_clauses[i+1:]:
                    # Simple check for different jurisdictions mentioned
                    text1 = clause1.clause_text.lower()
                    text2 = clause2.clause_text.lower()
                    
                    # Look for different state/country names
                    jurisdictions1 = self._extract_jurisdictions(text1)
                    jurisdictions2 = self._extract_jurisdictions(text2)
                    
                    if jurisdictions1 and jurisdictions2 and not jurisdictions1.intersection(jurisdictions2):
                        conflict = ConflictAnalysis(
                            conflict_id=f"jurisdiction_conflict_{clause1.clause_id}_{clause2.clause_id}",
                            clause_ids=[clause1.clause_id, clause2.clause_id],
                            conflict_type="jurisdiction_inconsistency",
                            description=f"Conflicting jurisdictions: {', '.join(jurisdictions1)} vs {', '.join(jurisdictions2)}",
                            severity=SeverityLevel.HIGH,
                            resolution_suggestions=[
                                "Choose a single governing jurisdiction",
                                "Clarify which jurisdiction applies to different aspects",
                                "Add hierarchy rules for jurisdiction conflicts"
                            ],
                            confidence=0.7
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _extract_jurisdictions(self, text: str) -> set:
        """Extract jurisdiction names from text"""
        # Simple jurisdiction extraction - could be enhanced with more comprehensive lists
        jurisdictions = set()
        
        # Common US states
        us_states = ['california', 'new york', 'texas', 'florida', 'illinois', 'pennsylvania', 'ohio', 'georgia', 'north carolina', 'michigan']
        for state in us_states:
            if state in text:
                jurisdictions.add(state.title())
        
        # Common countries
        countries = ['united states', 'canada', 'united kingdom', 'australia', 'germany', 'france', 'japan']
        for country in countries:
            if country in text:
                jurisdictions.add(country.title())
        
        return jurisdictions
    
    def _extract_high_risk_negotiation_points(
        self, 
        clause: ClauseAnalysis, 
        document_type: str
    ) -> List[NegotiationPoint]:
        """Extract negotiation points from high-risk clauses"""
        
        points = []
        
        # Enhanced high-risk patterns that should be negotiated
        high_risk_patterns = [
            {
                'pattern': r'sole discretion',
                'current': 'at [party]\'s sole discretion',
                'suggested': 'at [party]\'s reasonable discretion, not to be unreasonably withheld',
                'rationale': 'Limits arbitrary decision-making',
                'impact': 'Provides protection against unfair treatment'
            },
            {
                'pattern': r'unlimited liability',
                'current': 'unlimited liability',
                'suggested': 'liability limited to [amount] or [percentage] of contract value',
                'rationale': 'Caps financial exposure',
                'impact': 'Prevents catastrophic financial loss'
            },
            {
                'pattern': r'indemnify.*all.*claims',
                'current': 'indemnify against all claims',
                'suggested': 'indemnify against claims arising from [specific circumstances]',
                'rationale': 'Limits scope of indemnification',
                'impact': 'Reduces legal and financial exposure'
            },
            {
                'pattern': r'without.*notice',
                'current': 'terminate without notice',
                'suggested': 'terminate with [X] days written notice',
                'rationale': 'Provides time to remedy issues',
                'impact': 'Prevents sudden termination'
            },
            {
                'pattern': r'immediately.*upon',
                'current': 'immediately upon breach',
                'suggested': 'after [X] days written notice and opportunity to cure',
                'rationale': 'Allows time to fix problems',
                'impact': 'Prevents immediate termination'
            },
            {
                'pattern': r'all.*damages',
                'current': 'liable for all damages',
                'suggested': 'liable for direct damages up to [amount]',
                'rationale': 'Limits damage exposure',
                'impact': 'Caps financial liability'
            },
            {
                'pattern': r'waive.*rights?',
                'current': 'waive all rights',
                'suggested': 'waive specific rights as listed',
                'rationale': 'Preserves important legal protections',
                'impact': 'Maintains legal recourse'
            }
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern['pattern'], clause.clause_text, re.IGNORECASE):
                point = NegotiationPoint(
                    clause_id=clause.clause_id,
                    negotiation_type="risk_mitigation",
                    current_language=pattern['current'],
                    suggested_language=pattern['suggested'],
                    rationale=pattern['rationale'],
                    priority=SeverityLevel.HIGH,
                    potential_impact=pattern['impact'],
                    confidence=0.9
                )
                points.append(point)
        
        return points
    
    def _extract_medium_risk_negotiation_points(
        self, 
        clause: ClauseAnalysis, 
        document_type: str
    ) -> List[NegotiationPoint]:
        """Extract negotiation points from medium-risk clauses"""
        
        points = []
        
        # Medium-risk patterns that could be improved
        medium_risk_patterns = [
            {
                'pattern': r'reasonable efforts',
                'current': 'reasonable efforts',
                'suggested': 'best efforts' or 'commercially reasonable efforts',
                'rationale': 'Clarifies level of effort required',
                'impact': 'Sets clearer performance expectations'
            },
            {
                'pattern': r'as soon as possible',
                'current': 'as soon as possible',
                'suggested': 'within [specific timeframe]',
                'rationale': 'Provides definite timeline',
                'impact': 'Prevents delays and disputes'
            }
        ]
        
        for pattern in medium_risk_patterns:
            if re.search(pattern['pattern'], clause.clause_text, re.IGNORECASE):
                point = NegotiationPoint(
                    clause_id=clause.clause_id,
                    negotiation_type="clarity_improvement",
                    current_language=pattern['current'],
                    suggested_language=pattern['suggested'],
                    rationale=pattern['rationale'],
                    priority=SeverityLevel.MEDIUM,
                    potential_impact=pattern['impact'],
                    confidence=0.7
                )
                points.append(point)
        
        return points
    
    def _load_bias_patterns(self) -> Dict[str, List[Dict]]:
        """Load enhanced bias detection patterns"""
        return {
            'gender_bias': [
                {
                    'regex': r'\b(he|his|him)\b(?!.*\b(she|her|hers)\b)',
                    'example': 'he shall provide',
                    'explanation': 'Uses male pronouns exclusively',
                    'alternative': 'they shall provide',
                    'severity': 'medium',
                    'confidence': 0.8
                }
            ],
            'power_imbalance': [
                {
                    'regex': r'at.*sole.*discretion',
                    'example': 'at Company\'s sole discretion',
                    'explanation': 'Gives one party complete control',
                    'alternative': 'at Company\'s reasonable discretion',
                    'severity': 'high',
                    'confidence': 0.9
                },
                {
                    'regex': r'absolute.*right',
                    'example': 'absolute right to terminate',
                    'explanation': 'Grants unlimited power to one party',
                    'alternative': 'right to terminate with cause',
                    'severity': 'high',
                    'confidence': 0.85
                },
                {
                    'regex': r'final.*decision',
                    'example': 'Company\'s final decision',
                    'explanation': 'Removes appeal or review options',
                    'alternative': 'decision subject to reasonable review',
                    'severity': 'medium',
                    'confidence': 0.7
                }
            ],
            'unfair_advantage': [
                {
                    'regex': r'without.*notice',
                    'example': 'terminate without notice',
                    'explanation': 'Allows action without warning',
                    'alternative': 'terminate with [X] days notice',
                    'severity': 'high',
                    'confidence': 0.8
                },
                {
                    'regex': r'immediately.*effective',
                    'example': 'immediately effective termination',
                    'explanation': 'No grace period or cure time',
                    'alternative': 'effective after [X] days notice',
                    'severity': 'high',
                    'confidence': 0.8
                },
                {
                    'regex': r'waive.*all.*rights',
                    'example': 'waive all rights to appeal',
                    'explanation': 'Removes important legal protections',
                    'alternative': 'waive specific enumerated rights',
                    'severity': 'high',
                    'confidence': 0.9
                }
            ],
            'financial_bias': [
                {
                    'regex': r'all.*costs.*expenses',
                    'example': 'responsible for all costs and expenses',
                    'explanation': 'Unlimited financial responsibility',
                    'alternative': 'responsible for reasonable costs up to [amount]',
                    'severity': 'high',
                    'confidence': 0.8
                },
                {
                    'regex': r'no.*refund',
                    'example': 'no refund under any circumstances',
                    'explanation': 'Eliminates refund rights completely',
                    'alternative': 'refund available under specific conditions',
                    'severity': 'medium',
                    'confidence': 0.7
                }
            ],
            'nda_bias': [
                {
                    'regex': r'indefinitely|perpetual|forever',
                    'example': 'confidentiality obligations continue indefinitely',
                    'explanation': 'Unlimited time commitment for confidentiality',
                    'alternative': 'confidentiality obligations for [X] years',
                    'severity': 'high',
                    'confidence': 0.9
                },
                {
                    'regex': r'all.*information.*confidential',
                    'example': 'all information shall be confidential',
                    'explanation': 'Overly broad confidentiality scope',
                    'alternative': 'specifically identified information shall be confidential',
                    'severity': 'medium',
                    'confidence': 0.8
                }
            ]
        }
    
    def _load_negotiation_patterns(self) -> Dict[str, List[Dict]]:
        """Load enhanced negotiation opportunity patterns"""
        return {
            'liability_limitation': [
                {
                    'regex': r'unlimited.*liability',
                    'current_example': 'unlimited liability for damages',
                    'suggested_language': 'liability limited to contract value',
                    'rationale': 'Caps financial exposure',
                    'priority': 'critical',
                    'impact': 'Prevents unlimited financial loss',
                    'confidence': 0.95
                },
                {
                    'regex': r'liable.*for.*all',
                    'current_example': 'liable for all damages',
                    'suggested_language': 'liable for direct damages only',
                    'rationale': 'Excludes consequential damages',
                    'priority': 'high',
                    'impact': 'Reduces damage exposure',
                    'confidence': 0.85
                }
            ],
            'termination_rights': [
                {
                    'regex': r'terminate.*without.*cause',
                    'current_example': 'may terminate without cause',
                    'suggested_language': 'may terminate with 30 days notice',
                    'rationale': 'Provides notice period for planning',
                    'priority': 'high',
                    'impact': 'Allows time to find alternatives',
                    'confidence': 0.85
                },
                {
                    'regex': r'immediate.*termination',
                    'current_example': 'immediate termination allowed',
                    'suggested_language': 'termination with 15 days cure period',
                    'rationale': 'Allows opportunity to fix issues',
                    'priority': 'high',
                    'impact': 'Prevents sudden contract loss',
                    'confidence': 0.8
                }
            ],
            'payment_terms': [
                {
                    'regex': r'payment.*due.*immediately',
                    'current_example': 'payment due immediately',
                    'suggested_language': 'payment due within 30 days',
                    'rationale': 'Provides reasonable payment period',
                    'priority': 'medium',
                    'impact': 'Improves cash flow management',
                    'confidence': 0.8
                },
                {
                    'regex': r'late.*fee.*penalty',
                    'current_example': 'late fee penalty of 10% per month',
                    'suggested_language': 'late fee of 1.5% per month maximum',
                    'rationale': 'Reduces excessive penalty rates',
                    'priority': 'medium',
                    'impact': 'Limits penalty exposure',
                    'confidence': 0.75
                }
            ],
            'dispute_resolution': [
                {
                    'regex': r'binding.*arbitration',
                    'current_example': 'binding arbitration required',
                    'suggested_language': 'mediation first, then arbitration',
                    'rationale': 'Allows cheaper resolution attempt first',
                    'priority': 'medium',
                    'impact': 'Reduces dispute resolution costs',
                    'confidence': 0.7
                }
            ],
            'confidentiality_scope': [
                {
                    'regex': r'all.*information',
                    'current_example': 'all information disclosed',
                    'suggested_language': 'specifically marked confidential information',
                    'rationale': 'Limits scope to truly confidential material',
                    'priority': 'high',
                    'impact': 'Prevents over-broad confidentiality obligations',
                    'confidence': 0.85
                },
                {
                    'regex': r'indefinitely|perpetual',
                    'current_example': 'confidentiality obligations continue indefinitely',
                    'suggested_language': 'confidentiality obligations for 5 years',
                    'rationale': 'Limits duration of confidentiality',
                    'priority': 'high',
                    'impact': 'Prevents permanent confidentiality burden',
                    'confidence': 0.9
                }
            ]
        }
    
    def _load_compliance_patterns(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Load enhanced compliance checking patterns"""
        return {
            'employment_contract': {
                'labor_law': [
                    {
                        'regex': r'work.*more.*than.*40.*hours',
                        'issue': 'Potential overtime law violation',
                        'risk': 'May violate federal labor standards',
                        'action': 'Ensure compliance with FLSA overtime requirements',
                        'severity': 'high',
                        'confidence': 0.8
                    },
                    {
                        'regex': r'no.*break.*lunch',
                        'issue': 'Missing break/meal period provisions',
                        'risk': 'May violate state labor laws',
                        'action': 'Add required break and meal periods',
                        'severity': 'medium',
                        'confidence': 0.7
                    }
                ]
            },
            'rental_agreement': {
                'tenant_rights': [
                    {
                        'regex': r'no.*pets.*allowed',
                        'issue': 'Potential service animal discrimination',
                        'risk': 'May violate ADA requirements',
                        'action': 'Add exception for service animals',
                        'severity': 'high',
                        'confidence': 0.8
                    },
                    {
                        'regex': r'deposit.*non.*refundable',
                        'issue': 'Non-refundable deposit may be illegal',
                        'risk': 'May violate state tenant protection laws',
                        'action': 'Review local deposit refund requirements',
                        'severity': 'medium',
                        'confidence': 0.7
                    }
                ]
            },
            'general': {
                'data_privacy': [
                    {
                        'regex': r'personal.*data.*without.*consent',
                        'issue': 'Potential privacy law violation',
                        'risk': 'May violate GDPR or similar privacy laws',
                        'action': 'Add explicit consent requirements',
                        'severity': 'high',
                        'confidence': 0.9
                    },
                    {
                        'regex': r'share.*information.*third.*party',
                        'issue': 'Data sharing without disclosure',
                        'risk': 'May violate privacy regulations',
                        'action': 'Add clear data sharing disclosure',
                        'severity': 'medium',
                        'confidence': 0.8
                    }
                ],
                'consumer_protection': [
                    {
                        'regex': r'no.*warranty.*whatsoever',
                        'issue': 'Complete warranty disclaimer',
                        'risk': 'May violate consumer protection laws',
                        'action': 'Provide minimum required warranties',
                        'severity': 'medium',
                        'confidence': 0.7
                    },
                    {
                        'regex': r'automatic.*renewal',
                        'issue': 'Auto-renewal without clear notice',
                        'risk': 'May violate consumer protection laws',
                        'action': 'Add clear auto-renewal disclosure',
                        'severity': 'medium',
                        'confidence': 0.8
                    }
                ]
            }
        }
    
    def _load_entity_patterns(self) -> Dict[str, str]:
        """Load entity extraction patterns for fallback"""
        return {
            'person': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            'company': r'\b[A-Z][a-zA-Z\s]*(?:Inc|LLC|Corp|Ltd|Company)\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'money': r'\$[\d,]+(?:\.\d{2})?'
        }
    
    def _calculate_intelligence_score(
        self,
        entity_relationships: List[EntityRelationship],
        conflicts: List[ConflictAnalysis],
        bias_indicators: List[BiasIndicator],
        negotiation_points: List[NegotiationPoint],
        compliance_flags: List[ComplianceFlag]
    ) -> float:
        """Calculate overall document intelligence score"""
        
        # Base score starts at 50
        base_score = 50.0
        
        # Add points for insights discovered
        relationship_score = min(len(entity_relationships) * 2, 20)
        negotiation_score = min(len(negotiation_points) * 1.5, 15)
        
        # Subtract points for issues found
        conflict_penalty = min(len(conflicts) * 3, 15)
        bias_penalty = min(len(bias_indicators) * 2, 10)
        compliance_penalty = min(len(compliance_flags) * 4, 20)
        
        final_score = base_score + relationship_score + negotiation_score - conflict_penalty - bias_penalty - compliance_penalty
        
        return max(0.0, min(100.0, final_score))
    
    # Helper methods
    def _determine_relationship_type(self, type1: str, type2: str, document_text: str) -> Optional[str]:
        """Determine relationship type between entities"""
        if type1 == 'PERSON' and type2 == 'ORGANIZATION':
            return 'employment' if 'employ' in document_text.lower() else 'contractual'
        elif type1 == 'ORGANIZATION' and type2 == 'ORGANIZATION':
            return 'partnership' if 'partner' in document_text.lower() else 'vendor'
        return 'contractual'
    
    def _assess_legal_significance(self, name1: str, name2: str, relationship_type: str, clauses: List[ClauseAnalysis]) -> str:
        """Assess legal significance of entity relationship"""
        # Count mentions in high-risk clauses
        high_risk_mentions = sum(
            1 for clause in clauses 
            if clause.risk_assessment.level == RiskLevel.RED and 
            (name1.lower() in clause.clause_text.lower() or name2.lower() in clause.clause_text.lower())
        )
        
        if high_risk_mentions > 0:
            return f"High significance - mentioned in {high_risk_mentions} high-risk clauses"
        else:
            return f"Standard {relationship_type} relationship"
    
    def _calculate_co_occurrence_confidence(self, name1: str, name2: str, document_text: str) -> float:
        """Calculate confidence based on entity co-occurrence"""
        sentences = document_text.split('.')
        co_occurrences = sum(
            1 for sentence in sentences 
            if name1.lower() in sentence.lower() and name2.lower() in sentence.lower()
        )
        return min(co_occurrences * 0.2, 1.0)
    
    def _extract_entities_pattern_based(self, document_text: str) -> List[Dict]:
        """Fallback entity extraction using patterns"""
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, document_text)
            for match in matches[:5]:  # Limit to 5 per type
                entities.append({
                    'name': match,
                    'type': entity_type.upper(),
                    'salience': 0.5  # Default salience
                })
        return entities
    
    def _analyze_entity_relationship_simple(self, entity1: Dict, entity2: Dict, document_text: str) -> Optional[EntityRelationship]:
        """Simple entity relationship analysis for fallback"""
        name1, name2 = entity1['name'], entity2['name']
        
        if len(name1) < 3 or len(name2) < 3:
            return None
        
        # Simple co-occurrence check
        confidence = self._calculate_co_occurrence_confidence(name1, name2, document_text)
        
        if confidence > 0.3:
            return EntityRelationship(
                entity1=name1,
                entity2=name2,
                relationship_type='contractual',
                description=f"Contractual relationship between {name1} and {name2}",
                legal_significance="Standard contractual relationship",
                confidence=confidence
            )
        
        return None
    
    def _deduplicate_bias_indicators(self, indicators: List[BiasIndicator]) -> List[BiasIndicator]:
        """Remove duplicate bias indicators"""
        seen = set()
        unique = []
        for indicator in indicators:
            key = (indicator.bias_type, indicator.clause_id, indicator.biased_language)
            if key not in seen:
                seen.add(key)
                unique.append(indicator)
        return unique
    
    def _timelines_conflict(self, timelines1: List[Tuple], timelines2: List[Tuple]) -> bool:
        """Check if two sets of timelines conflict"""
        # Simple check - if timelines differ by more than 50%, consider it a conflict
        if not timelines1 or not timelines2:
            return False
        
        # Convert to days for comparison
        def to_days(amount: str, unit: str) -> int:
            amount = int(amount)
            unit = unit.lower()
            if 'day' in unit:
                return amount
            elif 'week' in unit:
                return amount * 7
            elif 'month' in unit:
                return amount * 30
            elif 'year' in unit:
                return amount * 365
            return amount
        
        days1 = [to_days(amount, unit) for amount, unit in timelines1]
        days2 = [to_days(amount, unit) for amount, unit in timelines2]
        
        avg1 = sum(days1) / len(days1)
        avg2 = sum(days2) / len(days2)
        
        # Consider conflict if difference is more than 50%
        return abs(avg1 - avg2) / max(avg1, avg2) > 0.5


# Global instance
legal_insights_engine = LegalInsightsEngine()