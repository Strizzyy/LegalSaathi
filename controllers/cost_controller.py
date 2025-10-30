"""
Cost Monitoring and Analytics Controller for LegalSaathi
Provides API endpoints for cost tracking, quota monitoring, and analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from services.cost_monitoring_service import cost_monitor, ServiceType, OperationType
from services.quota_manager import quota_manager, ServicePriority

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CostAnalyticsResponse(BaseModel):
    daily_cost: float = Field(..., description="Total cost for today")
    monthly_cost: float = Field(..., description="Total cost for current month")
    service_breakdown: Dict[str, float] = Field(..., description="Cost breakdown by service")
    usage_trends: List[Dict[str, Any]] = Field(..., description="Daily usage trends")
    optimization_suggestions: List[str] = Field(..., description="Cost optimization suggestions")
    cost_savings: float = Field(..., description="Potential cost savings")

class QuotaStatusResponse(BaseModel):
    service: str = Field(..., description="Service name")
    quota_limits: Dict[str, int] = Field(..., description="Quota limits")
    current_usage: Dict[str, int] = Field(..., description="Current usage")
    usage_percentages: Dict[str, float] = Field(..., description="Usage percentages")
    circuit_breaker: Dict[str, Any] = Field(..., description="Circuit breaker status")
    priority: str = Field(..., description="Service priority")
    timestamp: str = Field(..., description="Status timestamp")

class AllQuotaStatusResponse(BaseModel):
    services: Dict[str, Any] = Field(..., description="Status for all services")
    timestamp: str = Field(..., description="Status timestamp")
    batch_config: Dict[str, Any] = Field(..., description="Batch processing configuration")
    active_batches: int = Field(..., description="Number of active batches")

class HealthStatusResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    components: Dict[str, Any] = Field(..., description="Component health status")

class UsageMetricsResponse(BaseModel):
    service: str = Field(..., description="Service name")
    operation: str = Field(..., description="Operation type")
    tokens_used: int = Field(..., description="Tokens consumed")
    estimated_cost: float = Field(..., description="Estimated cost")
    timestamp: str = Field(..., description="Usage timestamp")
    request_id: str = Field(..., description="Request identifier")

# Create router
router = APIRouter(prefix="/api/costs", tags=["Cost Monitoring"])

@router.get("/analytics", response_model=CostAnalyticsResponse)
async def get_cost_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: Optional[str] = Query(None, description="Filter by specific service")
):
    """
    Get comprehensive cost analytics and optimization suggestions.
    
    - **days**: Number of days to analyze (1-365)
    - **service**: Optional service filter (vertex_ai, gemini_api, document_ai, etc.)
    """
    try:
        logger.info(f"Getting cost analytics for {days} days, service: {service}")
        
        # Get analytics from cost monitor
        analytics = await cost_monitor.get_cost_analytics(days=days)
        
        # Filter by service if specified
        if service and service in analytics.service_breakdown:
            filtered_breakdown = {service: analytics.service_breakdown[service]}
            # Recalculate daily/monthly costs for the specific service
            daily_cost = await cost_monitor.get_daily_cost(service)
            monthly_cost = await cost_monitor.get_monthly_cost(service)
        else:
            filtered_breakdown = analytics.service_breakdown
            daily_cost = analytics.daily_cost
            monthly_cost = analytics.monthly_cost
        
        return CostAnalyticsResponse(
            daily_cost=daily_cost,
            monthly_cost=monthly_cost,
            service_breakdown=filtered_breakdown,
            usage_trends=analytics.usage_trends,
            optimization_suggestions=analytics.optimization_suggestions,
            cost_savings=analytics.cost_savings
        )
        
    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost analytics: {str(e)}")

@router.get("/quota/{service}", response_model=QuotaStatusResponse)
async def get_service_quota_status(service: str):
    """
    Get quota status for a specific service.
    
    - **service**: Service name (vertex_ai, gemini_api, document_ai, natural_language_ai, translation_api, vision_api, speech_api)
    """
    try:
        logger.info(f"Getting quota status for service: {service}")
        
        # Validate service name
        valid_services = [s.value for s in ServiceType]
        if service not in valid_services:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
            )
        
        quota_status = await quota_manager.get_quota_status(service)
        
        if "error" in quota_status:
            raise HTTPException(status_code=500, detail=quota_status["error"])
        
        return QuotaStatusResponse(**quota_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quota status for {service}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota status: {str(e)}")

@router.get("/quota", response_model=AllQuotaStatusResponse)
async def get_all_quota_status():
    """
    Get quota status for all services.
    """
    try:
        logger.info("Getting quota status for all services")
        
        all_status = await quota_manager.get_all_quota_status()
        
        if "error" in all_status:
            raise HTTPException(status_code=500, detail=all_status["error"])
        
        return AllQuotaStatusResponse(**all_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all quota status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota status: {str(e)}")

@router.get("/health", response_model=HealthStatusResponse)
async def get_cost_system_health():
    """
    Get health status of the cost monitoring system.
    """
    try:
        logger.info("Getting cost system health status")
        
        # Get health from both services
        cost_health = await cost_monitor.get_health_status()
        quota_health = await quota_manager.get_health_status()
        
        # Combine health status
        overall_status = "healthy"
        if cost_health["status"] != "healthy" or quota_health["status"] != "healthy":
            overall_status = "degraded"
        
        combined_health = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "cost_monitoring": cost_health["components"],
                "quota_management": quota_health["components"]
            }
        }
        
        return HealthStatusResponse(**combined_health)
        
    except Exception as e:
        logger.error(f"Error getting cost system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.get("/daily/{service}")
async def get_daily_cost(service: Optional[str] = None):
    """
    Get daily cost for a specific service or all services.
    
    - **service**: Optional service name filter
    """
    try:
        logger.info(f"Getting daily cost for service: {service}")
        
        if service:
            # Validate service name
            valid_services = [s.value for s in ServiceType]
            if service not in valid_services:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
                )
        
        daily_cost = await cost_monitor.get_daily_cost(service)
        
        return {
            "service": service or "all",
            "daily_cost": daily_cost,
            "date": datetime.utcnow().date().isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily cost: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily cost: {str(e)}")

@router.get("/monthly/{service}")
async def get_monthly_cost(service: Optional[str] = None):
    """
    Get monthly cost for a specific service or all services.
    
    - **service**: Optional service name filter
    """
    try:
        logger.info(f"Getting monthly cost for service: {service}")
        
        if service:
            # Validate service name
            valid_services = [s.value for s in ServiceType]
            if service not in valid_services:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
                )
        
        monthly_cost = await cost_monitor.get_monthly_cost(service)
        
        return {
            "service": service or "all",
            "monthly_cost": monthly_cost,
            "month": datetime.utcnow().strftime("%Y-%m"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly cost: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monthly cost: {str(e)}")

@router.post("/optimize")
async def optimize_request(
    service: str,
    operation: str,
    usage_amount: int = 1,
    priority: str = "medium"
):
    """
    Get optimization recommendations for an API request.
    
    - **service**: Service name
    - **operation**: Operation type
    - **usage_amount**: Amount of usage (tokens, pages, etc.)
    - **priority**: Request priority (high, medium, low)
    """
    try:
        logger.info(f"Optimizing request for {service}/{operation}")
        
        # Validate service name
        valid_services = [s.value for s in ServiceType]
        if service not in valid_services:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
            )
        
        # Convert priority string to enum
        priority_map = {
            "high": ServicePriority.HIGH,
            "medium": ServicePriority.MEDIUM,
            "low": ServicePriority.LOW
        }
        
        if priority.lower() not in priority_map:
            raise HTTPException(
                status_code=400,
                detail="Invalid priority. Valid values: high, medium, low"
            )
        
        service_priority = priority_map[priority.lower()]
        
        # Get optimization recommendations
        optimization = await quota_manager.optimize_request_timing(
            service=service,
            operation=operation,
            usage_amount=usage_amount,
            priority=service_priority
        )
        
        return {
            "service": service,
            "operation": operation,
            "usage_amount": usage_amount,
            "priority": priority,
            "optimization": optimization,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize request: {str(e)}")

@router.get("/services")
async def get_available_services():
    """
    Get list of available services for cost monitoring.
    """
    try:
        services = [
            {
                "name": service.value,
                "display_name": service.value.replace("_", " ").title(),
                "description": f"{service.value.replace('_', ' ').title()} service"
            }
            for service in ServiceType
        ]
        
        operations = [
            {
                "name": operation.value,
                "display_name": operation.value.replace("_", " ").title(),
                "description": f"{operation.value.replace('_', ' ').title()} operation"
            }
            for operation in OperationType
        ]
        
        return {
            "services": services,
            "operations": operations,
            "priorities": ["high", "medium", "low"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting available services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

# Add router to main application
def get_cost_router():
    """Get the cost monitoring router"""
    return router