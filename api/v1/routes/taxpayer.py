from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from api.db.session import get_db
from api.v1.dependencies import get_current_user, require_role
from api.v1.models.user import User, UserRole
from api.v1.services.taxpayer_service import TaxpayerService
from api.v1.schemas.taxpayer import (
    TaxpayerCreate,
    TaxpayerUpdate,
    TaxpayerResponse,
    TaxpayerDetailResponse,
    TaxpayerFilter,
    TaxpayerListResponse,
    TaxpayerBulkCreate,
    TaxpayerImportResult,
    TaxpayerStatus,
)
from api.utils.exceptions import NotFoundException, BadRequestException

taxpayers_router = APIRouter(prefix="/taxpayers", tags=["taxpayers"])

@taxpayers_router.post("", response_model=TaxpayerResponse, status_code=status.HTTP_201_CREATED)
async def create_taxpayer(
    taxpayer_data: TaxpayerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "ACCOUNTANT", "EMPLOYER"]))
):
    """Create a new taxpayer"""
    taxpayer = await TaxpayerService.create(db, taxpayer_data, current_user)
    return TaxpayerResponse.model_validate(taxpayer)

@taxpayers_router.get("", response_model=TaxpayerListResponse)
async def get_taxpayers(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    state: Optional[str] = Query(None, description="Filter by state"),
    tax_type: Optional[str] = Query(None, description="Filter by tax type"),
    status: Optional[TaxpayerStatus] = Query(None, description="Filter by status"),
    employer_id: Optional[uuid.UUID] = Query(None, description="Filter by employer"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    search: Optional[str] = Query(None, description="Search in name, TIN, or business name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get list of taxpayers with filtering and pagination"""
    
    # Build filter
    filter_data = TaxpayerFilter(
        state=state,
        tax_type=tax_type,
        status=status,
        employer_id=employer_id,
        is_verified=is_verified,
        search=search
    )
    
    # Calculate pagination
    skip = (page - 1) * size
    
    # Get taxpayers
    taxpayers, total = await TaxpayerService.get_all(
        db, filter_data, current_user, skip, size
    )
    
    # Calculate pagination info
    pages = (total + size - 1) // size  # Ceiling division
    
    return TaxpayerListResponse(
        items=[TaxpayerResponse.model_validate(tp) for tp in taxpayers],
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@taxpayers_router.get("/{taxpayer_id}", response_model=TaxpayerDetailResponse)
async def get_taxpayer(
    taxpayer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get taxpayer by ID"""
    taxpayer = await TaxpayerService.get_by_id(db, taxpayer_id, include_related=True)
    
    if not taxpayer:
        raise NotFoundException(f"Taxpayer {taxpayer_id} not found")
    
    # Convert to response model
    response = TaxpayerDetailResponse.model_validate(taxpayer)
    
    # Add related counts (these would come from separate queries/services)
    # For now, we'll add placeholder values
    response.filing_count = len(taxpayer.filings) if taxpayer.filings else 0
    response.active_refund_cases = sum(
        1 for rc in taxpayer.refund_cases 
        if rc.status in ["initiated", "under_review"]  # You'll define these statuses later
    ) if taxpayer.refund_cases else 0
    
    return response

@taxpayers_router.put("/{taxpayer_id}", response_model=TaxpayerResponse)
async def update_taxpayer(
    taxpayer_id: uuid.UUID,
    update_data: TaxpayerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "ACCOUNTANT", "EMPLOYER"]))
):
    """Update taxpayer information"""
    taxpayer = await TaxpayerService.update(db, taxpayer_id, update_data, current_user)
    return TaxpayerResponse.model_validate(taxpayer)

@taxpayers_router.delete("/{taxpayer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_taxpayer(
    taxpayer_id: uuid.UUID,
    soft_delete: bool = Query(True, description="Soft delete (mark as deleted) or hard delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "ACCOUNTANT"]))
):
    """Delete a taxpayer"""
    await TaxpayerService.delete(db, taxpayer_id, current_user, soft_delete)
    return None

@taxpayers_router.post("/{taxpayer_id}/verify", response_model=TaxpayerResponse)
async def verify_taxpayer(
    taxpayer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "ACCOUNTANT"]))
):
    """Mark taxpayer as verified"""
    taxpayer = await TaxpayerService.verify_taxpayer(db, taxpayer_id, current_user)
    return TaxpayerResponse.model_validate(taxpayer)

@taxpayers_router.post("/bulk", response_model=TaxpayerImportResult)
async def bulk_create_taxpayers(
    bulk_data: TaxpayerBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "ACCOUNTANT"]))
):
    """Create multiple taxpayers at once"""
    successful, failed = await TaxpayerService.bulk_create(
        db, bulk_data.taxpayers, current_user
    )
    
    return TaxpayerImportResult(
        successful=[TaxpayerResponse.model_validate(tp) for tp in successful],
        failed=failed,
        total_processed=len(bulk_data.taxpayers),
        successful_count=len(successful),
        failed_count=len(failed)
    )

@taxpayers_router.get("/{taxpayer_id}/filings")
async def get_taxpayer_filings(
    taxpayer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all filings for a taxpayer (placeholder for now)"""
    # This will be implemented when we create the Filing model
    taxpayer = await TaxpayerService.get_by_id(db, taxpayer_id)
    
    if not taxpayer:
        raise NotFoundException(f"Taxpayer {taxpayer_id} not found")
    
    return {
        "taxpayer_id": taxpayer_id,
        "filings": []  # Will be populated when Filing model is created
    }

@taxpayers_router.get("/stats/summary")
async def get_taxpayer_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: Optional[uuid.UUID] = Query(None, description="Filter by organization")
):
    """Get taxpayer statistics"""
    stats = await TaxpayerService.get_stats(db, current_user, organization_id)
    return stats

@taxpayers_router.get("/search/tin/{tin}", response_model=TaxpayerDetailResponse)
async def search_by_tin(
    tin: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for taxpayer by TIN"""
    taxpayer = await TaxpayerService.get_by_tin(db, tin)
    
    if not taxpayer:
        raise NotFoundException(f"No taxpayer found with TIN {tin}")
    
    # Check permissions
    if current_user.role.value != "ADMIN":
        if current_user.role.value in ["ACCOUNTANT", "EMPLOYER"]:
            if taxpayer.employer_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this taxpayer"
                )
    
    return TaxpayerDetailResponse.model_validate(taxpayer)