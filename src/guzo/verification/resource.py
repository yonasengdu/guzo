"""Verification resource - API routes for driver verification."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user, get_current_admin
from src.guzo.verification.core import (
    VerificationStatus,
    VerificationSubmit,
    VerificationResponse,
    VerificationStats,
)
from src.guzo.verification.service import VerificationService

router = APIRouter(prefix="/verification", tags=["Verification"])


# ============== Request/Response Models ==============

class ApproveRequest(BaseModel):
    """Request for approving verification."""
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    """Request for rejecting verification."""
    reason: str
    notes: Optional[str] = None


class VerificationListResponse(BaseModel):
    """Response for verification list with stats."""
    verifications: list[VerificationResponse]
    stats: VerificationStats


class VerificationDetailResponse(BaseModel):
    """Response for verification detail."""
    verification: VerificationResponse
    driver_name: Optional[str] = None
    driver_email: Optional[str] = None
    driver_phone: Optional[str] = None


# ============== Driver Routes ==============

@router.get("/status", response_model=Optional[VerificationResponse])
async def get_verification_status(user: User = Depends(get_current_user)):
    """Get current user's verification status."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can access verification")
    
    verification = await VerificationService.get_driver_verification(str(user.id))
    
    if not verification:
        return None
    
    return VerificationResponse(
        id=str(verification.id),
        driver_id=verification.driver_id,
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


@router.post("/submit", response_model=VerificationResponse)
async def submit_verification(
    user: User = Depends(get_current_user),
    license_number: Optional[str] = None,
    license_expiry: Optional[datetime] = None,
    profile_photo: Optional[UploadFile] = File(None),
    license_document: Optional[UploadFile] = File(None),
    vehicle_registration: Optional[UploadFile] = File(None),
):
    """Submit verification documents."""
    import os
    import uuid
    
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can submit verification")
    
    # Create upload directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded files
    photo_path = None
    license_path = None
    registration_path = None
    
    if profile_photo and profile_photo.filename:
        ext = profile_photo.filename.split(".")[-1]
        photo_path = f"{upload_dir}/photos/{uuid.uuid4()}.{ext}"
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        with open(photo_path, "wb") as f:
            content = await profile_photo.read()
            f.write(content)
    
    if license_document and license_document.filename:
        ext = license_document.filename.split(".")[-1]
        license_path = f"{upload_dir}/licenses/{uuid.uuid4()}.{ext}"
        os.makedirs(os.path.dirname(license_path), exist_ok=True)
        with open(license_path, "wb") as f:
            content = await license_document.read()
            f.write(content)
    
    if vehicle_registration and vehicle_registration.filename:
        ext = vehicle_registration.filename.split(".")[-1]
        registration_path = f"{upload_dir}/registrations/{uuid.uuid4()}.{ext}"
        os.makedirs(os.path.dirname(registration_path), exist_ok=True)
        with open(registration_path, "wb") as f:
            content = await vehicle_registration.read()
            f.write(content)
    
    data = VerificationSubmit(
        license_number=license_number,
        license_expiry=license_expiry,
    )
    
    verification = await VerificationService.submit_verification(
        str(user.id),
        data,
        profile_photo=photo_path,
        license_document=license_path,
        vehicle_registration=registration_path,
    )
    
    return VerificationResponse(
        id=str(verification.id),
        driver_id=verification.driver_id,
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


# ============== Admin Routes ==============

@router.get("/admin/pending", response_model=VerificationListResponse)
async def get_pending_verifications(user: User = Depends(get_current_admin)):
    """Get all pending verifications (admin)."""
    verifications = await VerificationService.get_pending_verifications()
    stats = await VerificationService.get_verification_stats()
    
    return VerificationListResponse(
        verifications=[
            VerificationResponse(
                id=str(v.id),
                driver_id=v.driver_id,
                driver_name=getattr(v, 'driver_name', None),
                driver_email=getattr(v, 'driver_email', None),
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
            )
            for v in verifications
        ],
        stats=stats,
    )


@router.get("/admin/all", response_model=VerificationListResponse)
async def get_all_verifications(
    user: User = Depends(get_current_admin),
    status: Optional[VerificationStatus] = None,
):
    """Get all verifications with optional filter (admin)."""
    verifications = await VerificationService.get_all_verifications(status)
    stats = await VerificationService.get_verification_stats()
    
    return VerificationListResponse(
        verifications=[
            VerificationResponse(
                id=str(v.id),
                driver_id=v.driver_id,
                driver_name=getattr(v, 'driver_name', None),
                driver_email=getattr(v, 'driver_email', None),
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
            )
            for v in verifications
        ],
        stats=stats,
    )


@router.get("/admin/{verification_id}", response_model=VerificationDetailResponse)
async def get_verification_detail(
    verification_id: str,
    user: User = Depends(get_current_admin),
):
    """Get verification detail (admin)."""
    result = await VerificationService.get_verification_detail(verification_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    verification, driver = result
    
    return VerificationDetailResponse(
        verification=VerificationResponse(
            id=str(verification.id),
            driver_id=verification.driver_id,
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
        ),
        driver_name=driver.full_name if driver else None,
        driver_email=driver.email if driver else None,
        driver_phone=driver.phone if driver else None,
    )


@router.patch("/admin/{verification_id}/approve", response_model=VerificationResponse)
async def approve_verification(
    verification_id: str,
    request: ApproveRequest,
    user: User = Depends(get_current_admin),
):
    """Approve a verification (admin). Uses PATCH as this is a state change."""
    verification = await VerificationService.approve_verification(
        verification_id,
        str(user.id),
        notes=request.notes,
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return VerificationResponse(
        id=str(verification.id),
        driver_id=verification.driver_id,
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


@router.patch("/admin/{verification_id}/reject", response_model=VerificationResponse)
async def reject_verification(
    verification_id: str,
    request: RejectRequest,
    user: User = Depends(get_current_admin),
):
    """Reject a verification (admin)."""
    verification = await VerificationService.reject_verification(
        verification_id,
        str(user.id),
        reason=request.reason,
        notes=request.notes,
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return VerificationResponse(
        id=str(verification.id),
        driver_id=verification.driver_id,
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


@router.post("/admin/{verification_id}/review", response_model=VerificationResponse)
async def start_verification_review(
    verification_id: str,
    user: User = Depends(get_current_admin),
):
    """Mark verification as under review (admin)."""
    verification = await VerificationService.start_review(
        verification_id,
        str(user.id),
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return VerificationResponse(
        id=str(verification.id),
        driver_id=verification.driver_id,
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
