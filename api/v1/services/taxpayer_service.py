from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
import uuid
from datetime import date, datetime

from api.v1.models.taxpayer import Taxpayer, TaxType, TaxpayerStatus, NigerianState
from api.v1.models.user import User
from api.v1.schemas.taxpayer import (
    TaxpayerCreate,
    TaxpayerUpdate,
    TaxpayerFilter,
    TaxpayerResponse,
    TaxpayerDetailResponse,
)
from api.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
)
from api.v1.services.audit_service import AuditService

class TaxpayerService:
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession, 
        taxpayer_id: uuid.UUID,
        include_related: bool = False
    ) -> Optional[Taxpayer]:
        """Get taxpayer by ID with optional related data"""
        query = select(Taxpayer).where(Taxpayer.id == taxpayer_id)
        
        if include_related:
            query = query.options(
                selectinload(Taxpayer.employer)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_tin(db: AsyncSession, tin: str) -> Optional[Taxpayer]:
        """Get taxpayer by Tax Identification Number"""
        result = await db.execute(
            select(Taxpayer).where(Taxpayer.tin == tin)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession, 
        taxpayer_data: TaxpayerCreate,
        current_user: User
    ) -> Taxpayer:
        """Create a new taxpayer"""
        # Check if TIN already exists
        if taxpayer_data.tin:
            existing = await TaxpayerService.get_by_tin(db, taxpayer_data.tin)
            if existing:
                raise ConflictException(f"Taxpayer with TIN {taxpayer_data.tin} already exists")
        
        # Create taxpayer instance
        db_taxpayer = Taxpayer(
            **taxpayer_data.model_dump(exclude={"employer_id"}),
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # Set employer if provided and user has permission
        if taxpayer_data.employer_id:
            # Verify employer exists and user has access
            from api.v1.services.user_service import OrganizationService
            employer = await OrganizationService.get_by_id(db, taxpayer_data.employer_id)
            
            if not employer:
                raise BadRequestException(f"Organization {taxpayer_data.employer_id} not found")
            
            # Check if current user belongs to this organization
            if current_user.organization_id != taxpayer_data.employer_id and current_user.role.value != "ADMIN":
                raise ForbiddenException("You can only assign taxpayers to your own organization")
            
            db_taxpayer.employer_id = taxpayer_data.employer_id
        
        try:
            db.add(db_taxpayer)
            await db.commit()
            await db.refresh(db_taxpayer)
            
            # Log the creation
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                entity_type="taxpayer",
                entity_id=db_taxpayer.id,
                action="create",
                details={"data": taxpayer_data.model_dump()}
            )
            
            return db_taxpayer
        except IntegrityError as e:
            await db.rollback()
            if "unique constraint" in str(e).lower():
                raise ConflictException("Taxpayer with these details already exists")
            raise BadRequestException(f"Error creating taxpayer: {str(e)}")
    
    @staticmethod
    async def update(
        db: AsyncSession,
        taxpayer_id: uuid.UUID,
        update_data: TaxpayerUpdate,
        current_user: User
    ) -> Taxpayer:
        """Update an existing taxpayer"""
        taxpayer = await TaxpayerService.get_by_id(db, taxpayer_id)
        if not taxpayer:
            raise NotFoundException(f"Taxpayer {taxpayer_id} not found")
        
        # Check permissions
        await TaxpayerService._check_permissions(db, taxpayer, current_user, "update")
        
        # Store original data for audit
        original_data = {
            "full_name": taxpayer.full_name,
            "email": taxpayer.email,
            "status": taxpayer.status.value if taxpayer.status else None,
            "metadata": taxpayer.metadata.copy() if taxpayer.metadata else {}
        }
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if "metadata" in update_dict and taxpayer.metadata:
            # Merge metadata instead of replacing
            taxpayer.metadata.update(update_dict["metadata"])
            del update_dict["metadata"]
        
        for field, value in update_dict.items():
            setattr(taxpayer, field, value)
        
        taxpayer.updated_by = current_user.id
        taxpayer.updated_at = datetime.utcnow()
        
        try:
            await db.commit()
            await db.refresh(taxpayer)
            
            # Log the update
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                entity_type="taxpayer",
                entity_id=taxpayer.id,
                action="update",
                details={
                    "original": original_data,
                    "updated": update_dict
                }
            )
            
            return taxpayer
        except IntegrityError as e:
            await db.rollback()
            raise BadRequestException(f"Error updating taxpayer: {str(e)}")
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        taxpayer_id: uuid.UUID,
        current_user: User,
        soft_delete: bool = True
    ) -> None:
        """Delete a taxpayer (soft delete by default)"""
        taxpayer = await TaxpayerService.get_by_id(db, taxpayer_id)
        if not taxpayer:
            raise NotFoundException(f"Taxpayer {taxpayer_id} not found")
        
        # Check permissions
        await TaxpayerService._check_permissions(db, taxpayer, current_user, "delete")
        
        if soft_delete:
            # Soft delete (update status)
            taxpayer.status = TaxpayerStatus.DELETED
            taxpayer.updated_by = current_user.id
            taxpayer.updated_at = datetime.utcnow()
            
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                entity_type="taxpayer",
                entity_id=taxpayer.id,
                action="soft_delete",
                details={"reason": "User requested deletion"}
            )
        else:
            # Hard delete (remove from database)
            await db.delete(taxpayer)
            
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                entity_type="taxpayer",
                entity_id=taxpayer_id,
                action="hard_delete",
                details={"reason": "Permanent deletion requested"}
            )
        
        await db.commit()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        filter_data: TaxpayerFilter,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Taxpayer], int]:
        """Get taxpayers with filtering and pagination"""
        query = select(Taxpayer)
        
        # Apply filters
        query = TaxpayerService._apply_filters(query, filter_data, current_user)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        taxpayers = result.scalars().all()
        
        return taxpayers, total
    
    @staticmethod
    def _apply_filters(query, filter_data: TaxpayerFilter, current_user: User):
        """Apply filters to query based on user permissions"""
        
        # Base permission filter
        if current_user.role.value != "ADMIN":
            # Non-admin users can only see their organization's taxpayers
            if current_user.role.value in ["ACCOUNTANT", "EMPLOYER"]:
                query = query.where(Taxpayer.employer_id == current_user.organization_id)
        
        # Apply user-provided filters
        if filter_data.state:
            query = query.where(Taxpayer.state == filter_data.state)
        
        if filter_data.tax_type:
            query = query.where(Taxpayer.tax_type == filter_data.tax_type)
        
        if filter_data.status:
            query = query.where(Taxpayer.status == filter_data.status)
        else:
            # Exclude deleted taxpayers by default
            query = query.where(Taxpayer.status != TaxpayerStatus.DELETED)
        
        if filter_data.employer_id:
            query = query.where(Taxpayer.employer_id == filter_data.employer_id)
        
        if filter_data.is_verified is not None:
            query = query.where(Taxpayer.is_verified == filter_data.is_verified)
        
        if filter_data.search:
            search_pattern = f"%{filter_data.search}%"
            query = query.where(
                or_(
                    Taxpayer.full_name.ilike(search_pattern),
                    Taxpayer.tin.ilike(search_pattern),
                    Taxpayer.business_name.ilike(search_pattern),
                    Taxpayer.email.ilike(search_pattern)
                )
            )
        
        if filter_data.created_after:
            query = query.where(Taxpayer.created_at >= filter_data.created_after)
        
        if filter_data.created_before:
            query = query.where(Taxpayer.created_at <= filter_data.created_before)
        
        # Order by creation date (newest first)
        query = query.order_by(Taxpayer.created_at.desc())
        
        return query
    
    @staticmethod
    async def _check_permissions(
        db: AsyncSession,
        taxpayer: Taxpayer,
        current_user: User,
        action: str
    ) -> None:
        """Check if user has permission to perform action on taxpayer"""
        
        # Admins can do anything
        if current_user.role.value == "ADMIN":
            return
        
        # Accountants and Employers can only manage their organization's taxpayers
        if current_user.role.value in ["ACCOUNTANT", "EMPLOYER"]:
            if taxpayer.employer_id != current_user.organization_id:
                raise ForbiddenException(
                    f"You don't have permission to {action} this taxpayer"
                )
        
        # Organization users have limited access
        if current_user.role.value == "ORGANIZATION":
            raise ForbiddenException(
                f"Organization users cannot {action} taxpayers"
            )
    
    @staticmethod
    async def verify_taxpayer(
        db: AsyncSession,
        taxpayer_id: uuid.UUID,
        current_user: User,
        verification_data: Optional[Dict[str, Any]] = None
    ) -> Taxpayer:
        """Mark taxpayer as verified"""
        taxpayer = await TaxpayerService.get_by_id(db, taxpayer_id)
        if not taxpayer:
            raise NotFoundException(f"Taxpayer {taxpayer_id} not found")
        
        # Check permissions (only admins and organization accountants can verify)
        if current_user.role.value not in ["ADMIN", "ACCOUNTANT"]:
            raise ForbiddenException("You don't have permission to verify taxpayers")
        
        if taxpayer.employer_id and current_user.role.value == "ACCOUNTANT":
            if taxpayer.employer_id != current_user.organization_id:
                raise ForbiddenException(
                    "You can only verify taxpayers in your organization"
                )
        
        taxpayer.is_verified = True
        taxpayer.verification_date = date.today()
        taxpayer.updated_by = current_user.id
        taxpayer.updated_at = datetime.utcnow()
        
        if verification_data:
            if not taxpayer.metadata:
                taxpayer.metadata = {}
            taxpayer.metadata["verification"] = verification_data
        
        await db.commit()
        await db.refresh(taxpayer)
        
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            entity_type="taxpayer",
            entity_id=taxpayer.id,
            action="verify",
            details=verification_data or {}
        )
        
        return taxpayer
    
    @staticmethod
    async def bulk_create(
        db: AsyncSession,
        taxpayers_data: List[TaxpayerCreate],
        current_user: User
    ) -> tuple[List[Taxpayer], List[Dict[str, Any]]]:
        """Create multiple taxpayers at once"""
        successful = []
        failed = []
        
        for data in taxpayers_data:
            try:
                taxpayer = await TaxpayerService.create(db, data, current_user)
                successful.append(taxpayer)
                
                await AuditService.log_action(
                    db=db,
                    user_id=current_user.id,
                    entity_type="taxpayer",
                    entity_id=taxpayer.id,
                    action="bulk_create",
                    details={"data": data.model_dump()}
                )
                
            except Exception as e:
                failed.append({
                    "data": data.model_dump(),
                    "error": str(e)
                })
        
        # Commit once after all operations
        await db.commit()
        
        return successful, failed
    
    @staticmethod
    async def get_stats(
        db: AsyncSession,
        current_user: User,
        organization_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Get taxpayer statistics"""
        
        # Base query with permission filter
        query = select(Taxpayer)
        
        if current_user.role.value != "ADMIN":
            if current_user.role.value in ["ACCOUNTANT", "EMPLOYER"]:
                query = query.where(Taxpayer.employer_id == current_user.organization_id)
            elif current_user.role.value == "ORGANIZATION":
                # Organizations can only see aggregate stats
                pass
        
        if organization_id:
            query = query.where(Taxpayer.employer_id == organization_id)
        
        # Exclude deleted taxpayers
        query = query.where(Taxpayer.status != TaxpayerStatus.DELETED)
        
        # Get counts by tax type
        tax_type_query = select(
            Taxpayer.tax_type,
            func.count(Taxpayer.id)
        ).select_from(query.subquery()).group_by(Taxpayer.tax_type)
        
        tax_type_result = await db.execute(tax_type_query)
        tax_type_counts = dict(tax_type_result.all())
        
        # Get counts by status
        status_query = select(
            Taxpayer.status,
            func.count(Taxpayer.id)
        ).select_from(query.subquery()).group_by(Taxpayer.status)
        
        status_result = await db.execute(status_query)
        status_counts = dict(status_result.all())
        
        # Get total count
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # Get verified count
        verified_query = select(func.count()).where(
            query.whereclause & (Taxpayer.is_verified == True)
        )
        verified_result = await db.execute(verified_query)
        verified_count = verified_result.scalar()
        
        return {
            "total": total,
            "verified": verified_count,
            "verification_rate": (verified_count / total * 100) if total > 0 else 0,
            "by_tax_type": tax_type_counts,
            "by_status": status_counts,
            "by_state": {},  # Can be implemented similarly
        }