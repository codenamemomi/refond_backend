from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import uuid
from enum import Enum

from api.v1.schemas.user import OrganizationResponse

class TaxType(str, Enum):
    PAYE = "PAYE"
    VAT = "VAT"
    CIT = "CIT"
    WHT = "WHT"
    PIT = "PIT"

class TaxpayerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class NigerianState(str, Enum):
    ABIA = "Abia"
    ADAMAWA = "Adamawa"
    AKWA_IBOM = "Akwa Ibom"
    ANAMBRA = "Anambra"
    BAUCHI = "Bauchi"
    BAYELSA = "Bayelsa"
    BENUE = "Benue"
    BORNO = "Borno"
    CROSS_RIVER = "Cross River"
    DELTA = "Delta"
    EBONYI = "Ebonyi"
    EDO = "Edo"
    EKITI = "Ekiti"
    ENUGU = "Enugu"
    FCT = "FCT"
    GOMBE = "Gombe"
    IMO = "Imo"
    JIGAWA = "Jigawa"
    KADUNA = "Kaduna"
    KANO = "Kano"
    KATSINA = "Katsina"
    KEBBI = "Kebbi"
    KOGI = "Kogi"
    KWARA = "Kwara"
    LAGOS = "Lagos"
    NASARAWA = "Nasarawa"
    NIGER = "Niger"
    OGUN = "Ogun"
    ONDO = "Ondo"
    OSUN = "Osun"
    OYO = "Oyo"
    PLATEAU = "Plateau"
    RIVERS = "Rivers"
    SOKOTO = "Sokoto"
    TARABA = "Taraba"
    YOBE = "Yobe"
    ZAMFARA = "Zamfara"

# Base schemas
class TaxpayerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    tin: Optional[str] = Field(None, max_length=50, pattern=r'^\d{10,12}$')
    bvn: Optional[str] = Field(None, max_length=50, pattern=r'^\d{11}$')
    nin: Optional[str] = Field(None, max_length=50, pattern=r'^\d{11}$')
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=50, pattern=r'^\+?[\d\s\-\(\)]{7,}$')
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    
    # Tax Information
    state: NigerianState
    tax_type: TaxType = TaxType.PAYE
    
    # Business Information
    business_name: Optional[str] = Field(None, max_length=255)
    rc_number: Optional[str] = Field(None, max_length=50)
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    
    # Employment Information
    employment_status: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    employment_date: Optional[date] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('tin')
    def validate_tin(cls, v):
        if v is not None:
            # Basic TIN validation (Nigeria TIN is usually 10-12 digits)
            if not v.isdigit() or len(v) < 10 or len(v) > 12:
                raise ValueError('TIN must be 10-12 digits')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove all non-digit characters for validation
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v

# Create schemas
class TaxpayerCreate(TaxpayerBase):
    employer_id: Optional[uuid.UUID] = None
    
    @validator('business_name')
    def validate_business_name(cls, v, values):
        if values.get('tax_type') in [TaxType.CIT, TaxType.VAT, TaxType.WHT]:
            if not v:
                raise ValueError('Business name is required for company tax types')
        return v
    
    @validator('employment_status')
    def validate_employment_for_paye(cls, v, values):
        if values.get('tax_type') == TaxType.PAYE:
            if not v:
                raise ValueError('Employment status is required for PAYE taxpayers')
        return v

class TaxpayerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=50, pattern=r'^\+?[\d\s\-\(\)]{7,}$')
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[NigerianState] = None
    business_name: Optional[str] = Field(None, max_length=255)
    rc_number: Optional[str] = Field(None, max_length=50)
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    employment_status: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    employment_date: Optional[date] = None
    status: Optional[TaxpayerStatus] = None
    metadata: Optional[Dict[str, Any]] = None

# Response schemas
class TaxpayerResponse(TaxpayerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    employer_id: Optional[uuid.UUID] = None
    status: TaxpayerStatus
    is_verified: bool
    verification_date: Optional[date] = None
    last_filing_date: Optional[date] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed properties
    is_individual: bool
    is_company: bool

class TaxpayerDetailResponse(TaxpayerResponse):
    employer: Optional[OrganizationResponse] = None
    filing_count: int = 0
    active_refund_cases: int = 0
    current_compliance_score: Optional[float] = None

# List and filter schemas
class TaxpayerFilter(BaseModel):
    state: Optional[NigerianState] = None
    tax_type: Optional[TaxType] = None
    status: Optional[TaxpayerStatus] = None
    employer_id: Optional[uuid.UUID] = None
    is_verified: Optional[bool] = None
    search: Optional[str] = None  # Search in name, TIN, business_name
    created_after: Optional[date] = None
    created_before: Optional[date] = None

class TaxpayerListResponse(BaseModel):
    items: List[TaxpayerResponse]
    total: int
    page: int
    size: int
    pages: int

# Bulk operations
class TaxpayerBulkCreate(BaseModel):
    taxpayers: List[TaxpayerCreate]

class TaxpayerImportResult(BaseModel):
    successful: List[TaxpayerResponse]
    failed: List[Dict[str, Any]]
    total_processed: int
    successful_count: int
    failed_count: int