"""Payments domain service - business logic for payments."""

from datetime import datetime
from typing import Optional, List
from src.guzo.payments.core import (
    Payment, PaymentStatus, PaymentMethod,
    PaymentCreate, PaymentUpdate, PaymentResponse
)
from src.guzo.payments.repository import payment_repository


class PaymentService:
    """Service for managing payments."""
    
    @staticmethod
    async def create_payment(
        payment_data: PaymentCreate,
        customer_id: Optional[str] = None
    ) -> Payment:
        """Create a new payment."""
        payment = Payment(
            booking_id=payment_data.booking_id,
            customer_id=customer_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            notes=payment_data.notes,
        )
        await payment_repository.create(payment)
        return payment
    
    @staticmethod
    async def get_payment(payment_id: str) -> Optional[Payment]:
        """Get a payment by ID."""
        return await payment_repository.get_by_id(payment_id)
    
    @staticmethod
    async def update_payment(
        payment_id: str,
        payment_data: PaymentUpdate
    ) -> Optional[Payment]:
        """Update a payment."""
        update_data = payment_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            if "status" in update_data and update_data["status"] == PaymentStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
            
            return await payment_repository.update(payment_id, update_data)
        return await payment_repository.get_by_id(payment_id)
    
    @staticmethod
    async def complete_payment(payment_id: str, transaction_ref: Optional[str] = None) -> Optional[Payment]:
        """Mark a payment as completed."""
        payment = await payment_repository.get_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()
        if transaction_ref:
            payment.transaction_ref = transaction_ref
        
        await payment.save()
        return payment
    
    @staticmethod
    async def fail_payment(payment_id: str, reason: Optional[str] = None) -> Optional[Payment]:
        """Mark a payment as failed."""
        payment = await payment_repository.get_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = PaymentStatus.FAILED
        payment.updated_at = datetime.utcnow()
        if reason:
            payment.notes = (payment.notes or "") + f"\nFailed: {reason}"
        
        await payment.save()
        return payment
    
    @staticmethod
    async def get_booking_payments(booking_id: str) -> List[Payment]:
        """Get all payments for a booking."""
        return await payment_repository.get_by_booking(booking_id)
    
    @staticmethod
    async def get_customer_payments(customer_id: str) -> List[Payment]:
        """Get all payments for a customer."""
        return await payment_repository.get_by_customer(customer_id)
    
    @staticmethod
    async def get_payment_response(payment_id: str) -> Optional[PaymentResponse]:
        """Get payment response."""
        payment = await payment_repository.get_by_id(payment_id)
        if not payment:
            return None
        
        return PaymentResponse(
            id=str(payment.id),
            booking_id=payment.booking_id,
            customer_id=payment.customer_id,
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            status=payment.status,
            transaction_id=payment.transaction_id,
            transaction_ref=payment.transaction_ref,
            notes=payment.notes,
            created_at=payment.created_at,
            completed_at=payment.completed_at,
        )
    
    @staticmethod
    async def calculate_earnings(
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """Calculate earnings within a date range."""
        payments = await payment_repository.get_completed_by_date_range(start_date, end_date)
        
        total = sum(p.amount for p in payments)
        by_method = {}
        for payment in payments:
            method = payment.payment_method.value
            if method not in by_method:
                by_method[method] = 0.0
            by_method[method] += payment.amount
        
        return {
            "total": total,
            "count": len(payments),
            "by_method": by_method,
        }

