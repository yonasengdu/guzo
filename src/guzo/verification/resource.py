"""Verification resource - API routes for driver verification."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user, get_current_admin
from src.guzo.verification.core import VerificationStatus, VerificationSubmit
from src.guzo.verification.service import VerificationService

router = APIRouter(prefix="/verification", tags=["Verification"])
templates = Jinja2Templates(directory="src/guzo/templates")


# ============== Driver Routes ==============

@router.get("/status", response_class=HTMLResponse)
async def get_verification_status(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Get current user's verification status."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can access verification")
    
    verification = await VerificationService.get_driver_verification(str(user.id))
    
    return templates.TemplateResponse(
        "partials/verification_status.html",
        {
            "request": request,
            "verification": verification,
            "user": user,
        },
    )


@router.get("/form", response_class=HTMLResponse)
async def get_verification_form(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Get verification document upload form."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can access verification")
    
    verification = await VerificationService.get_driver_verification(str(user.id))
    
    return templates.TemplateResponse(
        "partials/verification_form.html",
        {
            "request": request,
            "verification": verification,
            "user": user,
        },
    )


@router.post("/submit", response_class=HTMLResponse)
async def submit_verification(
    request: Request,
    user: User = Depends(get_current_user),
    license_number: Optional[str] = Form(None),
    license_expiry: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    license_document: Optional[UploadFile] = File(None),
    vehicle_registration: Optional[UploadFile] = File(None),
):
    """Submit verification documents."""
    from src.guzo.verification.service import VerificationService
    import os
    import uuid
    
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can submit verification")
    
    # Create upload directory if it doesn't exist
    upload_dir = "static/uploads"
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
    
    # Parse license expiry
    from datetime import datetime
    expiry = None
    if license_expiry:
        try:
            expiry = datetime.fromisoformat(license_expiry)
        except ValueError:
            pass
    
    data = VerificationSubmit(
        license_number=license_number,
        license_expiry=expiry,
    )
    
    verification = await VerificationService.submit_verification(
        str(user.id),
        data,
        profile_photo=photo_path,
        license_document=license_path,
        vehicle_registration=registration_path,
    )
    
    return templates.TemplateResponse(
        "partials/verification_submitted.html",
        {
            "request": request,
            "verification": verification,
        },
    )


# ============== Admin Routes ==============

@router.get("/admin/pending", response_class=HTMLResponse)
async def get_pending_verifications(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Get all pending verifications (admin)."""
    verifications = await VerificationService.get_pending_verifications()
    stats = await VerificationService.get_verification_stats()
    
    return templates.TemplateResponse(
        "partials/admin_verifications.html",
        {
            "request": request,
            "verifications": verifications,
            "stats": stats,
            "user": user,
        },
    )


@router.get("/admin/all", response_class=HTMLResponse)
async def get_all_verifications(
    request: Request,
    user: User = Depends(get_current_admin),
    status: Optional[str] = None,
):
    """Get all verifications with optional filter (admin)."""
    ver_status = VerificationStatus(status) if status else None
    verifications = await VerificationService.get_all_verifications(ver_status)
    stats = await VerificationService.get_verification_stats()
    
    return templates.TemplateResponse(
        "partials/admin_verifications.html",
        {
            "request": request,
            "verifications": verifications,
            "stats": stats,
            "filter_status": status,
            "user": user,
        },
    )


@router.get("/admin/{verification_id}", response_class=HTMLResponse)
async def get_verification_detail(
    request: Request,
    verification_id: str,
    user: User = Depends(get_current_admin),
):
    """Get verification detail (admin)."""
    from beanie import PydanticObjectId
    from src.guzo.verification.repository import VerificationRepository
    
    verification = await VerificationRepository.get_by_id(verification_id)
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    driver = await User.get(PydanticObjectId(verification.driver_id))
    
    return templates.TemplateResponse(
        "partials/verification_detail.html",
        {
            "request": request,
            "verification": verification,
            "driver": driver,
            "user": user,
        },
    )


@router.post("/admin/{verification_id}/approve", response_class=HTMLResponse)
async def approve_verification(
    request: Request,
    verification_id: str,
    user: User = Depends(get_current_admin),
    notes: Optional[str] = Form(None),
):
    """Approve a verification (admin)."""
    verification = await VerificationService.approve_verification(
        verification_id,
        str(user.id),
        notes=notes,
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return HTMLResponse(
        '<span class="badge-apple badge-success">Approved</span>'
    )


@router.post("/admin/{verification_id}/reject", response_class=HTMLResponse)
async def reject_verification(
    request: Request,
    verification_id: str,
    user: User = Depends(get_current_admin),
    reason: str = Form(...),
    notes: Optional[str] = Form(None),
):
    """Reject a verification (admin)."""
    verification = await VerificationService.reject_verification(
        verification_id,
        str(user.id),
        reason=reason,
        notes=notes,
    )
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return HTMLResponse(
        '<span class="badge-apple badge-error">Rejected</span>'
    )


@router.post("/admin/{verification_id}/review", response_class=HTMLResponse)
async def start_verification_review(
    request: Request,
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
    
    return HTMLResponse(
        '<span class="badge-apple badge-warning">Under Review</span>'
    )

