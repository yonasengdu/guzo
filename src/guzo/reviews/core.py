"""Reviews domain models and schemas."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field

from src.guzo.auth.core import UserRole


# ============== Document Models ==============

class Review(Document):
    """Review model for two-way rating system."""
    
    booking_id: Indexed(str)  # Links to completed booking
    reviewer_id: Indexed(str)  # User who gave review
    reviewee_id: Indexed(str)  # User being reviewed
    reviewer_role: UserRole  # RIDER or DRIVER
    
    # Rating
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    comment: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "reviews"
        
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "507f1f77bcf86cd799439011",
                "reviewer_id": "507f1f77bcf86cd799439012",
                "reviewee_id": "507f1f77bcf86cd799439013",
                "reviewer_role": "rider",
                "rating": 5,
                "comment": "Great driver, very punctual!",
            }
        }


# ============== Pydantic Schemas ==============

class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    booking_id: str
    reviewee_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: str
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    reviewer_role: UserRole
    reviewer_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

