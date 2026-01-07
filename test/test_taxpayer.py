import asyncio
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import AsyncSessionLocal
from api.v1.services.user_service import UserService, OrganizationService
from api.v1.services.taxpayer_service import TaxpayerService
from api.v1.schemas.user import (
    UserCreate,
    OrganizationCreate,
    UserRole,
    OrganizationType,
)
from api.v1.schemas.taxpayer import (
    TaxpayerCreate,
    TaxpayerUpdate,
    NigerianState,
    TaxType,
    TaxpayerStatus,
)

async def test_taxpayer_api():
    async with AsyncSessionLocal() as db:
        print("Testing Taxpayer API...\n")
        
        # 1. Create test organization
        print("1. Creating test organization...")
        org_data = OrganizationCreate(
            name="Test Employer Ltd",
            type=OrganizationType.EMPLOYER,
            state="Lagos",
            registration_number="RC789012",
            tax_identification_number="0987654321",
        )
        
        organization = await OrganizationService.create(db, org_data)
        org_id = organization.id
        
        # 2. Create test user (accountant)
        print("\n2. Creating test user...")
        user_data = UserCreate(
            name="Test Accountant",
            email="taxpayer_test@example.com",
            password="TestPass123",
            role=UserRole.ACCOUNTANT,
            organization_id=org_id
        )
        
        user = await UserService.create(db, user_data)
        
        # 3. Create individual taxpayer (PAYE)
        print("\n3. Creating individual taxpayer (PAYE)...")
        individual_tp = TaxpayerCreate(
            full_name="John Chinedu",
            tin="123456789012",
            bvn="12345678901",
            nin="98765432109",
            email="john.chinedu@example.com",
            phone_number="+2348012345678",
            address="123 Main Street, Lagos",
            city="Lagos",
            state=NigerianState.LAGOS,
            tax_type=TaxType.PAYE,
            employment_status="employed",
            job_title="Software Engineer",
            employment_date=date(2020, 1, 1),
            employer_id=org_id
        )
        
        taxpayer1 = await TaxpayerService.create(db, individual_tp, user)
        print(f"Created individual taxpayer: {taxpayer1.full_name} (TIN: {taxpayer1.tin})")
        
        # 4. Create company taxpayer (CIT)
        print("\n4. Creating company taxpayer (CIT)...")
        company_tp = TaxpayerCreate(
            full_name="Jane Smith",
            tin="987654321098",
            email="info@techsolutions.com",
            phone_number="+2348023456789",
            address="456 Tech Park, Abuja",
            city="Abuja",
            state=NigerianState.FCT,
            tax_type=TaxType.CIT,
            business_name="Tech Solutions Ltd",
            rc_number="RC456789",
            business_type="Limited Liability",
            industry="Technology",
            metadata={
                "annual_revenue": 50000000,
                "employee_count": 25,
                "registration_year": 2018
            }
        )
        
        taxpayer2 = await TaxpayerService.create(db, company_tp, user)
        print(f"Created company taxpayer: {taxpayer2.business_name} (RC: {taxpayer2.rc_number})")
        
        # 5. Test getting taxpayer by ID
        print("\n5. Getting taxpayer by ID...")
        fetched_tp = await TaxpayerService.get_by_id(db, taxpayer1.id, include_related=True)
        print(f"Fetched taxpayer: {fetched_tp.full_name}")
        print(f"  Is individual: {fetched_tp.is_individual}")
        print(f"  Employer: {fetched_tp.employer.name if fetched_tp.employer else 'None'}")
        
        # 6. Test updating taxpayer
        print("\n6. Updating taxpayer...")
        update_data = TaxpayerUpdate(
            email="john.newemail@example.com",
            phone_number="+2348098765432",
            job_title="Senior Software Engineer"
        )
        
        updated_tp = await TaxpayerService.update(db, taxpayer1.id, update_data, user)
        print(f"Updated email: {updated_tp.email}")
        print(f"Updated phone: {updated_tp.phone_number}")
        
        # 7. Test verification
        print("\n7. Verifying taxpayer...")
        verified_tp = await TaxpayerService.verify_taxpayer(db, taxpayer1.id, user)
        print(f"Verification status: {verified_tp.is_verified}")
        print(f"Verification date: {verified_tp.verification_date}")
        
        # 8. Test filtering
        print("\n8. Testing taxpayer filtering...")
        from api.v1.schemas.taxpayer import TaxpayerFilter
        
        filter_data = TaxpayerFilter(
            state=NigerianState.LAGOS,
            tax_type=TaxType.PAYE,
            status=TaxpayerStatus.ACTIVE
        )
        
        taxpayers, total = await TaxpayerService.get_all(db, filter_data, user)
        print(f"Found {total} taxpayers matching filters")
        
        for tp in taxpayers:
            print(f"  - {tp.full_name} ({tp.tax_type.value})")
        
        # 9. Test stats
        print("\n9. Getting taxpayer statistics...")
        stats = await TaxpayerService.get_stats(db, user, org_id)
        print(f"Total taxpayers: {stats['total']}")
        print(f"Verified: {stats['verified']}")
        print(f"By tax type: {stats['by_tax_type']}")
        
        print("\n✅ Taxpayer API test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_taxpayer_api())