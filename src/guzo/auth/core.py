"""Auth domain models and schemas."""

import re
from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============== Constants ==============

# Supported languages
class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    AMHARIC = "am"


# Phone number regex for Ethiopian numbers
PHONE_REGEX = re.compile(r"^\+?251[97]\d{8}$|^0[97]\d{8}$")


# ============== Enums ==============

class UserRole(str, Enum):
    """User roles in the system."""
    RIDER = "rider"
    DRIVER = "driver"
    ADMIN = "admin"


class VerificationStatus(str, Enum):
    """Driver verification status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============== Document Models ==============

class User(Document):
    """User model for riders, drivers, and admins."""
    
    email: Indexed(EmailStr, unique=True)
    phone: Indexed(str, unique=True)
    full_name: str
    role: UserRole = UserRole.RIDER
    password_hash: str
    
    # Status flags
    is_active: bool = True
    is_verified: bool = False
    is_online: bool = False  # For drivers - availability status
    
    # Profile info (rating is None until user receives reviews)
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    total_ratings: int = 0
    language: str = "en"  # en or am (Amharic)
    profile_image: Optional[str] = None
    
    # Driver-specific fields
    license_number: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    documents_submitted_at: Optional[datetime] = None
    
    # Schedule/availability (for drivers)
    schedule: dict = Field(default_factory=dict)  # {"monday": {"start": "08:00", "end": "18:00"}, ...}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"
        
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone": "+251911234567",
                "full_name": "Abebe Kebede",
                "role": "rider",
            }
        }


# ============== Pydantic Schemas ==============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6)
    role: UserRole = UserRole.RIDER
    language: Language = Language.ENGLISH
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Ethiopian phone number format."""
        # Normalize phone number
        phone = v.strip()
        if not PHONE_REGEX.match(phone):
            raise ValueError(
                "Invalid phone number format. Expected Ethiopian format: "
                "+251911234567 or 0911234567"
            )
        return phone


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: EmailStr
    phone: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    is_online: bool
    rating: Optional[float] = None  # None until user receives reviews
    total_ratings: int
    language: str
    profile_image: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    is_online: Optional[bool] = None  # For drivers
    profile_image: Optional[str] = None
    schedule: Optional[dict] = None  # For drivers


class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

