import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.session import AsyncSessionLocal
from api.v1.services.user_service import UserService, OrganizationService
from api.v1.schemas.user import (
    UserCreate,
    OrganizationCreate,
    UserRole,
    OrganizationType,
)

async def test_auth():
    async with AsyncSessionLocal() as db:
        print("Testing authentication system...\n")
        
        # 1. Create an organization
        print("1. Creating organization...")
        org_data = OrganizationCreate(
            name="Test Accounting Firm",
            type=OrganizationType.ACCOUNTING_FIRM,
            state="Lagos",
            registration_number="RC123456",
            tax_identification_number="1234567890",
            contact_email="info@testfirm.com",
            contact_phone="+2348012345678",
            address="123 Test Street, Lagos"
        )
        
        organization = await OrganizationService.create(db, org_data)
        print(f"Created organization: {organization.name} (ID: {organization.id})")
        
        # 2. Create an admin user
        print("\n2. Creating admin user...")
        admin_data = UserCreate(
            name="Admin User",
            email="admin@testfirm.com",
            password="SecurePass123",
            role=UserRole.ADMIN,
            organization_id=organization.id
        )
        
        admin_user = await UserService.create(db, admin_data)
        print(f"Created admin user: {admin_user.email}")
        
        # 3. Create an accountant user
        print("\n3. Creating accountant user...")
        accountant_data = UserCreate(
            name="Accountant User",
            email="accountant@testfirm.com",
            password="AccountantPass123",
            role=UserRole.ACCOUNTANT,
            organization_id=organization.id
        )
        
        accountant = await UserService.create(db, accountant_data)
        print(f"Created accountant: {accountant.email}")
        
        # 4. Test getting users
        print("\n4. Fetching all users...")
        users = await UserService.get_all(db, organization_id=organization.id)
        print(f"Total users in organization: {len(users)}")
        
        for user in users:
            print(f"  - {user.name} ({user.role.value})")
        
        print("\n✅ Authentication system test completed!")

if __name__ == "__main__":
    asyncio.run(test_auth())