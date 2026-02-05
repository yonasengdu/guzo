"""Wallet domain models and schemas - Token-based payment system for drivers."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from beanie import Document, Indexed
from pydantic import BaseModel, Field, field_validator


# ============== Enums ==============

class TokenTransactionType(str, Enum):
    """Types of token transactions."""
    PURCHASE = "purchase"      # Driver bought tokens
    TRIP_FEE = "trip_fee"      # Deducted for completed trip
    REFUND = "refund"          # Refund for cancelled trip
    BONUS = "bonus"            # Promotional tokens
    ADJUSTMENT = "adjustment"  # Admin adjustment


# ============== Document Models ==============

class DriverWallet(Document):
    """Driver wallet model - stores token balance."""
    
    driver_id: Indexed(str, unique=True)  # Reference to User (driver)
    
    # Balance
    token_balance: int = Field(default=0, ge=0)
    
    # Lifetime stats
    total_purchased: int = Field(default=0, ge=0)
    total_spent: int = Field(default=0, ge=0)
    total_bonus: int = Field(default=0, ge=0)
    
    # Settings
    low_balance_threshold: int = Field(default=50, ge=0)
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "driver_wallets"
        
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "507f1f77bcf86cd799439011",
                "token_balance": 500,
                "low_balance_threshold": 50,
            }
        }
    
    @property
    def is_low_balance(self) -> bool:
        """Check if balance is below threshold."""
        return self.token_balance < self.low_balance_threshold


class TokenTransaction(Document):
    """Token transaction history."""
    
    driver_id: Indexed(str)  # Reference to User (driver)
    wallet_id: str  # Reference to DriverWallet
    
    # Transaction details
    transaction_type: TokenTransactionType
    amount: int  # Positive for credit, negative for debit
    balance_after: int  # Balance after this transaction
    
    # For purchases
    payment_reference: Optional[str] = None  # Receipt number, bank ref, etc.
    payment_amount_etb: Optional[float] = None  # Amount paid in ETB
    admin_id: Optional[str] = None  # Admin who processed the purchase
    
    # For trip fees
    trip_id: Optional[str] = None
    booking_count: Optional[int] = None  # Number of bookings on the trip
    
    # Metadata
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "token_transactions"
        indexes = [
            "driver_id",
            "wallet_id",
            "created_at",
            [("driver_id", 1), ("created_at", -1)],  # For transaction history
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "507f1f77bcf86cd799439011",
                "transaction_type": "purchase",
                "amount": 500,
                "balance_after": 500,
                "payment_reference": "TXN-12345",
            }
        }


class TokenPackage(Document):
    """Token package - predefined token bundles for purchase."""
    
    name: str  # "Starter", "Standard", "Premium"
    description: Optional[str] = None
    
    # Token amounts
    tokens: int = Field(gt=0)
    bonus_tokens: int = Field(default=0, ge=0)
    
    # Pricing
    price_etb: float = Field(gt=0)
    
    # Validity
    is_active: bool = True
    sort_order: int = Field(default=0)  # For display ordering
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "token_packages"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Standard",
                "description": "Best value for regular drivers",
                "tokens": 500,
                "bonus_tokens": 25,
                "price_etb": 900.00,
            }
        }
    
    @property
    def total_tokens(self) -> int:
        """Total tokens including bonus."""
        return self.tokens + self.bonus_tokens
    
    @property
    def price_per_token(self) -> float:
        """Price per token (including bonus)."""
        return round(self.price_etb / self.total_tokens, 2)


class PlatformFeeConfig(Document):
    """Platform fee configuration - how many tokens to charge per trip."""
    
    # Fee structure
    fee_per_seat: int = Field(default=5, ge=0)  # Tokens per booked seat
    fee_per_trip: int = Field(default=0, ge=0)  # Fixed tokens per trip
    
    # Minimum balance required to accept trips
    minimum_balance_required: int = Field(default=20, ge=0)
    
    # Active configuration
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "platform_fee_config"
        
    class Config:
        json_schema_extra = {
            "example": {
                "fee_per_seat": 5,
                "fee_per_trip": 0,
                "minimum_balance_required": 20,
            }
        }
    
    def calculate_fee(self, booked_seats: int) -> int:
        """Calculate total fee for a trip based on booked seats."""
        return self.fee_per_trip + (self.fee_per_seat * booked_seats)


# ============== Pydantic Schemas ==============

class WalletResponse(BaseModel):
    """Response schema for driver wallet."""
    id: str
    driver_id: str
    token_balance: int
    total_purchased: int
    total_spent: int
    total_bonus: int
    low_balance_threshold: int
    is_low_balance: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Response schema for token transaction."""
    id: str
    driver_id: str
    transaction_type: TokenTransactionType
    amount: int
    balance_after: int
    payment_reference: Optional[str] = None
    payment_amount_etb: Optional[float] = None
    trip_id: Optional[str] = None
    booking_count: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    """Response schema for token package."""
    id: str
    name: str
    description: Optional[str] = None
    tokens: int
    bonus_tokens: int
    total_tokens: int
    price_etb: float
    price_per_token: float
    is_active: bool
    
    class Config:
        from_attributes = True


class FeeConfigResponse(BaseModel):
    """Response schema for platform fee configuration."""
    fee_per_seat: int
    fee_per_trip: int
    minimum_balance_required: int
    
    class Config:
        from_attributes = True


# ============== Request Schemas ==============

class PurchaseTokensRequest(BaseModel):
    """Request schema for admin to credit tokens to a driver."""
    driver_id: str
    package_id: str
    payment_reference: str  # Receipt number, bank ref, etc.
    notes: Optional[str] = None


class ManualCreditRequest(BaseModel):
    """Request schema for admin to manually credit/debit tokens."""
    driver_id: str
    amount: int  # Positive for credit, negative for debit
    transaction_type: TokenTransactionType = TokenTransactionType.ADJUSTMENT
    description: str
    notes: Optional[str] = None
    
    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v


class CreatePackageRequest(BaseModel):
    """Request schema for creating a token package."""
    name: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)
    tokens: int = Field(gt=0)
    bonus_tokens: int = Field(default=0, ge=0)
    price_etb: float = Field(gt=0)
    sort_order: int = Field(default=0)
    
    @field_validator("price_etb")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 2)


class UpdatePackageRequest(BaseModel):
    """Request schema for updating a token package."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)
    tokens: Optional[int] = Field(default=None, gt=0)
    bonus_tokens: Optional[int] = Field(default=None, ge=0)
    price_etb: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class UpdateFeeConfigRequest(BaseModel):
    """Request schema for updating platform fee configuration."""
    fee_per_seat: Optional[int] = Field(default=None, ge=0)
    fee_per_trip: Optional[int] = Field(default=None, ge=0)
    minimum_balance_required: Optional[int] = Field(default=None, ge=0)


class UpdateWalletSettingsRequest(BaseModel):
    """Request schema for driver to update their wallet settings."""
    low_balance_threshold: int = Field(ge=0, le=1000)
