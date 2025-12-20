"""Payments domain resource - API routes for payments."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.guzo.auth.core import User, UserRole
from src.guzo.payments.core import PaymentMethod, PaymentCreate, PaymentUpdate, PaymentResponse
from src.guzo.payments.service import PaymentService
from src.guzo.middleware import get_current_user_required, get_current_admin

router = APIRouter(prefix="/payments", tags=["Payments"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("", response_model=list[PaymentResponse])
async def get_my_payments(user: User = Depends(get_current_user_required)):
    """Get all payments for the current user."""
    payments = await PaymentService.get_customer_payments(str(user.id))
    return [
        PaymentResponse(
            id=str(p.id),
            booking_id=p.booking_id,
            customer_id=p.customer_id,
            amount=p.amount,
            currency=p.currency,
            payment_method=p.payment_method,
            status=p.status,
            transaction_id=p.transaction_id,
            transaction_ref=p.transaction_ref,
            notes=p.notes,
            created_at=p.created_at,
            completed_at=p.completed_at,
        )
        for p in payments
    ]


@router.post("", response_model=PaymentResponse)
async def create_payment(
    request: Request,
    user: User = Depends(get_current_user_required),
    booking_id: str = Form(...),
    amount: float = Form(...),
    payment_method: str = Form("cash"),
    notes: Optional[str] = Form(None),
):
    """Create a new payment."""
    try:
        payment_data = PaymentCreate(
            booking_id=booking_id,
            amount=float(amount),
            payment_method=PaymentMethod(payment_method),
            notes=notes,
        )
        
        payment = await PaymentService.create_payment(
            payment_data,
            customer_id=str(user.id),
        )
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/payment_success.html",
                {
                    "request": request,
                    "amount": amount,
                    "method": payment_method,
                },
            )
        
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
        
    except Exception as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get a specific payment."""
    payment = await PaymentService.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Only allow access to own payments (or admin)
    if payment.customer_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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


@router.get("/booking/{booking_id}", response_model=list[PaymentResponse])
async def get_booking_payments(
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get all payments for a booking."""
    payments = await PaymentService.get_booking_payments(booking_id)
    return [
        PaymentResponse(
            id=str(p.id),
            booking_id=p.booking_id,
            customer_id=p.customer_id,
            amount=p.amount,
            currency=p.currency,
            payment_method=p.payment_method,
            status=p.status,
            transaction_id=p.transaction_id,
            transaction_ref=p.transaction_ref,
            notes=p.notes,
            created_at=p.created_at,
            completed_at=p.completed_at,
        )
        for p in payments
    ]


@router.post("/{payment_id}/complete")
async def complete_payment(
    request: Request,
    payment_id: str,
    user: User = Depends(get_current_admin),
    transaction_ref: Optional[str] = Form(None),
):
    """Mark a payment as completed (admin only)."""
    payment = await PaymentService.complete_payment(payment_id, transaction_ref)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge badge-success">Completed</span>')
    
    return {"status": "completed"}

