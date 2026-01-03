from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ACCOUNTANT = "ACCOUNTANT"
    EMPLOYER = "EMPLOYER"
    ORGANIZATION = "ORGANIZATION"

class OrganizationType(str, Enum):
    ACCOUNTING_FIRM = "accounting_firm"
    EMPLOYER = "employer"
    FINTECH = "fintech"

# Base schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    type: OrganizationType
    state: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_identification_number: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)

# Create schemas
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.ACCOUNTANT
    organization_id: Optional[uuid.UUID] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationCreateWithUser(OrganizationCreate):
    admin_user: UserCreate

# Response schemas
class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    organization_id: Optional[uuid.UUID]
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationResponse(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    role: Optional[str] = None

# Update schemas
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v