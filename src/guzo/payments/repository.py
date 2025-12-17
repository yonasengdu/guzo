"""Payments domain repository - database operations for payments."""

from datetime import datetime
from typing import Optional, List
from src.guzo.payments.core import Payment, PaymentStatus, PaymentMethod
from src.guzo.infrastructure.repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment database operations."""
    
    def __init__(self):
        super().__init__(Payment)
    
    async def get_by_booking(self, booking_id: str) -> List[Payment]:
        """Get all payments for a booking."""
        return await Payment.find(Payment.booking_id == booking_id).to_list()
    
    async def get_by_customer(self, customer_id: str) -> List[Payment]:
        """Get all payments for a customer."""
        return await Payment.find(
            Payment.customer_id == customer_id
        ).sort("-created_at").to_list()
    
    async def get_by_status(self, status: PaymentStatus, limit: int = 100) -> List[Payment]:
        """Get all payments with a specific status."""
        return await Payment.find(
            Payment.status == status
        ).sort("-created_at").limit(limit).to_list()
    
    async def update_status(
        self, payment_id: str, status: PaymentStatus
    ) -> Optional[Payment]:
        """Update payment status."""
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = status
        payment.updated_at = datetime.utcnow()
        
        if status == PaymentStatus.COMPLETED:
            payment.completed_at = datetime.utcnow()
        
        await payment.save()
        return payment
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        return await Payment.find_one(Payment.transaction_id == transaction_id)
    
    async def get_completed_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Payment]:
        """Get completed payments within a date range."""
        return await Payment.find(
            {
                "status": PaymentStatus.COMPLETED,
                "completed_at": {"$gte": start_date, "$lt": end_date},
            }
        ).sort("-completed_at").to_list()


# Singleton instance
payment_repository = PaymentRepository()

