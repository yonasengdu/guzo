"""Verification repository - Database operations for verification."""

from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId

from src.guzo.verification.core import (
    DriverVerification,
    VerificationStatus,
    VerificationDocument,
)


class VerificationRepository:
    """Repository for verification database operations."""
    
    @staticmethod
    async def create(verification: DriverVerification) -> DriverVerification:
        """Create a new verification record."""
        await verification.insert()
        return verification
    
    @staticmethod
    async def get_by_id(verification_id: str) -> Optional[DriverVerification]:
        """Get verification by ID."""
        return await DriverVerification.get(PydanticObjectId(verification_id))
    
    @staticmethod
    async def get_by_driver(driver_id: str) -> Optional[DriverVerification]:
        """Get verification for a driver."""
        return await DriverVerification.find_one(
            DriverVerification.driver_id == driver_id
        )
    
    @staticmethod
    async def get_pending() -> list[DriverVerification]:
        """Get all pending verifications."""
        return await DriverVerification.find(
            DriverVerification.status == VerificationStatus.PENDING
        ).sort(DriverVerification.submitted_at).to_list()
    
    @staticmethod
    async def get_under_review() -> list[DriverVerification]:
        """Get all verifications under review."""
        return await DriverVerification.find(
            DriverVerification.status == VerificationStatus.UNDER_REVIEW
        ).sort(DriverVerification.submitted_at).to_list()
    
    @staticmethod
    async def get_by_status(status: VerificationStatus) -> list[DriverVerification]:
        """Get verifications by status."""
        return await DriverVerification.find(
            DriverVerification.status == status
        ).sort(-DriverVerification.submitted_at).to_list()
    
    @staticmethod
    async def get_all(limit: int = 100) -> list[DriverVerification]:
        """Get all verifications."""
        return await DriverVerification.find_all().sort(
            -DriverVerification.submitted_at
        ).limit(limit).to_list()
    
    @staticmethod
    async def update(
        verification_id: str,
        data: dict,
    ) -> Optional[DriverVerification]:
        """Update a verification."""
        verification = await DriverVerification.get(PydanticObjectId(verification_id))
        if verification:
            for key, value in data.items():
                if value is not None:
                    setattr(verification, key, value)
            await verification.save()
        return verification
    
    @staticmethod
    async def update_status(
        verification_id: str,
        status: VerificationStatus,
        admin_id: str,
        notes: str = None,
        rejection_reason: str = None,
    ) -> Optional[DriverVerification]:
        """Update verification status."""
        verification = await DriverVerification.get(PydanticObjectId(verification_id))
        if verification:
            verification.status = status
            verification.reviewed_at = datetime.utcnow()
            verification.reviewed_by = admin_id
            if notes:
                verification.admin_notes = notes
            if rejection_reason:
                verification.rejection_reason = rejection_reason
            await verification.save()
        return verification
    
    @staticmethod
    async def get_stats() -> dict:
        """Get verification statistics."""
        pending = await DriverVerification.find(
            DriverVerification.status == VerificationStatus.PENDING
        ).count()
        under_review = await DriverVerification.find(
            DriverVerification.status == VerificationStatus.UNDER_REVIEW
        ).count()
        approved = await DriverVerification.find(
            DriverVerification.status == VerificationStatus.APPROVED
        ).count()
        rejected = await DriverVerification.find(
            DriverVerification.status == VerificationStatus.REJECTED
        ).count()
        
        return {
            "total_pending": pending,
            "total_under_review": under_review,
            "total_approved": approved,
            "total_rejected": rejected,
        }


class VerificationDocumentRepository:
    """Repository for verification documents."""
    
    @staticmethod
    async def create(doc: VerificationDocument) -> VerificationDocument:
        """Create a new verification document."""
        await doc.insert()
        return doc
    
    @staticmethod
    async def get_by_verification(verification_id: str) -> list[VerificationDocument]:
        """Get all documents for a verification."""
        return await VerificationDocument.find(
            VerificationDocument.verification_id == verification_id
        ).to_list()
    
    @staticmethod
    async def delete_by_verification(verification_id: str) -> int:
        """Delete all documents for a verification."""
        docs = await VerificationDocument.find(
            VerificationDocument.verification_id == verification_id
        ).to_list()
        for doc in docs:
            await doc.delete()
        return len(docs)

