"""
Email rate limiting middleware for user-based email restrictions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmailRateLimiter:
    """Rate limiter for email sending per user"""
    
    def __init__(self):
        self.user_limits = defaultdict(lambda: {
            'hourly_count': 0,
            'hourly_reset': datetime.now() + timedelta(hours=1),
            'daily_count': 0,
            'daily_reset': datetime.now() + timedelta(days=1)
        })
        self.hourly_limit = 5
        self.daily_limit = 50
    
    def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded rate limits"""
        now = datetime.now()
        user_data = self.user_limits[user_id]
        
        # Reset counters if time has passed
        if now >= user_data['hourly_reset']:
            user_data['hourly_count'] = 0
            user_data['hourly_reset'] = now + timedelta(hours=1)
        
        if now >= user_data['daily_reset']:
            user_data['daily_count'] = 0
            user_data['daily_reset'] = now + timedelta(days=1)
        
        # Check if rate limited
        is_rate_limited = (
            user_data['hourly_count'] >= self.hourly_limit or 
            user_data['daily_count'] >= self.daily_limit
        )
        
        return {
            'user_id': user_id,
            'emails_sent_today': user_data['daily_count'],
            'emails_sent_this_hour': user_data['hourly_count'],
            'daily_limit': self.daily_limit,
            'hourly_limit': self.hourly_limit,
            'next_reset_time': min(user_data['hourly_reset'], user_data['daily_reset']),
            'is_rate_limited': is_rate_limited
        }
    
    def increment_counter(self, user_id: str):
        """Increment email counter for user"""
        user_data = self.user_limits[user_id]
        user_data['hourly_count'] += 1
        user_data['daily_count'] += 1
        logger.info(f"Email counter incremented for user {user_id}: hourly={user_data['hourly_count']}, daily={user_data['daily_count']}")
    
    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until user can send another email"""
        user_data = self.user_limits[user_id]
        now = datetime.now()
        
        if user_data['hourly_count'] >= self.hourly_limit:
            return int((user_data['hourly_reset'] - now).total_seconds())
        elif user_data['daily_count'] >= self.daily_limit:
            return int((user_data['daily_reset'] - now).total_seconds())
        
        return 0
    
    def reset_user_limits(self, user_id: str):
        """Reset limits for a specific user (admin function)"""
        if user_id in self.user_limits:
            del self.user_limits[user_id]
            logger.info(f"Rate limits reset for user {user_id}")
    
    def get_all_user_stats(self) -> Dict[str, Any]:
        """Get statistics for all users (admin function)"""
        stats = {}
        for user_id, data in self.user_limits.items():
            stats[user_id] = {
                'hourly_count': data['hourly_count'],
                'daily_count': data['daily_count'],
                'hourly_reset': data['hourly_reset'].isoformat(),
                'daily_reset': data['daily_reset'].isoformat()
            }
        return stats


# Global instance
email_rate_limiter = EmailRateLimiter()