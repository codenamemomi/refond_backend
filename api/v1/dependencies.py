from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_db
from api.v1.services.auth_service import AuthService
from api.v1.models.user import User, UserRole
from api.utils.exceptions import UnauthorizedException

security = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency to get current authenticated user"""
    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Invalid authentication scheme")
    
    return await AuthService.get_current_user(db, credentials.credentials)

def require_role(required_roles: list):
    """Dependency to require specific role(s)"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        AuthService.require_role(current_user, required_roles)
        return current_user
    return role_checker

# Role-specific dependencies
async def require_admin(current_user: User = Depends(get_current_user)):
    AuthService.require_role(current_user, [UserRole.ADMIN.value])
    return current_user

async def require_accountant(current_user: User = Depends(get_current_user)):
    AuthService.require_role(current_user, [UserRole.ACCOUNTANT.value, UserRole.ADMIN.value])
    return current_user

async def require_employer(current_user: User = Depends(get_current_user)):
    AuthService.require_role(current_user, [UserRole.EMPLOYER.value, UserRole.ADMIN.value])
    return current_user

async def require_organization(current_user: User = Depends(get_current_user)):
    AuthService.require_role(current_user, [UserRole.ORGANIZATION.value, UserRole.ADMIN.value])
    return current_user