from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
import uuid

from api.v1.models.user import User, Organization, UserRole
from api.v1.schemas.user import UserCreate, OrganizationCreate, UserUpdate, PasswordChange
from core.security import get_password_hash, verify_password
from api.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)

class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        # Check if user already exists
        existing_user = await UserService.get_by_email(db, user_data.email)
        if existing_user:
            raise ConflictException("User with this email already exists")

        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        db_user = User(
            **user_data.model_dump(exclude={"password"}),
            password_hash=hashed_password
        )
        
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            raise ConflictException("User could not be created")

    @staticmethod
    async def update(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        update_data: UserUpdate,
        current_user: User
    ) -> User:
        # Check if user exists
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Check permissions (users can only update themselves unless admin)
        if user.id != current_user.id and current_user.role != UserRole.ADMIN:
            raise UnauthorizedException("Not authorized to update this user")
        
        # Check if new email is already taken
        if update_data.email and update_data.email != user.email:
            existing = await UserService.get_by_email(db, update_data.email)
            if existing and existing.id != user_id:
                raise ConflictException("Email already in use")
        
        # Update user
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_dict)
            )
            await db.commit()
            await db.refresh(user)
        
        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: uuid.UUID,
        password_data: PasswordChange,
        current_user: User
    ) -> None:
        # Check if user exists
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Check permissions (users can only change their own password unless admin)
        if user.id != current_user.id and current_user.role != UserRole.ADMIN:
            raise UnauthorizedException("Not authorized to change this user's password")
        
        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")
        
        # Update password
        new_hashed_password = get_password_hash(password_data.new_password)
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_hashed_password)
        )
        await db.commit()

    @staticmethod
    async def delete(db: AsyncSession, user_id: uuid.UUID, current_user: User) -> None:
        # Check if user exists
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Check permissions (users can only delete themselves unless admin)
        if user.id != current_user.id and current_user.role != UserRole.ADMIN:
            raise UnauthorizedException("Not authorized to delete this user")
        
        # Don't allow self-deletion if admin (or implement soft delete)
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()

    @staticmethod
    async def get_all(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        organization_id: Optional[uuid.UUID] = None
    ) -> List[User]:
        query = select(User)
        
        if organization_id:
            query = query.where(User.organization_id == organization_id)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

class OrganizationService:
    @staticmethod
    async def get_by_id(db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, org_data: OrganizationCreate) -> Organization:
        db_org = Organization(**org_data.model_dump())
        
        try:
            db.add(db_org)
            await db.commit()
            await db.refresh(db_org)
            return db_org
        except IntegrityError as e:
            await db.rollback()
            # Check which constraint was violated
            if "registration_number" in str(e):
                raise ConflictException("Registration number already in use")
            elif "tax_identification_number" in str(e):
                raise ConflictException("Tax identification number already in use")
            raise ConflictException("Organization could not be created")

    @staticmethod
    async def update(
        db: AsyncSession,
        org_id: uuid.UUID,
        update_data: OrganizationCreate
    ) -> Organization:
        org = await OrganizationService.get_by_id(db, org_id)
        if not org:
            raise NotFoundException("Organization not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            await db.execute(
                update(Organization)
                .where(Organization.id == org_id)
                .values(**update_dict)
            )
            await db.commit()
            await db.refresh(org)
        
        return org

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        org_type: Optional[str] = None
    ) -> List[Organization]:
        query = select(Organization)
        
        if org_type:
            query = query.where(Organization.type == org_type)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()