"""
Cost Monitoring Service for LegalSaathi - INTERNAL USE ONLY
Provides real-time tracking for all Google Cloud AI services with cost optimization.

SECURITY WARNING: This service tracks sensitive cost and usage data.
- Never expose cost data to end users
- Only use for internal administrative monitoring
- All endpoints require admin authentication
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.sqlite import insert
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()

class ServiceType(Enum):
    VERTEX_AI = "vertex_ai"
    GEMINI_API = "gemini_api"
    DOCUMENT_AI = "document_ai"
    NATURAL_LANGUAGE_AI = "natural_language_ai"
    TRANSLATION_API = "translation_api"
    VISION_API = "vision_api"
    SPEECH_API = "speech_api"

class OperationType(Enum):
    TEXT_GENERATION = "text_generation"
    DOCUMENT_PROCESSING = "document_processing"
    TRANSLATION = "translation"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    SPEECH_TO_TEXT = "speech_to_text"

@dataclass
class UsageMetrics:
    service: str
    operation: str
    tokens_used: int
    estimated_cost: float
    timestamp: datetime
    request_id: str
    user_id: Optional[str] = None
    model_name: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

@dataclass
class QuotaStatus:
    service: str
    current_usage: int
    quota_limit: int
    reset_time: datetime
    usage_percentage: float
    warning_threshold_reached: bool
    critical_threshold_reached: bool

@dataclass
class CostAnalytics:
    daily_cost: float
    monthly_cost: float
    service_breakdown: Dict[str, float]
    usage_trends: List[Dict[str, Any]]
    optimization_suggestions: List[str]
    cost_savings: float

# Database Models
class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(50), nullable=False, index=True)
    operation = Column(String(50), nullable=False)
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    request_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True)
    model_name = Column(String(100))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    request_metadata = Column(Text)  # JSON string for additional data

class QuotaTracking(Base):
    __tablename__ = "quota_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(50), nullable=False, unique=True, index=True)
    current_usage = Column(Integer, default=0)
    quota_limit = Column(Integer, nullable=False)
    reset_time = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    warning_sent = Column(Boolean, default=False)
    critical_warning_sent = Column(Boolean, default=False)

class CostAlert(Base):
    __tablename__ = "cost_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)  # quota_warning, cost_threshold, etc.
    service = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    threshold_value = Column(Float)
    current_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)

class CostMonitoringService:
    """
    Comprehensive cost monitoring service for Google Cloud AI services.
    Provides real-time tracking, quota monitoring, and cost optimization.
    """
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./cost_monitoring.db')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Initialize database
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize Redis for caching
        try:
            if self.redis_url.startswith('redis://'):
                self.redis_client = redis.from_url(self.redis_url)
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()  # Test connection
            self.cache_enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.redis_client = None
            self.cache_enabled = False
        
        # Cost configuration (per unit pricing)
        self.cost_config = {
            ServiceType.VERTEX_AI.value: {
                'gemini-pro': {'input': 0.000002, 'output': 0.000006},  # per token
                'gemini-pro-vision': {'input': 0.000002, 'output': 0.000006},
                'text-embedding-3-large': {'input': 0.00000013, 'output': 0},  # per token
            },
            ServiceType.GEMINI_API.value: {
                'gemini-pro': {'input': 0.000002, 'output': 0.000006},  # per token
                'gemini-pro-vision': {'input': 0.000002, 'output': 0.000006},
            },
            ServiceType.DOCUMENT_AI.value: {
                'process_document': 0.05,  # per page
            },
            ServiceType.NATURAL_LANGUAGE_AI.value: {
                'analyze_entities': 0.001,  # per 1000 characters
                'analyze_sentiment': 0.001,  # per 1000 characters
            },
            ServiceType.TRANSLATION_API.value: {
                'translate_text': 20.0,  # per million characters
            },
            ServiceType.VISION_API.value: {
                'detect_text': 1.50,  # per 1000 images
                'detect_labels': 1.50,  # per 1000 images
            },
            ServiceType.SPEECH_API.value: {
                'speech_to_text': 0.024,  # per minute
            }
        }
        
        # Quota limits (default values, should be configured per project)
        self.quota_limits = {
            ServiceType.VERTEX_AI.value: 1000000,  # tokens per day
            ServiceType.GEMINI_API.value: 500000,   # tokens per day
            ServiceType.DOCUMENT_AI.value: 1000,    # pages per day
            ServiceType.NATURAL_LANGUAGE_AI.value: 5000000,  # characters per day
            ServiceType.TRANSLATION_API.value: 10000000,     # characters per day
            ServiceType.VISION_API.value: 1000,     # images per day
            ServiceType.SPEECH_API.value: 1000,     # minutes per day
        }
        
        # Alert thresholds
        self.warning_threshold = 0.8  # 80%
        self.critical_threshold = 0.95  # 95%
        
        # Cost alert thresholds (daily)
        self.daily_cost_threshold = 50.0  # $50 per day
        self.monthly_cost_threshold = 1000.0  # $1000 per month
        
        logger.info("Cost Monitoring Service initialized")
    
    def get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def track_api_usage(
        self,
        service: str,
        operation: str,
        tokens: int = 0,
        request_id: str = None,
        user_id: str = None,
        model_name: str = None,
        input_tokens: int = None,
        output_tokens: int = None,
        pages: int = 0,
        characters: int = 0,
        images: int = 0,
        minutes: float = 0,
        metadata: Dict[str, Any] = None
    ) -> UsageMetrics:
        """
        Track API usage and calculate costs
        """
        try:
            # Calculate cost based on service and operation
            estimated_cost = self._calculate_cost(
                service, operation, tokens, pages, characters, images, minutes,
                model_name, input_tokens, output_tokens
            )
            
            # Create usage metrics
            usage_metrics = UsageMetrics(
                service=service,
                operation=operation,
                tokens_used=tokens,
                estimated_cost=estimated_cost,
                timestamp=datetime.utcnow(),
                request_id=request_id or self._generate_request_id(),
                user_id=user_id,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Store in database
            await self._store_usage_metrics(usage_metrics, metadata)
            
            # Update quota tracking
            await self._update_quota_tracking(service, tokens, pages, characters, images, minutes)
            
            # Check for alerts
            await self._check_cost_alerts(service, estimated_cost)
            
            # Cache recent usage for quick access
            if self.cache_enabled:
                await self._cache_usage_metrics(usage_metrics)
            
            logger.debug(f"Tracked usage: {service}/{operation} - ${estimated_cost:.6f}")
            
            return usage_metrics
            
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
            # Return minimal metrics on error
            return UsageMetrics(
                service=service,
                operation=operation,
                tokens_used=tokens,
                estimated_cost=0.0,
                timestamp=datetime.utcnow(),
                request_id=request_id or self._generate_request_id()
            )
    
    def _calculate_cost(
        self,
        service: str,
        operation: str,
        tokens: int,
        pages: int,
        characters: int,
        images: int,
        minutes: float,
        model_name: str = None,
        input_tokens: int = None,
        output_tokens: int = None
    ) -> float:
        """Calculate cost based on service and usage"""
        try:
            service_config = self.cost_config.get(service, {})
            
            if service in [ServiceType.VERTEX_AI.value, ServiceType.GEMINI_API.value]:
                # Token-based pricing
                model_config = service_config.get(model_name or 'gemini-pro', {})
                input_cost = (input_tokens or tokens) * model_config.get('input', 0)
                output_cost = (output_tokens or 0) * model_config.get('output', 0)
                return input_cost + output_cost
            
            elif service == ServiceType.DOCUMENT_AI.value:
                # Page-based pricing
                return pages * service_config.get(operation, 0.05)
            
            elif service == ServiceType.NATURAL_LANGUAGE_AI.value:
                # Character-based pricing (per 1000 characters)
                return (characters / 1000) * service_config.get(operation, 0.001)
            
            elif service == ServiceType.TRANSLATION_API.value:
                # Character-based pricing (per million characters)
                return (characters / 1000000) * service_config.get(operation, 20.0)
            
            elif service == ServiceType.VISION_API.value:
                # Image-based pricing (per 1000 images)
                return (images / 1000) * service_config.get(operation, 1.50)
            
            elif service == ServiceType.SPEECH_API.value:
                # Time-based pricing (per minute)
                return minutes * service_config.get(operation, 0.024)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return 0.0
    
    async def _store_usage_metrics(self, metrics: UsageMetrics, metadata: Dict[str, Any] = None):
        """Store usage metrics in database"""
        try:
            db = self.get_db()
            try:
                usage_record = APIUsage(
                    service=metrics.service,
                    operation=metrics.operation,
                    tokens_used=metrics.tokens_used,
                    estimated_cost=metrics.estimated_cost,
                    timestamp=metrics.timestamp,
                    request_id=metrics.request_id,
                    user_id=metrics.user_id,
                    model_name=metrics.model_name,
                    input_tokens=metrics.input_tokens,
                    output_tokens=metrics.output_tokens,
                    request_metadata=json.dumps(metadata) if metadata else None
                )
                
                db.add(usage_record)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing usage metrics: {e}")
    
    async def _update_quota_tracking(
        self,
        service: str,
        tokens: int,
        pages: int,
        characters: int,
        images: int,
        minutes: float
    ):
        """Update quota tracking for service"""
        try:
            db = self.get_db()
            try:
                # Calculate usage units based on service type
                usage_units = self._calculate_usage_units(service, tokens, pages, characters, images, minutes)
                
                # Get or create quota tracking record
                quota_record = db.query(QuotaTracking).filter(
                    QuotaTracking.service == service
                ).first()
                
                if not quota_record:
                    # Create new quota tracking record
                    quota_record = QuotaTracking(
                        service=service,
                        current_usage=usage_units,
                        quota_limit=self.quota_limits.get(service, 1000000),
                        reset_time=self._get_next_reset_time(),
                        last_updated=datetime.utcnow()
                    )
                    db.add(quota_record)
                else:
                    # Update existing record
                    if datetime.utcnow() > quota_record.reset_time:
                        # Reset quota if time has passed
                        quota_record.current_usage = usage_units
                        quota_record.reset_time = self._get_next_reset_time()
                        quota_record.warning_sent = False
                        quota_record.critical_warning_sent = False
                    else:
                        # Add to current usage
                        quota_record.current_usage += usage_units
                    
                    quota_record.last_updated = datetime.utcnow()
                
                db.commit()
                
                # Check for quota warnings
                await self._check_quota_warnings(quota_record)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating quota tracking: {e}")
    
    def _calculate_usage_units(
        self,
        service: str,
        tokens: int,
        pages: int,
        characters: int,
        images: int,
        minutes: float
    ) -> int:
        """Calculate usage units for quota tracking"""
        if service in [ServiceType.VERTEX_AI.value, ServiceType.GEMINI_API.value]:
            return tokens
        elif service == ServiceType.DOCUMENT_AI.value:
            return pages
        elif service in [ServiceType.NATURAL_LANGUAGE_AI.value, ServiceType.TRANSLATION_API.value]:
            return characters
        elif service == ServiceType.VISION_API.value:
            return images
        elif service == ServiceType.SPEECH_API.value:
            return int(minutes)
        return 0
    
    def _get_next_reset_time(self) -> datetime:
        """Get next quota reset time (daily reset)"""
        now = datetime.utcnow()
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    async def _check_quota_warnings(self, quota_record: QuotaTracking):
        """Check and send quota warnings if needed"""
        try:
            usage_percentage = (quota_record.current_usage / quota_record.quota_limit) * 100
            
            # Check critical threshold (95%)
            if usage_percentage >= (self.critical_threshold * 100) and not quota_record.critical_warning_sent:
                await self._send_quota_alert(
                    quota_record.service,
                    "critical",
                    usage_percentage,
                    quota_record.current_usage,
                    quota_record.quota_limit
                )
                quota_record.critical_warning_sent = True
                
                # Update database
                db = self.get_db()
                try:
                    db.merge(quota_record)
                    db.commit()
                finally:
                    db.close()
            
            # Check warning threshold (80%)
            elif usage_percentage >= (self.warning_threshold * 100) and not quota_record.warning_sent:
                await self._send_quota_alert(
                    quota_record.service,
                    "warning",
                    usage_percentage,
                    quota_record.current_usage,
                    quota_record.quota_limit
                )
                quota_record.warning_sent = True
                
                # Update database
                db = self.get_db()
                try:
                    db.merge(quota_record)
                    db.commit()
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error checking quota warnings: {e}")
    
    async def _send_quota_alert(
        self,
        service: str,
        alert_type: str,
        usage_percentage: float,
        current_usage: int,
        quota_limit: int
    ):
        """Send quota alert notification"""
        try:
            message = f"Quota {alert_type} for {service}: {usage_percentage:.1f}% used ({current_usage}/{quota_limit})"
            
            # Store alert in database
            db = self.get_db()
            try:
                alert = CostAlert(
                    alert_type=f"quota_{alert_type}",
                    service=service,
                    message=message,
                    threshold_value=self.critical_threshold if alert_type == "critical" else self.warning_threshold,
                    current_value=usage_percentage / 100,
                    timestamp=datetime.utcnow(),
                    resolved=False,
                    notification_sent=False
                )
                db.add(alert)
                db.commit()
                
                # Send email notification
                await self._send_email_alert(alert_type, service, message, usage_percentage)
                
                # Update notification sent status
                alert.notification_sent = True
                db.commit()
                
                logger.warning(f"QUOTA ALERT: {message}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error sending quota alert: {e}")
    
    async def _check_cost_alerts(self, service: str, cost: float):
        """Check for cost threshold alerts"""
        try:
            # Get daily cost for service
            daily_cost = await self.get_daily_cost(service)
            
            if daily_cost > self.daily_cost_threshold:
                await self._send_cost_alert(service, "daily", daily_cost, self.daily_cost_threshold)
            
            # Get monthly cost for service
            monthly_cost = await self.get_monthly_cost(service)
            
            if monthly_cost > self.monthly_cost_threshold:
                await self._send_cost_alert(service, "monthly", monthly_cost, self.monthly_cost_threshold)
                
        except Exception as e:
            logger.error(f"Error checking cost alerts: {e}")
    
    async def _send_cost_alert(self, service: str, period: str, current_cost: float, threshold: float):
        """Send cost threshold alert"""
        try:
            message = f"Cost threshold exceeded for {service}: ${current_cost:.2f} ({period} threshold: ${threshold:.2f})"
            
            # Store alert in database
            db = self.get_db()
            try:
                alert = CostAlert(
                    alert_type=f"cost_{period}",
                    service=service,
                    message=message,
                    threshold_value=threshold,
                    current_value=current_cost,
                    timestamp=datetime.utcnow(),
                    resolved=False,
                    notification_sent=False
                )
                db.add(alert)
                db.commit()
                
                # Send email notification
                await self._send_email_alert(f"cost_{period}", service, message, current_cost)
                
                # Update notification sent status
                alert.notification_sent = True
                db.commit()
                
                logger.warning(f"COST ALERT: {message}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error sending cost alert: {e}")
    
    async def _cache_usage_metrics(self, metrics: UsageMetrics):
        """Cache usage metrics for quick access"""
        try:
            if not self.cache_enabled:
                return
            
            cache_key = f"usage:{metrics.service}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
            else:
                data = {"total_cost": 0.0, "total_tokens": 0, "request_count": 0}
            
            data["total_cost"] += metrics.estimated_cost
            data["total_tokens"] += metrics.tokens_used
            data["request_count"] += 1
            data["last_updated"] = metrics.timestamp.isoformat()
            
            # Cache for 25 hours (expires next day)
            self.redis_client.setex(cache_key, 90000, json.dumps(data))
            
        except Exception as e:
            logger.error(f"Error caching usage metrics: {e}")
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.utcnow()) % 10000:04d}"
    
    async def get_quota_status(self, service: str) -> QuotaStatus:
        """Get current quota status for service"""
        try:
            db = self.get_db()
            try:
                quota_record = db.query(QuotaTracking).filter(
                    QuotaTracking.service == service
                ).first()
                
                if not quota_record:
                    # Return default quota status
                    return QuotaStatus(
                        service=service,
                        current_usage=0,
                        quota_limit=self.quota_limits.get(service, 1000000),
                        reset_time=self._get_next_reset_time(),
                        usage_percentage=0.0,
                        warning_threshold_reached=False,
                        critical_threshold_reached=False
                    )
                
                usage_percentage = (quota_record.current_usage / quota_record.quota_limit) * 100
                
                return QuotaStatus(
                    service=service,
                    current_usage=quota_record.current_usage,
                    quota_limit=quota_record.quota_limit,
                    reset_time=quota_record.reset_time,
                    usage_percentage=usage_percentage,
                    warning_threshold_reached=usage_percentage >= (self.warning_threshold * 100),
                    critical_threshold_reached=usage_percentage >= (self.critical_threshold * 100)
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting quota status: {e}")
            return QuotaStatus(
                service=service,
                current_usage=0,
                quota_limit=self.quota_limits.get(service, 1000000),
                reset_time=self._get_next_reset_time(),
                usage_percentage=0.0,
                warning_threshold_reached=False,
                critical_threshold_reached=False
            )
    
    async def get_daily_cost(self, service: str = None) -> float:
        """Get daily cost for service or all services"""
        try:
            if self.cache_enabled and service:
                # Try to get from cache first
                cache_key = f"usage:{service}:{datetime.utcnow().strftime('%Y-%m-%d')}"
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return data.get("total_cost", 0.0)
            
            # Get from database
            db = self.get_db()
            try:
                today = datetime.utcnow().date()
                query = db.query(APIUsage).filter(
                    APIUsage.timestamp >= today,
                    APIUsage.timestamp < today + timedelta(days=1)
                )
                
                if service:
                    query = query.filter(APIUsage.service == service)
                
                total_cost = sum(record.estimated_cost for record in query.all())
                return total_cost
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting daily cost: {e}")
            return 0.0
    
    async def get_monthly_cost(self, service: str = None) -> float:
        """Get monthly cost for service or all services"""
        try:
            db = self.get_db()
            try:
                now = datetime.utcnow()
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                query = db.query(APIUsage).filter(
                    APIUsage.timestamp >= month_start
                )
                
                if service:
                    query = query.filter(APIUsage.service == service)
                
                total_cost = sum(record.estimated_cost for record in query.all())
                return total_cost
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting monthly cost: {e}")
            return 0.0
    
    async def get_api_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get API usage statistics for dashboard"""
        try:
            db = self.get_db()
            try:
                # Get data for the specified period
                start_date = datetime.utcnow() - timedelta(days=days)
                records = db.query(APIUsage).filter(
                    APIUsage.timestamp >= start_date
                ).all()
                
                # Calculate usage statistics by service
                service_stats = {}
                for record in records:
                    if record.service not in service_stats:
                        service_stats[record.service] = {
                            'total_requests': 0,
                            'total_tokens': 0,
                            'total_cost': 0.0,
                            'avg_cost_per_request': 0.0,
                            'last_used': None,
                            'models_used': set(),
                            'operations': set()
                        }
                    
                    stats = service_stats[record.service]
                    stats['total_requests'] += 1
                    stats['total_tokens'] += record.tokens_used or 0
                    stats['total_cost'] += record.estimated_cost
                    
                    if record.model_name:
                        stats['models_used'].add(record.model_name)
                    if record.operation:
                        stats['operations'].add(record.operation)
                    
                    if not stats['last_used'] or record.timestamp > stats['last_used']:
                        stats['last_used'] = record.timestamp
                
                # Calculate averages and convert sets to lists
                for service, stats in service_stats.items():
                    if stats['total_requests'] > 0:
                        stats['avg_cost_per_request'] = stats['total_cost'] / stats['total_requests']
                    stats['models_used'] = list(stats['models_used'])
                    stats['operations'] = list(stats['operations'])
                    if stats['last_used']:
                        stats['last_used'] = stats['last_used'].isoformat()
                
                # Get daily usage trends
                daily_usage = {}
                for i in range(days):
                    date = (datetime.utcnow() - timedelta(days=i)).date()
                    day_records = [r for r in records if r.timestamp.date() == date]
                    daily_usage[date.isoformat()] = {
                        'requests': len(day_records),
                        'cost': sum(r.estimated_cost for r in day_records),
                        'tokens': sum(r.tokens_used or 0 for r in day_records)
                    }
                
                return {
                    'service_stats': service_stats,
                    'daily_usage': daily_usage,
                    'total_requests': len(records),
                    'total_cost': sum(r.estimated_cost for r in records),
                    'period_days': days,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {
                'service_stats': {},
                'daily_usage': {},
                'total_requests': 0,
                'total_cost': 0.0,
                'period_days': days,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    async def get_cost_analytics(self, days: int = 30) -> CostAnalytics:
        """Get comprehensive cost analytics"""
        try:
            db = self.get_db()
            try:
                # Get data for the specified period
                start_date = datetime.utcnow() - timedelta(days=days)
                records = db.query(APIUsage).filter(
                    APIUsage.timestamp >= start_date
                ).all()
                
                # Calculate daily and monthly costs
                daily_cost = await self.get_daily_cost()
                monthly_cost = await self.get_monthly_cost()
                
                # Service breakdown
                service_breakdown = {}
                for record in records:
                    service_breakdown[record.service] = service_breakdown.get(record.service, 0) + record.estimated_cost
                
                # Usage trends (daily aggregation)
                usage_trends = []
                for i in range(days):
                    date = (datetime.utcnow() - timedelta(days=i)).date()
                    day_records = [r for r in records if r.timestamp.date() == date]
                    day_cost = sum(r.estimated_cost for r in day_records)
                    day_requests = len(day_records)
                    
                    usage_trends.append({
                        "date": date.isoformat(),
                        "cost": day_cost,
                        "requests": day_requests
                    })
                
                # Generate optimization suggestions
                optimization_suggestions = await self._generate_optimization_suggestions(records, service_breakdown)
                
                # Calculate potential cost savings
                cost_savings = await self._calculate_potential_savings(records)
                
                return CostAnalytics(
                    daily_cost=daily_cost,
                    monthly_cost=monthly_cost,
                    service_breakdown=service_breakdown,
                    usage_trends=usage_trends,
                    optimization_suggestions=optimization_suggestions,
                    cost_savings=cost_savings
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting cost analytics: {e}")
            return CostAnalytics(
                daily_cost=0.0,
                monthly_cost=0.0,
                service_breakdown={},
                usage_trends=[],
                optimization_suggestions=[],
                cost_savings=0.0
            )
    
    async def _generate_optimization_suggestions(
        self,
        records: List[APIUsage],
        service_breakdown: Dict[str, float]
    ) -> List[str]:
        """Generate cost optimization suggestions"""
        suggestions = []
        
        try:
            # Analyze service usage patterns
            total_cost = sum(service_breakdown.values())
            
            if total_cost == 0:
                return ["No usage data available for optimization analysis"]
            
            # Check for high-cost services
            for service, cost in service_breakdown.items():
                percentage = (cost / total_cost) * 100
                if percentage > 50:
                    suggestions.append(f"Consider optimizing {service} usage - accounts for {percentage:.1f}% of total cost")
            
            # Check for caching opportunities
            duplicate_requests = self._find_duplicate_requests(records)
            if duplicate_requests > 0:
                potential_savings = duplicate_requests * 0.001  # Rough estimate
                suggestions.append(f"Enable intelligent caching - could save ~${potential_savings:.2f} from {duplicate_requests} duplicate requests")
            
            # Check for model optimization opportunities
            vertex_ai_records = [r for r in records if r.service == ServiceType.VERTEX_AI.value]
            if len(vertex_ai_records) > 100:
                suggestions.append("Consider using smaller models for simple queries to reduce Vertex AI costs")
            
            # Check for batch processing opportunities
            small_requests = [r for r in records if r.tokens_used < 100]
            if len(small_requests) > 50:
                suggestions.append("Consider batching small requests to improve cost efficiency")
            
            # Check for quota optimization
            for service in service_breakdown.keys():
                quota_status = await self.get_quota_status(service)
                if quota_status.usage_percentage < 20:
                    suggestions.append(f"Consider reducing quota limits for {service} - currently using only {quota_status.usage_percentage:.1f}%")
            
            if not suggestions:
                suggestions.append("Current usage patterns are well optimized")
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            suggestions.append("Unable to generate optimization suggestions due to analysis error")
        
        return suggestions
    
    def _find_duplicate_requests(self, records: List[APIUsage]) -> int:
        """Find potential duplicate requests that could be cached"""
        try:
            # Simple heuristic: requests with same service, operation, and similar token count within short time window
            duplicates = 0
            processed = set()
            
            for i, record in enumerate(records):
                if i in processed:
                    continue
                
                # Look for similar requests within 1 hour
                similar_requests = []
                for j, other_record in enumerate(records[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    time_diff = abs((record.timestamp - other_record.timestamp).total_seconds())
                    token_diff = abs(record.tokens_used - other_record.tokens_used)
                    
                    if (record.service == other_record.service and
                        record.operation == other_record.operation and
                        time_diff < 3600 and  # Within 1 hour
                        token_diff < 50):     # Similar token count
                        similar_requests.append(j)
                
                if similar_requests:
                    duplicates += len(similar_requests)
                    processed.update(similar_requests)
                    processed.add(i)
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding duplicate requests: {e}")
            return 0
    
    async def _calculate_potential_savings(self, records: List[APIUsage]) -> float:
        """Calculate potential cost savings from optimization"""
        try:
            # Calculate savings from caching duplicate requests
            duplicate_requests = self._find_duplicate_requests(records)
            duplicate_cost = sum(r.estimated_cost for r in records[:duplicate_requests])
            
            # Calculate savings from model optimization (assume 20% savings on large requests)
            large_requests = [r for r in records if r.tokens_used > 1000]
            model_optimization_savings = sum(r.estimated_cost for r in large_requests) * 0.2
            
            # Calculate savings from batch processing (assume 10% savings on small requests)
            small_requests = [r for r in records if r.tokens_used < 100]
            batch_processing_savings = sum(r.estimated_cost for r in small_requests) * 0.1
            
            total_savings = duplicate_cost + model_optimization_savings + batch_processing_savings
            return total_savings
            
        except Exception as e:
            logger.error(f"Error calculating potential savings: {e}")
            return 0.0
    
    async def optimize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize API request for cost efficiency"""
        try:
            optimized_request = request_data.copy()
            
            # Check cache for similar requests
            if self.cache_enabled:
                cache_key = self._generate_cache_key(request_data)
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info("Request served from cache, cost saved")
                    return json.loads(cached_result)
            
            # Optimize model selection based on complexity
            if 'model' in request_data and 'query' in request_data:
                query_complexity = len(request_data['query'].split())
                if query_complexity < 20:  # Simple query
                    optimized_request['model'] = 'gemini-pro'  # Use smaller model
                else:
                    optimized_request['model'] = 'gemini-pro'  # Use appropriate model
            
            # Optimize token limits
            if 'max_tokens' in request_data:
                # Reduce max tokens for simple queries
                query_length = len(request_data.get('query', ''))
                if query_length < 100:
                    optimized_request['max_tokens'] = min(request_data['max_tokens'], 500)
            
            return optimized_request
            
        except Exception as e:
            logger.error(f"Error optimizing request: {e}")
            return request_data
    
    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        try:
            # Create hash of relevant request parameters
            cache_data = {
                'service': request_data.get('service'),
                'operation': request_data.get('operation'),
                'query': request_data.get('query', ''),
                'model': request_data.get('model')
            }
            
            cache_string = json.dumps(cache_data, sort_keys=True)
            cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
            return f"request_cache:{cache_hash}"
            
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"request_cache:error_{datetime.utcnow().timestamp()}"
    
    async def _send_email_alert(self, alert_type: str, service: str, message: str, value: float):
        """Send email alert notification"""
        try:
            # Get admin email from environment
            admin_email = os.getenv('COST_ALERT_EMAIL')
            if not admin_email:
                logger.warning("No COST_ALERT_EMAIL configured, skipping email notification")
                return
            
            # Import email service
            try:
                from services.smtp_email_service import SMTPEmailService
                email_service = SMTPEmailService()
                
                if not email_service.is_available():
                    logger.warning("Email service not configured, skipping email notification")
                    return
                
                # Prepare email content
                subject = f"LegalSaathi Cost Alert: {alert_type.replace('_', ' ').title()}"
                
                html_body = f"""
                <html>
                <body>
                    <h2>Cost Monitoring Alert</h2>
                    <p><strong>Service:</strong> {service.replace('_', ' ').title()}</p>
                    <p><strong>Alert Type:</strong> {alert_type.replace('_', ' ').title()}</p>
                    <p><strong>Message:</strong> {message}</p>
                    <p><strong>Current Value:</strong> {value}</p>
                    <p><strong>Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    
                    <h3>Recommended Actions:</h3>
                    <ul>
                        <li>Review current API usage patterns</li>
                        <li>Check for any unusual activity</li>
                        <li>Consider implementing additional rate limiting</li>
                        <li>Review cost optimization suggestions in the dashboard</li>
                    </ul>
                    
                    <p>This is an automated alert from the LegalSaathi cost monitoring system.</p>
                </body>
                </html>
                """
                
                # Send email using SMTP service
                # Note: This is a simplified integration - in production, you'd use the proper email models
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = email_service.sender_email
                msg['To'] = admin_email
                
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
                
                # Send email
                with smtplib.SMTP(email_service.smtp_server, email_service.smtp_port) as server:
                    server.starttls()
                    server.login(email_service.sender_email, email_service.sender_password)
                    server.send_message(msg)
                
                logger.info(f"Cost alert email sent to {admin_email}")
                
            except ImportError:
                logger.warning("Email service not available, skipping email notification")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
                
        except Exception as e:
            logger.error(f"Error in email alert system: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of cost monitoring system"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {}
            }
            
            # Check database connection
            try:
                db = self.get_db()
                try:
                    # Test database connection with a simple query
                    result = db.execute(text("SELECT 1")).fetchone()
                    if result and result[0] == 1:
                        health_status["components"]["database"] = {"status": "healthy"}
                    else:
                        health_status["components"]["database"] = {"status": "unhealthy", "error": "Database query returned unexpected result"}
                        health_status["status"] = "degraded"
                finally:
                    db.close()
            except Exception as e:
                health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check Redis connection
            try:
                if self.cache_enabled:
                    self.redis_client.ping()
                    health_status["components"]["cache"] = {"status": "healthy"}
                else:
                    health_status["components"]["cache"] = {"status": "disabled"}
            except Exception as e:
                health_status["components"]["cache"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check recent activity
            try:
                recent_usage = await self.get_daily_cost()
                health_status["components"]["monitoring"] = {
                    "status": "healthy",
                    "daily_cost": recent_usage
                }
            except Exception as e:
                health_status["components"]["monitoring"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Global instance
cost_monitor = CostMonitoringService()