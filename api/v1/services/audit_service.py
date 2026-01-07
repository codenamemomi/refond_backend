from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from datetime import datetime
import uuid
from typing import Optional, Dict, Any

from api.v1.models.audit_log import AuditLog

class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an action to the audit trail"""
        
        audit_log = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        await db.flush()  # Flush but don't commit - let the main transaction handle it
        
        return audit_log