"""
Consolidated Expert Services
Combines expert authentication, queue management, PDF generation, and review tracking
"""

import os
import logging
import uuid
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class ExpertServices:
    """Consolidated expert services for authentication, queue, and review management"""
    
    def __init__(self):
        self.is_cloud_run = os.getenv('GOOGLE_CLOUD_DEPLOYMENT', 'false').lower() == 'true'
        self.db_path = "expert_queue.db" if not self.is_cloud_run else ":memory:"
        self._init_database()
        logger.info("✅ Expert services initialized")
    
    def _init_database(self):
        """Initialize expert database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS expert_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        review_id TEXT UNIQUE NOT NULL,
                        user_email TEXT NOT NULL,
                        document_type TEXT,
                        status TEXT DEFAULT 'pending',
                        expert_id TEXT,
                        expert_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS experts (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        specialty TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default experts for demo
                experts = [
                    ('expert_1', 'Sarah Chen', 'sarah.chen@legalsaathi.com', 'Contract Law'),
                    ('expert_2', 'Michael Rodriguez', 'michael.rodriguez@legalsaathi.com', 'Real Estate Law'),
                    ('expert_3', 'Dr. Priya Sharma', 'priya.sharma@legalsaathi.com', 'Corporate Law')
                ]
                
                conn.executemany("""
                    INSERT OR IGNORE INTO experts (id, name, email, specialty)
                    VALUES (?, ?, ?, ?)
                """, experts)
                
                conn.commit()
                logger.info("Expert database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize expert database: {e}")
    
    # Expert Authentication
    async def authenticate_expert(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate expert user"""
        try:
            email = credentials.get('email', '').lower()
            password = credentials.get('password', '')
            
            # Simple authentication for demo (in production, use proper auth)
            if email.endswith('@legalsaathi.com') and password == 'expert123':
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT id, name, specialty FROM experts WHERE email = ?",
                        (email,)
                    )
                    expert = cursor.fetchone()
                    
                    if expert:
                        return {
                            "success": True,
                            "expert": {
                                "id": expert[0],
                                "name": expert[1],
                                "email": email,
                                "specialty": expert[2]
                            },
                            "token": f"expert_token_{expert[0]}"
                        }
            
            return {"success": False, "error": "Invalid credentials"}
            
        except Exception as e:
            logger.error(f"Expert authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Queue Management
    async def get_expert_queue(self, expert_id: str, status_filter: str = None) -> Dict[str, Any]:
        """Get expert review queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM expert_reviews WHERE expert_id = ? OR expert_id IS NULL"
                params = [expert_id]
                
                if status_filter:
                    query += " AND status = ?"
                    params.append(status_filter)
                
                query += " ORDER BY created_at DESC LIMIT 50"
                
                cursor = conn.execute(query, params)
                reviews = cursor.fetchall()
                
                return {
                    "success": True,
                    "reviews": [
                        {
                            "id": review[0],
                            "review_id": review[1],
                            "user_email": review[2],
                            "document_type": review[3],
                            "status": review[4],
                            "expert_id": review[5],
                            "expert_notes": review[6],
                            "created_at": review[7],
                            "updated_at": review[8]
                        }
                        for review in reviews
                    ],
                    "total": len(reviews)
                }
                
        except Exception as e:
            logger.error(f"Failed to get expert queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def assign_review_to_expert(self, review_id: str, expert_id: str) -> Dict[str, Any]:
        """Assign review to expert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE expert_reviews 
                    SET expert_id = ?, status = 'assigned', updated_at = CURRENT_TIMESTAMP
                    WHERE review_id = ?
                """, (expert_id, review_id))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Review {review_id} assigned to expert {expert_id}"
                }
                
        except Exception as e:
            logger.error(f"Failed to assign review: {e}")
            return {"success": False, "error": str(e)}
    
    # Review Management
    async def submit_expert_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit expert review"""
        try:
            review_id = review_data.get('review_id')
            expert_id = review_data.get('expert_id')
            expert_notes = review_data.get('expert_notes', '')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE expert_reviews 
                    SET expert_notes = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE review_id = ? AND expert_id = ?
                """, (expert_notes, review_id, expert_id))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Expert review submitted for {review_id}"
                }
                
        except Exception as e:
            logger.error(f"Failed to submit expert review: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_review_request(self, user_email: str, document_type: str = "general") -> Dict[str, Any]:
        """Create a new review request"""
        try:
            review_id = f"review_{uuid.uuid4().hex[:8]}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO expert_reviews (review_id, user_email, document_type, status)
                    VALUES (?, ?, ?, 'pending')
                """, (review_id, user_email.lower(), document_type))
                
                conn.commit()
                
                return {
                    "success": True,
                    "review_id": review_id,
                    "message": "Review request created successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to create review request: {e}")
            return {"success": False, "error": str(e)}
    
    # PDF Generation (simplified)
    async def generate_expert_report_pdf(self, review_data: Dict[str, Any]) -> bytes:
        """Generate PDF report for expert review"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import io
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Add content to PDF
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, height - 100, "Expert Review Report")
            
            p.setFont("Helvetica", 12)
            y_position = height - 140
            
            for key, value in review_data.items():
                p.drawString(100, y_position, f"{key}: {value}")
                y_position -= 20
                if y_position < 100:
                    p.showPage()
                    y_position = height - 100
            
            p.save()
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            return b""


# Global instance
expert_services = ExpertServices()