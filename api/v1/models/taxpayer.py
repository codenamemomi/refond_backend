from sqlalchemy import Column, String, ForeignKey, Enum, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import enum
from datetime import date

from api.v1.models.base import BaseModel

class TaxType(str, enum.Enum):
    PAYE = "PAYE"  # Pay As You Earn
    VAT = "VAT"    # Value Added Tax
    CIT = "CIT"    # Company Income Tax
    WHT = "WHT"    # Withholding Tax
    PIT = "PIT"    # Personal Income Tax

class TaxpayerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class NigerianState(str, enum.Enum):
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

class Taxpayer(BaseModel):
    __tablename__ = "taxpayers"
    
    # Core identity
    full_name = Column(String(255), nullable=False)
    tin = Column(String(50), unique=True, index=True, nullable=True)  # Tax Identification Number
    bvn = Column(String(50), nullable=True)  # Bank Verification Number
    nin = Column(String(50), nullable=True)  # National Identity Number
    
    # Contact Information
    email = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Tax Information
    state = Column(Enum(NigerianState), nullable=False)
    tax_type = Column(Enum(TaxType), nullable=False, default=TaxType.PAYE)
    
    # Business Information (for companies)
    business_name = Column(String(255), nullable=True)
    rc_number = Column(String(50), nullable=True)  # Registration Certificate Number
    business_type = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Employment Information (for PAYE)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    employment_status = Column(String(50), nullable=True)  # employed, self-employed, unemployed, retired
    job_title = Column(String(100), nullable=True)
    employment_date = Column(Date, nullable=True)
    
    # Status & Metadata
    status = Column(Enum(TaxpayerStatus), default=TaxpayerStatus.PENDING)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(Date, nullable=True)
    last_filing_date = Column(Date, nullable=True)
    
    # Additional metadata
    extra_data = Column(JSONB, default=dict)  # For flexible additional data
    
    # Relationships
    employer = relationship("Organization", back_populates="taxpayers")
    # filings = relationship("Filing", back_populates="taxpayer", cascade="all, delete-orphan")
    # refund_cases = relationship("RefundCase", back_populates="taxpayer", cascade="all, delete-orphan")
    # compliance_scores = relationship("ComplianceScore", back_populates="taxpayer", cascade="all, delete-orphan")
    
    # Audit fields (in addition to BaseModel fields)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<Taxpayer {self.full_name} ({self.tin})>"
    
    @property
    def is_individual(self) -> bool:
        """Check if taxpayer is an individual (not a company)"""
        return self.tax_type in [TaxType.PAYE, TaxType.PIT]
    
    @property
    def is_company(self) -> bool:
        """Check if taxpayer is a company"""
        return self.tax_type in [TaxType.CIT, TaxType.VAT, TaxType.WHT]