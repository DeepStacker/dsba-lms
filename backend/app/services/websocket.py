from fastapi import WebSocket
from typing import Dict, List
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.models import Exam, Attempt, AttemptStatus, ExamStatus

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = []
        self.active_connections[connection_id].append(websocket)
        logger.info(f"WebSocket connected: {connection_id}")
    
    def disconnect(self, websocket: WebSocket, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            if websocket in self.active_connections[connection_id]:
                self.active_connections[connection_id].remove(websocket)
            if not self.active_connections[connection_id]:
                del self.active_connections[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            for websocket in self.active_connections[connection_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {connection_id}: {str(e)}")
    
    async def broadcast_to_exam(self, message: str, exam_id: int):
        """Broadcast message to all connections for an exam"""
        exam_connections = [
            conn_id for conn_id in self.active_connections.keys()
            if conn_id.startswith(f"exam_{exam_id}_")
        ]
        
        for connection_id in exam_connections:
            await self.send_personal_message(message, connection_id)

class AutoSubmitService:
    """Service to automatically submit exams when time expires"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.running = False
        self.task = None
    
    async def start_monitoring(self):
        """Start the auto-submit monitoring service"""
        self.running = True
        self.task = asyncio.create_task(self._monitor_exams())
        logger.info("Auto-submit monitoring service started")
    
    def stop_monitoring(self):
        """Stop the auto-submit monitoring service"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Auto-submit monitoring service stopped")
    
    async def _monitor_exams(self):
        """Monitor exams and auto-submit expired attempts"""
        while self.running:
            try:
                await self._check_and_submit_expired_attempts()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-submit monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_and_submit_expired_attempts(self):
        """Check for expired attempts and auto-submit them"""
        now = datetime.utcnow()
        
        # Find exams that have ended but have active attempts
        query = """
            SELECT DISTINCT a.id, a.exam_id, a.student_id, e.end_at
            FROM attempts a
            JOIN exams e ON a.exam_id = e.id
            WHERE a.status = 'in_progress'
            AND e.end_at <= :now
            AND e.status IN ('started', 'ended')
        """
        
        result = await self.db.execute(query, {"now": now})
        expired_attempts = result.fetchall()
        
        for attempt_data in expired_attempts:
            try:
                # Update attempt to auto-submitted
                update_query = """
                    UPDATE attempts 
                    SET status = 'auto_submitted', 
                        submitted_at = :now,
                        autosubmitted = true
                    WHERE id = :attempt_id
                """
                
                await self.db.execute(update_query, {
                    "now": now,
                    "attempt_id": attempt_data.id
                })
                
                logger.info(f"Auto-submitted attempt {attempt_data.id} for exam {attempt_data.exam_id}")
                
            except Exception as e:
                logger.error(f"Error auto-submitting attempt {attempt_data.id}: {str(e)}")
        
        if expired_attempts:
            await self.db.commit()
    
    async def auto_submit_attempt(self, attempt_id: int):
        """Manually trigger auto-submit for a specific attempt"""
        try:
            now = datetime.utcnow()
            
            update_query = """
                UPDATE attempts 
                SET status = 'auto_submitted', 
                    submitted_at = :now,
                    autosubmitted = true
                WHERE id = :attempt_id
                AND status = 'in_progress'
            """
            
            result = await self.db.execute(update_query, {
                "now": now,
                "attempt_id": attempt_id
            })
            
            await self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Manually auto-submitted attempt {attempt_id}")
                return True
            else:
                logger.warning(f"Attempt {attempt_id} was not auto-submitted (may already be submitted)")
                return False
                
        except Exception as e:
            logger.error(f"Error manually auto-submitting attempt {attempt_id}: {str(e)}")
            return False