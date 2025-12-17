"""Verification domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class VerificationStatus(str, Enum):
    """Status of driver verification."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DocumentType(str, Enum):
    """Types of verification documents."""
    PROFILE_PHOTO = "profile_photo"
    DRIVERS_LICENSE = "drivers_license"
    VEHICLE_REGISTRATION = "vehicle_registration"
    INSURANCE = "insurance"
    ID_CARD = "id_card"


# ============== Document Models ==============

class DriverVerification(Document):
    """Driver verification model."""
    
    driver_id: Indexed(str, unique=True)
    
    # Documents (file paths)
    profile_photo: Optional[str] = None
    license_document: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    vehicle_registration: Optional[str] = None
    
    # Status
    status: VerificationStatus = VerificationStatus.PENDING
    
    # Admin review
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # Admin user ID
    expires_at: Optional[datetime] = None
    
    class Settings:
        name = "driver_verifications"
        
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "507f1f77bcf86cd799439011",
                "profile_photo": "/uploads/photos/abc123.jpg",
                "license_document": "/uploads/licenses/def456.pdf",
                "license_number": "DL123456",
                "status": "pending",
            }
        }


class VerificationDocument(Document):
    """Individual verification document."""
    
    verification_id: Indexed(str)
    document_type: DocumentType
    file_path: str
    original_filename: str
    
    # Status
    is_verified: bool = False
    admin_notes: Optional[str] = None
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    
    class Settings:
        name = "verification_documents"


# ============== Pydantic Schemas ==============

class VerificationSubmit(BaseModel):
    """Schema for submitting verification documents."""
    license_number: Optional[str] = Field(default=None, min_length=5)
    license_expiry: Optional[datetime] = None


class VerificationUpdate(BaseModel):
    """Schema for updating verification (admin)."""
    status: Optional[VerificationStatus] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class VerificationResponse(BaseModel):
    """Schema for verification response."""
    id: str
    driver_id: str
    driver_name: Optional[str] = None
    driver_email: Optional[str] = None
    profile_photo: Optional[str] = None
    license_document: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    vehicle_registration: Optional[str] = None
    status: VerificationStatus
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VerificationStats(BaseModel):
    """Schema for verification statistics."""
    total_pending: int
    total_under_review: int
    total_approved: int
    total_rejected: int

