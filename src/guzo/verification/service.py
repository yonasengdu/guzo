"""Verification service - Business logic for driver verification."""

from datetime import datetime
from typing import Optional

from src.guzo.auth.core import User
from src.guzo.verification.core import (
    DriverVerification,
    VerificationStatus,
    VerificationSubmit,
    VerificationUpdate,
    VerificationResponse,
    VerificationStats,
)
from src.guzo.verification.repository import VerificationRepository


class VerificationService:
    """Service for verification business logic."""
    
    @staticmethod
    async def get_or_create_verification(driver_id: str) -> DriverVerification:
        """Get existing verification or create new one."""
        verification = await VerificationRepository.get_by_driver(driver_id)
        
        if not verification:
            verification = DriverVerification(driver_id=driver_id)
            await VerificationRepository.create(verification)
        
        return verification
    
    @staticmethod
    async def submit_verification(
        driver_id: str,
        data: VerificationSubmit,
        profile_photo: str = None,
        license_document: str = None,
        vehicle_registration: str = None,
    ) -> DriverVerification:
        """Submit or update verification documents."""
        verification = await VerificationService.get_or_create_verification(driver_id)
        
        # Update fields
        if profile_photo:
            verification.profile_photo = profile_photo
        if license_document:
            verification.license_document = license_document
        if vehicle_registration:
            verification.vehicle_registration = vehicle_registration
        if data.license_number:
            verification.license_number = data.license_number
        if data.license_expiry:
            verification.license_expiry = data.license_expiry
        
        # Reset status if documents changed
        if verification.status in (
            VerificationStatus.REJECTED,
            VerificationStatus.EXPIRED,
        ):
            verification.status = VerificationStatus.PENDING
        
        verification.submitted_at = datetime.utcnow()
        await verification.save()
        
        return verification
    
    @staticmethod
    async def get_driver_verification(driver_id: str) -> Optional[VerificationResponse]:
        """Get verification status for a driver."""
        from beanie import PydanticObjectId
        
        verification = await VerificationRepository.get_by_driver(driver_id)
        
        if not verification:
            return None
        
        driver = await User.get(PydanticObjectId(driver_id))
        
        return VerificationResponse(
            id=str(verification.id),
            driver_id=verification.driver_id,
            driver_name=driver.full_name if driver else None,
            driver_email=driver.email if driver else None,
            profile_photo=verification.profile_photo,
            license_document=verification.license_document,
            license_number=verification.license_number,
            license_expiry=verification.license_expiry,
            vehicle_registration=verification.vehicle_registration,
            status=verification.status,
            admin_notes=verification.admin_notes,
            rejection_reason=verification.rejection_reason,
            submitted_at=verification.submitted_at,
            reviewed_at=verification.reviewed_at,
        )
    
    @staticmethod
    async def get_pending_verifications() -> list[VerificationResponse]:
        """Get all pending verifications with driver info."""
        from beanie import PydanticObjectId
        
        verifications = await VerificationRepository.get_pending()
        
        responses = []
        for v in verifications:
            driver = await User.get(PydanticObjectId(v.driver_id))
            
            responses.append(VerificationResponse(
                id=str(v.id),
                driver_id=v.driver_id,
                driver_name=driver.full_name if driver else None,
                driver_email=driver.email if driver else None,
                profile_photo=v.profile_photo,
                license_document=v.license_document,
                license_number=v.license_number,
                license_expiry=v.license_expiry,
                vehicle_registration=v.vehicle_registration,
                status=v.status,
                admin_notes=v.admin_notes,
                rejection_reason=v.rejection_reason,
                submitted_at=v.submitted_at,
                reviewed_at=v.reviewed_at,
            ))
        
        return responses
    
    @staticmethod
    async def get_all_verifications(
        status: VerificationStatus = None,
    ) -> list[VerificationResponse]:
        """Get all verifications with optional status filter."""
        from beanie import PydanticObjectId
        
        if status:
            verifications = await VerificationRepository.get_by_status(status)
        else:
            verifications = await VerificationRepository.get_all()
        
        responses = []
        for v in verifications:
            driver = await User.get(PydanticObjectId(v.driver_id))
            
            responses.append(VerificationResponse(
                id=str(v.id),
                driver_id=v.driver_id,
                driver_name=driver.full_name if driver else None,
                driver_email=driver.email if driver else None,
                profile_photo=v.profile_photo,
                license_document=v.license_document,
                license_number=v.license_number,
                license_expiry=v.license_expiry,
                vehicle_registration=v.vehicle_registration,
                status=v.status,
                admin_notes=v.admin_notes,
                rejection_reason=v.rejection_reason,
                submitted_at=v.submitted_at,
                reviewed_at=v.reviewed_at,
            ))
        
        return responses
    
    @staticmethod
    async def approve_verification(
        verification_id: str,
        admin_id: str,
        notes: str = None,
    ) -> Optional[DriverVerification]:
        """Approve a driver verification."""
        from beanie import PydanticObjectId
        
        verification = await VerificationRepository.update_status(
            verification_id,
            VerificationStatus.APPROVED,
            admin_id,
            notes=notes,
        )
        
        if verification:
            # Update user's verified status
            driver = await User.get(PydanticObjectId(verification.driver_id))
            if driver:
                driver.is_verified = True
                await driver.save()
        
        return verification
    
    @staticmethod
    async def reject_verification(
        verification_id: str,
        admin_id: str,
        reason: str,
        notes: str = None,
    ) -> Optional[DriverVerification]:
        """Reject a driver verification."""
        from beanie import PydanticObjectId
        
        verification = await VerificationRepository.update_status(
            verification_id,
            VerificationStatus.REJECTED,
            admin_id,
            notes=notes,
            rejection_reason=reason,
        )
        
        if verification:
            # Update user's verified status
            driver = await User.get(PydanticObjectId(verification.driver_id))
            if driver:
                driver.is_verified = False
                await driver.save()
        
        return verification
    
    @staticmethod
    async def start_review(
        verification_id: str,
        admin_id: str,
    ) -> Optional[DriverVerification]:
        """Mark verification as under review."""
        return await VerificationRepository.update_status(
            verification_id,
            VerificationStatus.UNDER_REVIEW,
            admin_id,
        )
    
    @staticmethod
    async def get_verification_stats() -> VerificationStats:
        """Get verification statistics."""
        stats = await VerificationRepository.get_stats()
        return VerificationStats(**stats)
    
    @staticmethod
    async def is_driver_verified(driver_id: str) -> bool:
        """Check if a driver is verified."""
        verification = await VerificationRepository.get_by_driver(driver_id)
        return verification is not None and verification.status == VerificationStatus.APPROVED
    
    @staticmethod
    async def get_verification_detail(verification_id: str) -> Optional[tuple[DriverVerification, Optional[User]]]:
        """Get verification with driver info for admin detail view."""
        from beanie import PydanticObjectId
        
        verification = await VerificationRepository.get_by_id(verification_id)
        if not verification:
            return None
        
        driver = await User.get(PydanticObjectId(verification.driver_id))
        return verification, driver

