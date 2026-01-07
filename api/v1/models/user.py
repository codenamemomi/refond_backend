from sqlalchemy import Column, String, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from api.v1.models.base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ACCOUNTANT = "ACCOUNTANT"
    EMPLOYER = "EMPLOYER"
    ORGANIZATION = "ORGANIZATION"

class OrganizationType(str, enum.Enum):
    ACCOUNTING_FIRM = "accounting_firm"
    EMPLOYER = "employer"
    FINTECH = "fintech"

class User(BaseModel):
    __tablename__ = "users"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ACCOUNTANT)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False)
    type = Column(Enum(OrganizationType), nullable=False)
    state = Column(String(100), nullable=True)
    registration_number = Column(String(100), unique=True, nullable=True)
    tax_identification_number = Column(String(100), unique=True, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    taxpayers = relationship("Taxpayer", back_populates="employer")
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.type})>"