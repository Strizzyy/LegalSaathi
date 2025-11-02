"""
Insights Controller for Advanced Natural Language AI Features
Handles actionable insights, conflict detection, bias analysis, and negotiation points
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from models.document_models import DocumentAnalysisRequest
from services.document_service import DocumentService
from services.legal_insights_engine import legal_insights_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])

# Initialize services
document_service = DocumentService()


@router.post("/generate")
async def generate_actionable_insights(
    analysis_id: str,
    document_text: Optional[str] = None,
    document_type: Optional[str] = "general_contract"
) -> Dict[str, Any]:
    """
    Generate comprehensive actionable insights for a document analysis
    
    Args:
        analysis_id: ID of existing document analysis
        document_text: Optional document text if not using existing analysis
        document_type: Type of document for specialized analysis
    
    Returns:
        Comprehensive actionable insights including conflicts, bias, negotiation points
    """
    try:
        logger.info(f"Generating actionable insights for analysis: {analysis_id}")
        
        # Debug: Log available analyses
        logger.debug(f"Available analyses: {list(document_service.analysis_storage.keys())}")
        
        # Check if analysis exists with retry mechanism for race conditions
        analysis_found = False
        max_retries = 3
        retry_delay = 0.5  # 500ms
        
        for attempt in range(max_retries):
            if analysis_id in document_service.analysis_storage:
                analysis_found = True
                break
            elif attempt < max_retries - 1:
                logger.warning(f"Analysis {analysis_id} not found, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
        
        # Get existing analysis if available
        if analysis_found:
            stored_analysis = document_service.analysis_storage[analysis_id]
            clause_analyses = stored_analysis['clause_assessments']
            doc_text = stored_analysis['response'].document_text
            # Handle document_type properly - it's stored as enum
            doc_type_obj = stored_analysis['document_type']
            if hasattr(doc_type_obj, 'value'):
                doc_type = doc_type_obj.value
            else:
                doc_type = str(doc_type_obj)
        elif document_text:
            # Use provided document text
            doc_text = document_text
            doc_type = document_type
            # Need to create temporary clause analyses
            clause_analyses = []
            logger.warning("No existing analysis found, using provided document text without clause analysis")
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Analysis {analysis_id} not found and no document text provided"
            )
        
        # Generate actionable insights
        try:
            insights = await document_service.generate_actionable_insights(
                doc_text, clause_analyses, doc_type
            )
        except Exception as insights_error:
            logger.error(f"Insights generation failed: {insights_error}")
            # Return empty insights structure as fallback
            insights = {
                'entity_relationships': [],
                'conflict_analysis': [],
                'bias_indicators': [],
                'negotiation_points': [],
                'compliance_flags': [],
                'overall_intelligence_score': 0.0,
                'generation_timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_relationships': 0,
                    'total_conflicts': 0,
                    'total_bias_indicators': 0,
                    'total_negotiation_points': 0,
                    'total_compliance_flags': 0,
                    'critical_issues': 0
                },
                'error': f"Insights generation failed: {str(insights_error)}"
            }
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "insights": insights,
            "message": "Actionable insights generated successfully" if 'error' not in insights else "Insights generation failed, returning empty structure"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate actionable insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")


@router.get("/analysis/{analysis_id}")
async def get_analysis_insights(analysis_id: str) -> Dict[str, Any]:
    """
    Get actionable insights for an existing document analysis
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Actionable insights if available, or generates them if not cached
    """
    try:
        logger.info(f"Retrieving insights for analysis: {analysis_id}")
        
        # Debug: Log available analyses
        logger.debug(f"Available analyses: {list(document_service.analysis_storage.keys())}")
        
        # Check if analysis exists with retry mechanism for race conditions
        max_retries = 3
        retry_delay = 0.5  # 500ms
        
        for attempt in range(max_retries):
            if analysis_id in document_service.analysis_storage:
                break
            elif attempt < max_retries - 1:
                logger.warning(f"Analysis {analysis_id} not found, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                import asyncio
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Analysis {analysis_id} not found after {max_retries} attempts")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Analysis {analysis_id} not found"
                )
        
        stored_analysis = document_service.analysis_storage[analysis_id]
        
        # Check if insights are already available in enhanced_insights
        response = stored_analysis['response']
        if (hasattr(response, 'enhanced_insights') and 
            response.enhanced_insights and 
            'actionable_insights' in response.enhanced_insights):
            
            insights = response.enhanced_insights['actionable_insights']
            logger.info("Returning cached actionable insights")
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "insights": insights,
                "cached": True,
                "message": "Cached actionable insights retrieved successfully"
            }
        
        # Generate insights if not available
        clause_analyses = stored_analysis['clause_assessments']
        doc_text = response.document_text
        # Handle document_type properly - it's stored as enum
        doc_type_obj = stored_analysis['document_type']
        if hasattr(doc_type_obj, 'value'):
            doc_type = doc_type_obj.value
        else:
            doc_type = str(doc_type_obj)
        
        try:
            insights = await document_service.generate_actionable_insights(
                doc_text, clause_analyses, doc_type
            )
        except Exception as insights_error:
            logger.error(f"Insights generation failed: {insights_error}")
            # Return empty insights structure as fallback
            insights = {
                'entity_relationships': [],
                'conflict_analysis': [],
                'bias_indicators': [],
                'negotiation_points': [],
                'compliance_flags': [],
                'overall_intelligence_score': 0.0,
                'generation_timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_relationships': 0,
                    'total_conflicts': 0,
                    'total_bias_indicators': 0,
                    'total_negotiation_points': 0,
                    'total_compliance_flags': 0,
                    'critical_issues': 0
                },
                'error': f"Insights generation failed: {str(insights_error)}"
            }
        
        # Update stored analysis with insights
        if not hasattr(response, 'enhanced_insights') or not response.enhanced_insights:
            response.enhanced_insights = {}
        response.enhanced_insights['actionable_insights'] = insights
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "insights": insights,
            "cached": False,
            "message": "Actionable insights generated and cached successfully" if 'error' not in insights else "Insights generation failed, returning empty structure"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")


@router.get("/conflicts/{analysis_id}")
async def get_conflict_analysis(analysis_id: str) -> Dict[str, Any]:
    """
    Get conflict analysis for a specific document
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Detailed conflict analysis including contradictions and inconsistencies
    """
    try:
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        conflicts = insights.get('conflict_analysis', [])
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "critical_conflicts": len([c for c in conflicts if c.get('severity') == 'critical']),
            "high_priority_conflicts": len([c for c in conflicts if c.get('severity') == 'high']),
            "message": f"Found {len(conflicts)} potential conflicts"
        }
        
    except Exception as e:
        logger.error(f"Failed to get conflict analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Conflict analysis failed: {str(e)}")


@router.get("/bias/{analysis_id}")
async def get_bias_analysis(analysis_id: str) -> Dict[str, Any]:
    """
    Get bias analysis for a specific document
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Detailed bias analysis including biased language and suggested alternatives
    """
    try:
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        bias_indicators = insights.get('bias_indicators', [])
        
        # Group by bias type
        bias_by_type = {}
        for bias in bias_indicators:
            bias_type = bias.get('bias_type', 'unknown')
            if bias_type not in bias_by_type:
                bias_by_type[bias_type] = []
            bias_by_type[bias_type].append(bias)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "bias_indicators": bias_indicators,
            "bias_by_type": bias_by_type,
            "total_bias_indicators": len(bias_indicators),
            "bias_types_found": list(bias_by_type.keys()),
            "critical_bias": len([b for b in bias_indicators if b.get('severity') == 'critical']),
            "message": f"Found {len(bias_indicators)} potential bias indicators"
        }
        
    except Exception as e:
        logger.error(f"Failed to get bias analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Bias analysis failed: {str(e)}")


@router.get("/negotiation/{analysis_id}")
async def get_negotiation_points(analysis_id: str) -> Dict[str, Any]:
    """
    Get negotiation opportunities for a specific document
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Detailed negotiation points with suggested language and rationale
    """
    try:
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        negotiation_points = insights.get('negotiation_points', [])
        
        # Group by priority
        points_by_priority = {}
        for point in negotiation_points:
            priority = point.get('priority', 'medium')
            if priority not in points_by_priority:
                points_by_priority[priority] = []
            points_by_priority[priority].append(point)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "negotiation_points": negotiation_points,
            "points_by_priority": points_by_priority,
            "total_points": len(negotiation_points),
            "critical_points": len(points_by_priority.get('critical', [])),
            "high_priority_points": len(points_by_priority.get('high', [])),
            "medium_priority_points": len(points_by_priority.get('medium', [])),
            "message": f"Found {len(negotiation_points)} negotiation opportunities"
        }
        
    except Exception as e:
        logger.error(f"Failed to get negotiation points: {e}")
        raise HTTPException(status_code=500, detail=f"Negotiation analysis failed: {str(e)}")


@router.get("/entities/{analysis_id}")
async def get_entity_relationships(analysis_id: str) -> Dict[str, Any]:
    """
    Get entity relationship mapping for a specific document
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Entity relationships and their legal significance
    """
    try:
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        entity_relationships = insights.get('entity_relationships', [])
        
        # Extract unique entities
        entities = set()
        for rel in entity_relationships:
            entities.add(rel.get('entity1', ''))
            entities.add(rel.get('entity2', ''))
        entities.discard('')  # Remove empty strings
        
        # Group by relationship type
        relationships_by_type = {}
        for rel in entity_relationships:
            rel_type = rel.get('relationship_type', 'unknown')
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            relationships_by_type[rel_type].append(rel)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "entity_relationships": entity_relationships,
            "relationships_by_type": relationships_by_type,
            "unique_entities": list(entities),
            "total_relationships": len(entity_relationships),
            "total_entities": len(entities),
            "relationship_types": list(relationships_by_type.keys()),
            "message": f"Found {len(entity_relationships)} entity relationships"
        }
        
    except Exception as e:
        logger.error(f"Failed to get entity relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Entity analysis failed: {str(e)}")


@router.get("/compliance/{analysis_id}")
async def get_compliance_analysis(analysis_id: str) -> Dict[str, Any]:
    """
    Get compliance analysis for a specific document
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        Compliance flags and regulatory concerns
    """
    try:
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        compliance_flags = insights.get('compliance_flags', [])
        
        # Group by regulation type
        flags_by_regulation = {}
        for flag in compliance_flags:
            reg_type = flag.get('regulation_type', 'unknown')
            if reg_type not in flags_by_regulation:
                flags_by_regulation[reg_type] = []
            flags_by_regulation[reg_type].append(flag)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "compliance_flags": compliance_flags,
            "flags_by_regulation": flags_by_regulation,
            "total_flags": len(compliance_flags),
            "regulation_types": list(flags_by_regulation.keys()),
            "critical_compliance_issues": len([f for f in compliance_flags if f.get('severity') == 'critical']),
            "high_priority_issues": len([f for f in compliance_flags if f.get('severity') == 'high']),
            "message": f"Found {len(compliance_flags)} potential compliance issues"
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance analysis failed: {str(e)}")


@router.get("/check/{analysis_id}")
async def check_analysis_exists(analysis_id: str) -> Dict[str, Any]:
    """
    Check if an analysis exists in storage
    """
    try:
        exists = analysis_id in document_service.analysis_storage
        available_analyses = list(document_service.analysis_storage.keys())
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "exists": exists,
            "available_analyses": available_analyses,
            "total_analyses": len(available_analyses),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Analysis check failed: {e}")
        return {
            "success": False,
            "analysis_id": analysis_id,
            "exists": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/health")
async def insights_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for insights service
    """
    try:
        # Test basic functionality
        from services.legal_insights_engine import legal_insights_engine
        
        return {
            "success": True,
            "service": "insights",
            "status": "healthy",
            "message": "Insights service is operational",
            "available_analyses": len(document_service.analysis_storage),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Insights health check failed: {e}")
        return {
            "success": False,
            "service": "insights", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/summary/{analysis_id}")
async def get_insights_summary(analysis_id: str) -> Dict[str, Any]:
    """
    Get a comprehensive summary of all actionable insights
    
    Args:
        analysis_id: ID of the document analysis
    
    Returns:
        High-level summary of all insights with key metrics
    """
    try:
        logger.info(f"Getting insights summary for analysis: {analysis_id}")
        
        # Debug: Check if analysis exists
        logger.debug(f"Available analyses in summary: {list(document_service.analysis_storage.keys())}")
        
        # Get full insights first
        insights_response = await get_analysis_insights(analysis_id)
        insights = insights_response['insights']
        
        summary = insights.get('summary', {})
        intelligence_score = insights.get('overall_intelligence_score', 0.0)
        
        # Calculate risk distribution
        all_issues = (
            insights.get('conflict_analysis', []) +
            insights.get('bias_indicators', []) +
            insights.get('compliance_flags', [])
        )
        
        critical_issues = len([item for item in all_issues if item.get('severity') == 'critical'])
        high_issues = len([item for item in all_issues if item.get('severity') == 'high'])
        medium_issues = len([item for item in all_issues if item.get('severity') == 'medium'])
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "intelligence_score": intelligence_score,
            "summary": summary,
            "risk_distribution": {
                "critical": critical_issues,
                "high": high_issues,
                "medium": medium_issues,
                "total": len(all_issues)
            },
            "key_metrics": {
                "negotiation_opportunities": summary.get('total_negotiation_points', 0),
                "compliance_concerns": summary.get('total_compliance_flags', 0),
                "document_conflicts": summary.get('total_conflicts', 0),
                "bias_indicators": summary.get('total_bias_indicators', 0),
                "entity_relationships": summary.get('total_relationships', 0)
            },
            "recommendations": [
                f"Review {critical_issues} critical issues immediately" if critical_issues > 0 else None,
                f"Consider negotiating {summary.get('total_negotiation_points', 0)} identified points" if summary.get('total_negotiation_points', 0) > 0 else None,
                f"Address {summary.get('total_compliance_flags', 0)} compliance concerns" if summary.get('total_compliance_flags', 0) > 0 else None,
                f"Resolve {summary.get('total_conflicts', 0)} document conflicts" if summary.get('total_conflicts', 0) > 0 else None
            ],
            "message": "Insights summary generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get insights summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")