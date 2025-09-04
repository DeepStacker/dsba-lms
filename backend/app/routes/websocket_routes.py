from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User, Exam, Attempt, Response, ProctorLog, ProctorEventType, AttemptStatus

router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        # exam_id -> List[WebSocket connections]
        self.exam_connections: Dict[int, List[WebSocket]] = {}
        # attempt_id -> WebSocket connection
        self.student_connections: Dict[int, WebSocket] = {}
        # teacher monitoring connections
        self.teacher_connections: Dict[int, List[WebSocket]] = {}

    async def connect_student(self, websocket: WebSocket, attempt_id: int):
        """Connect a student to their exam attempt"""
        await websocket.accept()
        self.student_connections[attempt_id] = websocket

    async def connect_teacher(self, websocket: WebSocket, exam_id: int):
        """Connect a teacher to monitor an exam"""
        await websocket.accept()
        if exam_id not in self.teacher_connections:
            self.teacher_connections[exam_id] = []
        self.teacher_connections[exam_id].append(websocket)

    def disconnect_student(self, attempt_id: int):
        """Disconnect a student"""
        if attempt_id in self.student_connections:
            del self.student_connections[attempt_id]

    def disconnect_teacher(self, websocket: WebSocket, exam_id: int):
        """Disconnect a teacher"""
        if exam_id in self.teacher_connections:
            if websocket in self.teacher_connections[exam_id]:
                self.teacher_connections[exam_id].remove(websocket)
            if not self.teacher_connections[exam_id]:
                del self.teacher_connections[exam_id]

    async def send_to_student(self, attempt_id: int, message: dict):
        """Send message to a specific student"""
        if attempt_id in self.student_connections:
            try:
                await self.student_connections[attempt_id].send_text(json.dumps(message))
            except:
                self.disconnect_student(attempt_id)

    async def send_to_teachers(self, exam_id: int, message: dict):
        """Send message to all teachers monitoring an exam"""
        if exam_id in self.teacher_connections:
            disconnected = []
            for websocket in self.teacher_connections[exam_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected connections
            for ws in disconnected:
                self.teacher_connections[exam_id].remove(ws)

    async def broadcast_exam_update(self, exam_id: int, message: dict):
        """Broadcast update to all connections for an exam"""
        await self.send_to_teachers(exam_id, message)

manager = ConnectionManager()

# ==================== STUDENT EXAM WEBSOCKET ====================

@router.websocket("/exam/{exam_id}/attempt/{attempt_id}")
async def student_exam_websocket(
    websocket: WebSocket,
    exam_id: int,
    attempt_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for student exam taking"""
    try:
        # Verify token and get user (simplified - in production use proper JWT verification)
        # For now, we'll skip token verification and assume valid connection
        
        # Verify attempt exists and belongs to the exam
        attempt_result = await db.execute(
            select(Attempt, Exam)
            .join(Exam, Attempt.exam_id == Exam.id)
            .where(
                and_(
                    Attempt.id == attempt_id,
                    Attempt.exam_id == exam_id,
                    Attempt.status == AttemptStatus.IN_PROGRESS
                )
            )
        )
        
        attempt_data = attempt_result.first()
        if not attempt_data:
            await websocket.close(code=4004, reason="Invalid attempt")
            return
        
        attempt, exam = attempt_data
        
        # Connect student
        await manager.connect_student(websocket, attempt_id)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "attempt_id": attempt_id,
            "exam_id": exam_id,
            "time_remaining": int((exam.end_at - datetime.utcnow()).total_seconds())
        }))
        
        # Notify teachers about student connection
        await manager.send_to_teachers(exam_id, {
            "type": "student_connected",
            "attempt_id": attempt_id,
            "student_id": attempt.student_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                # Receive message from student
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_student_message(message, attempt_id, exam_id, db)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
    
    finally:
        # Cleanup
        manager.disconnect_student(attempt_id)
        
        # Notify teachers about disconnection
        await manager.send_to_teachers(exam_id, {
            "type": "student_disconnected",
            "attempt_id": attempt_id,
            "timestamp": datetime.utcnow().isoformat()
        })

async def handle_student_message(message: dict, attempt_id: int, exam_id: int, db: AsyncSession):
    """Handle messages from student during exam"""
    message_type = message.get("type")
    
    if message_type == "save_response":
        # Save student response
        await save_student_response(message, attempt_id, db)
        
        # Confirm save to student
        await manager.send_to_student(attempt_id, {
            "type": "response_saved",
            "question_id": message.get("question_id"),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "proctor_event":
        # Log proctoring event
        await log_proctor_event(message, attempt_id, db)
        
        # Notify teachers about suspicious activity
        if message.get("event_type") in ["tab_switch", "focus_loss", "paste"]:
            await manager.send_to_teachers(exam_id, {
                "type": "proctor_alert",
                "attempt_id": attempt_id,
                "event_type": message.get("event_type"),
                "timestamp": datetime.utcnow().isoformat(),
                "details": message.get("payload", {})
            })
    
    elif message_type == "heartbeat":
        # Student heartbeat to maintain connection
        await manager.send_to_student(attempt_id, {
            "type": "heartbeat_ack",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "request_time":
        # Send current time remaining
        attempt_result = await db.execute(
            select(Attempt, Exam)
            .join(Exam, Attempt.exam_id == Exam.id)
            .where(Attempt.id == attempt_id)
        )
        
        attempt_data = attempt_result.first()
        if attempt_data:
            attempt, exam = attempt_data
            time_remaining = int((exam.end_at - datetime.utcnow()).total_seconds())
            
            await manager.send_to_student(attempt_id, {
                "type": "time_update",
                "time_remaining": max(0, time_remaining),
                "timestamp": datetime.utcnow().isoformat()
            })

async def save_student_response(message: dict, attempt_id: int, db: AsyncSession):
    """Save student response to database"""
    question_id = message.get("question_id")
    answer_data = message.get("answer")
    
    if not question_id or not answer_data:
        return
    
    # Check if response already exists
    existing_result = await db.execute(
        select(Response).where(
            and_(
                Response.attempt_id == attempt_id,
                Response.question_id == question_id
            )
        )
    )
    
    existing_response = existing_result.scalar_one_or_none()
    
    if existing_response:
        # Update existing response
        existing_response.answer_json = answer_data
        existing_response.updated_at = datetime.utcnow()
    else:
        # Create new response
        new_response = Response(
            attempt_id=attempt_id,
            question_id=question_id,
            answer_json=answer_data
        )
        db.add(new_response)
    
    await db.commit()

async def log_proctor_event(message: dict, attempt_id: int, db: AsyncSession):
    """Log proctoring event"""
    event_type_str = message.get("event_type")
    payload = message.get("payload", {})
    
    # Convert string to enum
    try:
        event_type = ProctorEventType(event_type_str)
    except ValueError:
        return  # Invalid event type
    
    proctor_log = ProctorLog(
        attempt_id=attempt_id,
        event_type=event_type,
        payload=payload
    )
    
    db.add(proctor_log)
    await db.commit()

# ==================== TEACHER MONITORING WEBSOCKET ====================

@router.websocket("/exam/{exam_id}/monitor")
async def teacher_monitor_websocket(
    websocket: WebSocket,
    exam_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for teacher exam monitoring"""
    try:
        # Verify token and permissions (simplified)
        # In production, properly verify JWT and check teacher permissions
        
        # Verify exam exists
        exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = exam_result.scalar_one_or_none()
        
        if not exam:
            await websocket.close(code=4004, reason="Exam not found")
            return
        
        # Connect teacher
        await manager.connect_teacher(websocket, exam_id)
        
        # Send initial exam status
        exam_status = await get_exam_status(exam_id, db)
        await websocket.send_text(json.dumps({
            "type": "exam_status",
            "data": exam_status
        }))
        
        while True:
            try:
                # Receive message from teacher
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_teacher_message(message, exam_id, db)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
    
    finally:
        # Cleanup
        manager.disconnect_teacher(websocket, exam_id)

async def handle_teacher_message(message: dict, exam_id: int, db: AsyncSession):
    """Handle messages from teacher during monitoring"""
    message_type = message.get("type")
    
    if message_type == "request_status":
        # Send current exam status
        exam_status = await get_exam_status(exam_id, db)
        await manager.send_to_teachers(exam_id, {
            "type": "exam_status",
            "data": exam_status
        })
    
    elif message_type == "send_announcement":
        # Send announcement to all students in exam
        announcement = message.get("message", "")
        
        # Get all active attempts for this exam
        attempts_result = await db.execute(
            select(Attempt.id).where(
                and_(
                    Attempt.exam_id == exam_id,
                    Attempt.status == AttemptStatus.IN_PROGRESS
                )
            )
        )
        
        attempt_ids = [row[0] for row in attempts_result.fetchall()]
        
        # Send announcement to all active students
        for attempt_id in attempt_ids:
            await manager.send_to_student(attempt_id, {
                "type": "announcement",
                "message": announcement,
                "timestamp": datetime.utcnow().isoformat()
            })

async def get_exam_status(exam_id: int, db: AsyncSession) -> dict:
    """Get current exam status for monitoring"""
    # Get exam details
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    
    if not exam:
        return {}
    
    # Get attempt statistics
    attempts_result = await db.execute(
        select(
            Attempt.status,
            func.count(Attempt.id)
        )
        .where(Attempt.exam_id == exam_id)
        .group_by(Attempt.status)
    )
    
    status_counts = {}
    for status, count in attempts_result.all():
        status_counts[status.value] = count
    
    # Get recent proctor events
    recent_events_result = await db.execute(
        select(ProctorLog, User.name)
        .join(Attempt, ProctorLog.attempt_id == Attempt.id)
        .join(User, Attempt.student_id == User.id)
        .where(Attempt.exam_id == exam_id)
        .order_by(ProctorLog.ts.desc())
        .limit(10)
    )
    
    recent_events = []
    for log, student_name in recent_events_result.all():
        recent_events.append({
            "attempt_id": log.attempt_id,
            "student_name": student_name,
            "event_type": log.event_type.value,
            "timestamp": log.ts.isoformat(),
            "payload": log.payload
        })
    
    # Calculate time remaining
    now = datetime.utcnow()
    time_remaining = int((exam.end_at - now).total_seconds()) if exam.end_at > now else 0
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "status": exam.status.value,
        "time_remaining": time_remaining,
        "attempt_counts": status_counts,
        "recent_events": recent_events,
        "timestamp": now.isoformat()
    }

# ==================== BACKGROUND TASKS ====================

async def exam_timer_task():
    """Background task to handle exam timing and auto-submissions"""
    while True:
        try:
            # This would run in a separate process/container in production
            # For now, it's a placeholder for the auto-submission logic
            
            # Check for exams that should end
            # Auto-submit active attempts
            # Send notifications
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Error in exam timer task: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start background task (in production, this would be handled differently)
# asyncio.create_task(exam_timer_task())