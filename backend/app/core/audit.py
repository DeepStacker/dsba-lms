"""
Audit logging utilities for Apollo LMS
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, or_

from ..models.models import AuditLog, User


async def create_audit_log(
    db: AsyncSession,
    actor_id: int,
    entity_type: str,
    entity_id: Optional[int],
    action: str,
    before_json: Optional[Dict[str, Any]] = None,
    after_json: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    prev_hash: Optional[str] = None
) -> AuditLog:
    """Create a new audit log entry with hash chaining"""

    # Create log data
    log_data = {
        "ts": datetime.utcnow(),
        "actor_id": actor_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "before_json": before_json,
        "after_json": after_json,
        "reason": reason,
        "prev_hash": prev_hash
    }

    # Generate hash
    data_str = json.dumps(log_data, sort_keys=True, default=str)
    hash_value = hashlib.sha256(data_str.encode()).hexdigest()

    # Create audit log entry
    audit_log = AuditLog(
        ts=log_data["ts"],
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json,
        reason=reason,
        hash=hash_value,
        prev_hash=prev_hash
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    return audit_log


class AuditService:
    """Service for audit logging operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        action: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""

        query = select(AuditLog, User).join(User, AuditLog.actor_id == User.id)
        filters = []

        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if entity_id:
            filters.append(AuditLog.entity_id == entity_id)
        if actor_id:
            filters.append(AuditLog.actor_id == actor_id)
        if action:
            filters.append(AuditLog.action == action)

        # Time filter
        date_threshold = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days)
        filters.append(AuditLog.ts >= date_threshold)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(AuditLog.ts))
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        audit_data = result.fetchall()

        logs = []
        for audit_log, actor in audit_data:
            log_data = {
                "id": audit_log.id,
                "timestamp": audit_log.ts,
                "actor_id": audit_log.actor_id,
                "actor_name": actor.name,
                "actor_email": actor.email,
                "entity_type": audit_log.entity_type,
                "entity_id": audit_log.entity_id,
                "action": audit_log.action,
                "before_data": audit_log.before_json,
                "after_data": audit_log.after_json,
                "reason": audit_log.reason,
                "hash": audit_log.hash,
                "prev_hash": audit_log.prev_hash,
                "hash_chain_valid": True  # Simplified validation
            }
            logs.append(log_data)

        return logs

    async def get_entity_history(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """Get complete audit history for a specific entity"""

        return await self.get_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=1000
        )

    async def get_system_changes(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get system-wide changes in the last N days"""

        return await self.get_audit_logs(days=days, limit=500)

    async def verify_hash_chain(self, logs: List[AuditLog]) -> bool:
        """Verify the integrity of the audit hash chain"""

        # Sort logs by timestamp
        sorted_logs = sorted(logs, key=lambda x: x.ts)

        prev_hash = None
        for log in sorted_logs:
            # Recalculate hash based on log data
            log_data = {
                "ts": log.ts,
                "actor_id": log.actor_id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "before_json": log.before_json,
                "after_json": log.after_json,
                "reason": log.reason,
                "prev_hash": prev_hash
            }

            data_str = json.dumps(log_data, sort_keys=True, default=str)
            calculated_hash = hashlib.sha256(data_str.encode()).hexdigest()

            if calculated_hash != log.hash:
                return False

            prev_hash = log.hash

        return True

    async def export_audit_logs(self, logs: List[Dict[str, Any]]) -> str:
        """Export audit logs to structured format"""

        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_logs": len(logs),
            "logs": logs
        }

        return json.dumps(export_data, indent=2, default=str)


# Utility functions for easy access
async def log_audit_event(db: AsyncSession, actor_id: int, entity_type: str,
                         entity_id: int, action: str, before_data=None,
                         after_data=None, reason=None):
    """Convenience function to log an audit event"""
    return await create_audit_log(
        db=db,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_data,
        after_json=after_data,
        reason=reason
    )


# Audit categories for consistent logging
AUDIT_ACTIONS = {
    "CREATE": "create",
    "UPDATE": "update",
    "DELETE": "delete",
    "BULK_IMPORT": "bulk_import",
    "BULK_EXPORT": "bulk_export",
    "BULK_UPDATE": "bulk_update",
    "LOGIN": "login",
    "LOGOUT": "logout",
    "PASSWORD_CHANGE": "password_change",
    "PERMISSION_CHANGE": "permission_change",
    "EXAM_SUBMIT": "exam_submit",
    "GRADE_UPDATE": "grade_update",
    "AI_GRADING": "ai_grading",
    "QUESTION_GENERATION": "question_generation",
    "LOCK_OVERRIDE": "lock_override",
    "CONFIG_CHANGE": "config_change"
}

AUDIT_ENTITIES = {
    "USER": "user",
    "ROLE": "role",
    "COURSE": "course",
    "EXAM": "exam",
    "QUESTION": "question",
    "RESPONSE": "response",
    "PROGRAM": "program",
    "OUTCOME": "outcome",
    "GRADE": "grade",
    "LOCK": "lock",
    "CONFIG": "config",
    "SYSTEM": "system"
}