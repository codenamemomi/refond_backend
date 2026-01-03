from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_db
from api.v1.services.auth_service import AuthService
from api.v1.services.user_service import UserService
from api.v1.dependencies import get_current_user, require_role
from api.v1.schemas.user import (
    LoginRequest,
    OrganizationCreate,
    Token,
    UserResponse,
    UserCreate,
    OrganizationCreateWithUser,
    UserUpdate,
    PasswordChange,
    UserRole,
)
from api.v1.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["authentication"])

@auth_router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    result = await AuthService.login(db, login_data)
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "user": UserResponse.model_validate(result["user"])
    }

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    user = await UserService.create(db, user_data)
    return UserResponse.model_validate(user)

@auth_router.post("/register-with-organization", status_code=status.HTTP_201_CREATED)
async def register_with_organization(
    data: OrganizationCreateWithUser,
    db: AsyncSession = Depends(get_db)
):
    """Register an organization with an admin user"""
    from api.v1.services.user_service import OrganizationService
    
    # Create organization first
    org_data = data.model_dump(exclude={"admin_user"})
    organization = await OrganizationService.create(db, OrganizationCreate(**org_data))
    
    # Create admin user with organization ID
    admin_data = data.admin_user
    admin_data.organization_id = organization.id
    admin_data.role = UserRole.ADMIN  # Organization admin
    
    user = await UserService.create(db, admin_data)
    
    return {
        "organization": organization,
        "user": UserResponse.model_validate(user)
    }

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user's information"""
    return UserResponse.model_validate(current_user)

@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's information"""
    user = await UserService.update(db, current_user.id, update_data, current_user)
    return UserResponse.model_validate(user)

@auth_router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    await UserService.change_password(db, current_user.id, password_data, current_user)
    return {"message": "Password changed successfully"}

@auth_router.post("/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify user's email (placeholder - implement email service later)"""
    # TODO: Implement email verification logic
    return {"message": "Email verification endpoint"}

@auth_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset (placeholder)"""
    # TODO: Implement password reset logic
    return {"message": "Password reset email sent"}