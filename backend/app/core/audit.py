import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, or_
from ..models.models import AuditLog, User

# Audit action constants
AUDIT_ACTIONS = {
    "CREATE": "create",
    "UPDATE": "update", 
    "DELETE": "delete",
    "LOGIN": "login",
    "LOGOUT": "logout",
    "PUBLISH": "publish",
    "START": "start",
    "END": "end",
    "SUBMIT": "submit",
    "GRADE_UPDATE": "grade_update",
    "AI_GRADING": "ai_grading",
    "BULK_UPDATE": "bulk_update",
    "BULK_IMPORT": "bulk_import",
    "BULK_EXPORT": "bulk_export",
    "LOCK_OVERRIDE": "lock_override",
    "CONFIG_CHANGE": "config_change",
    "SUSPEND_USER": "suspend_user",
    "REACTIVATE_USER": "reactivate_user",
    "PUBLISH_RESULTS": "publish_results"
}

def calculate_hash(data: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
    """Calculate hash for audit log entry to ensure integrity"""
    hash_input = json.dumps(data, sort_keys=True, default=str)
    if prev_hash:
        hash_input = prev_hash + hash_input
    return hashlib.sha256(hash_input.encode()).hexdigest()

async def log_audit_event(
    db: AsyncSession,
    actor_id: int,
    entity_type: str,
    entity_id: Optional[int],
    action: str,
    before_json: Optional[Dict[str, Any]] = None,
    after_json: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None
) -> AuditLog:
    """Log an audit event with hash chain for integrity"""
    
    # Get the last audit log entry for hash chaining
    last_log_result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.id)).limit(1)
    )
    last_log = last_log_result.scalar_one_or_none()
    prev_hash = last_log.hash if last_log else None
    
    # Create audit data
    audit_data = {
        "ts": datetime.utcnow().isoformat(),
        "actor_id": actor_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "before_json": before_json,
        "after_json": after_json,
        "reason": reason
    }
    
    # Calculate hash
    current_hash = calculate_hash(audit_data, prev_hash)
    
    # Create audit log entry
    audit_log = AuditLog(
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json,
        reason=reason,
        hash=current_hash,
        prev_hash=prev_hash
    )
    
    db.add(audit_log)
    await db.flush()  # Get the ID without committing
    
    return audit_log

class AuditService:
    """Service for audit log operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        action: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        
        query = select(AuditLog).join(User, AuditLog.actor_id == User.id)
        
        # Apply filters
        filters = []
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if entity_id:
            filters.append(AuditLog.entity_id == entity_id)
        if actor_id:
            filters.append(AuditLog.actor_id == actor_id)
        if action:
            filters.append(AuditLog.action == action)
        
        # Date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filters.append(AuditLog.ts >= cutoff_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(AuditLog.ts)).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        # Format response
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log.id,
                "timestamp": log.ts,
                "actor_id": log.actor_id,
                "actor_name": log.actor.name if log.actor else "Unknown",
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "before_json": log.before_json,
                "after_json": log.after_json,
                "reason": log.reason,
                "hash": log.hash
            })
        
        return formatted_logs
    
    async def get_entity_history(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Get complete audit history for a specific entity"""
        
        query = select(AuditLog).join(User, AuditLog.actor_id == User.id).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(AuditLog.ts)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log.id,
                "timestamp": log.ts,
                "actor_name": log.actor.name if log.actor else "Unknown",
                "action": log.action,
                "changes": self._calculate_changes(log.before_json, log.after_json),
                "reason": log.reason
            })
        
        return formatted_logs
    
    def _calculate_changes(
        self, 
        before: Optional[Dict[str, Any]], 
        after: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate what changed between before and after states"""
        
        changes = {}
        
        if before and after:
            # Find changed fields
            all_keys = set(before.keys()) | set(after.keys())
            for key in all_keys:
                before_val = before.get(key)
                after_val = after.get(key)
                if before_val != after_val:
                    changes[key] = {
                        "from": before_val,
                        "to": after_val
                    }
        elif after and not before:
            # Creation
            changes = {"created": after}
        elif before and not after:
            # Deletion
            changes = {"deleted": before}
        
        return changes
    
    async def verify_audit_chain(self) -> Dict[str, Any]:
        """Verify the integrity of the audit log chain"""
        
        query = select(AuditLog).order_by(AuditLog.id)
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        verification_result = {
            "total_logs": len(logs),
            "verified_count": 0,
            "broken_chains": [],
            "is_valid": True
        }
        
        prev_hash = None
        for log in logs:
            # Recreate audit data for hash verification
            audit_data = {
                "ts": log.ts.isoformat(),
                "actor_id": log.actor_id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "before_json": log.before_json,
                "after_json": log.after_json,
                "reason": log.reason
            }
            
            expected_hash = calculate_hash(audit_data, prev_hash)
            
            if expected_hash == log.hash and log.prev_hash == prev_hash:
                verification_result["verified_count"] += 1
            else:
                verification_result["broken_chains"].append({
                    "log_id": log.id,
                    "expected_hash": expected_hash,
                    "actual_hash": log.hash,
                    "expected_prev_hash": prev_hash,
                    "actual_prev_hash": log.prev_hash
                })
                verification_result["is_valid"] = False
            
            prev_hash = log.hash
        
        return verification_result
    
    async def export_audit_logs(self, logs: List[Dict[str, Any]]) -> str:
        """Export audit logs to JSON format"""
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_logs": len(logs),
            "logs": logs
        }
        
        return json.dumps(export_data, indent=2, default=str)