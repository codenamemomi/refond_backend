from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.v1.models.user import User
from api.v1.schemas.user import LoginRequest, TokenData
from core.security import verify_password, create_access_token
from core.config import settings
from api.utils.exceptions import UnauthorizedException, NotFoundException

class AuthService:
    @staticmethod
    async def authenticate_user(db: AsyncSession, login_data: LoginRequest) -> Optional[User]:
        # Get user by email
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Check password
        if not verify_password(login_data.password, user.password_hash):
            return None
        
        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        return user

    @staticmethod
    async def login(db: AsyncSession, login_data: LoginRequest):
        user = await AuthService.authenticate_user(db, login_data)
        
        if not user:
            raise UnauthorizedException("Incorrect email or password")
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        token: str,
    ) -> User:
        from core.security import decode_token
        
        try:
            payload = decode_token(token)
            user_id: str = payload.get("sub")
            if user_id is None:
                raise UnauthorizedException("Could not validate credentials")
            
            token_data = TokenData(
                user_id=user_id,
                email=payload.get("email"),
                role=payload.get("role")
            )
        except Exception:
            raise UnauthorizedException("Could not validate credentials")
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise NotFoundException("User not found")
        
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        return user

    @staticmethod
    def require_role(user: User, required_roles: list):
        """Check if user has required role(s)"""
        if user.role.value not in required_roles:
            from api.utils.exceptions import ForbiddenException
            raise ForbiddenException("Insufficient permissions")