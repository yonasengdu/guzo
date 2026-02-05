"""Reviews resource - API routes for reviews."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.guzo.auth.core import User, UserResponse
from src.guzo.middleware import get_current_user
from src.guzo.reviews.core import ReviewCreate, ReviewResponse
from src.guzo.reviews.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ============== Request/Response Models ==============

class CanReviewResponse(BaseModel):
    """Response for can review check."""
    can_review: bool
    reviewee_id: Optional[str] = None
    reviewee_name: Optional[str] = None


class PendingReview(BaseModel):
    """Pending review info."""
    booking_id: str
    reviewee_id: str
    reviewee_name: Optional[str] = None
    pickup_location: str
    dropoff_location: str


# ============== Endpoints ==============

@router.get("/pending", response_model=list[PendingReview])
async def get_pending_reviews(user: User = Depends(get_current_user)):
    """Get pending reviews for current user."""
    pending = await ReviewService.get_pending_reviews(user)
    return [
        PendingReview(
            booking_id=str(p.get('booking_id', '')),
            reviewee_id=str(p.get('reviewee_id', '')),
            reviewee_name=p.get('reviewee_name'),
            pickup_location=p.get('pickup_location', ''),
            dropoff_location=p.get('dropoff_location', ''),
        )
        for p in pending
    ] if pending else []


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(
    user_id: str,
    user: User = Depends(get_current_user),
):
    """Get reviews for a specific user."""
    reviews = await ReviewService.get_reviews_for_user(user_id)
    return [
        ReviewResponse(
            id=str(r.id),
            booking_id=r.booking_id,
            reviewer_id=r.reviewer_id,
            reviewee_id=r.reviewee_id,
            reviewer_role=r.reviewer_role,
            reviewer_name=getattr(r, 'reviewer_name', None),
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in reviews
    ]


@router.post("", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    user: User = Depends(get_current_user),
):
    """Submit a review for a completed booking."""
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    review = await ReviewService.create_review(review_data, user)
    
    if not review:
        raise HTTPException(
            status_code=400,
            detail="Unable to create review. You may have already reviewed this booking.",
        )
    
    return ReviewResponse(
        id=str(review.id),
        booking_id=review.booking_id,
        reviewer_id=review.reviewer_id,
        reviewee_id=review.reviewee_id,
        reviewer_role=review.reviewer_role,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.get("/can-review/{booking_id}", response_model=CanReviewResponse)
async def check_can_review(
    booking_id: str,
    user: User = Depends(get_current_user),
):
    """Check if user can review a booking."""
    from beanie import PydanticObjectId
    from src.guzo.bookings.service import BookingService
    
    can_review = await ReviewService.can_review_booking(user, booking_id)
    
    if not can_review:
        return CanReviewResponse(can_review=False)
    
    # Get booking to find reviewee
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        return CanReviewResponse(can_review=False)
    
    # Determine reviewee based on user role
    reviewee_id = None
    reviewee_name = None
    
    if str(user.id) == booking.customer_id:
        # Customer reviewing driver
        reviewee_id = booking.assigned_driver_id
        if reviewee_id:
            from src.guzo.auth.core import User as UserModel
            driver = await UserModel.get(PydanticObjectId(reviewee_id))
            if driver:
                reviewee_name = driver.full_name
    else:
        # Driver reviewing customer
        reviewee_id = booking.customer_id
        if reviewee_id:
            from src.guzo.auth.core import User as UserModel
            customer = await UserModel.get(PydanticObjectId(reviewee_id))
            if customer:
                reviewee_name = customer.full_name
    
    return CanReviewResponse(
        can_review=True,
        reviewee_id=reviewee_id,
        reviewee_name=reviewee_name,
    )
