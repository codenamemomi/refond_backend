from sqlalchemy import Column, String, Enum, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from api.v1.models.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # e.g., "taxpayer", "filing", "refund"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "create", "update", "delete", "verify"
    details = Column(JSONB, default=dict)  # JSON payload with action details
    
    # Request context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp (more precise than created_at for audit purposes)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.entity_type}.{self.action} by {self.user_id}>"