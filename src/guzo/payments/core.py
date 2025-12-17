"""Payments domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class PaymentStatus(str, Enum):
    """Status of a payment."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment methods available."""
    CASH = "cash"
    TELEBIRR = "telebirr"
    EBIRR = "ebirr"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"


# ============== Document Models ==============

class Payment(Document):
    """Payment record model."""
    
    booking_id: Indexed(str)  # Reference to Booking
    customer_id: Optional[str] = None  # Reference to User
    
    # Amount
    amount: float = Field(gt=0)
    currency: str = "ETB"
    
    # Payment details
    payment_method: PaymentMethod = PaymentMethod.CASH
    status: PaymentStatus = PaymentStatus.PENDING
    
    # Transaction info
    transaction_id: Optional[str] = None
    transaction_ref: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "payments"
        
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "507f1f77bcf86cd799439011",
                "amount": 1600.00,
                "payment_method": "telebirr",
            }
        }


# ============== Pydantic Schemas ==============

class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    booking_id: str
    amount: float = Field(gt=0)
    payment_method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: str
    booking_id: str
    customer_id: Optional[str] = None
    amount: float
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str] = None
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
