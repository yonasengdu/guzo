"""Reviews resource - API routes for reviews."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.guzo.auth.core import User
from src.guzo.middleware import get_current_user
from src.guzo.reviews.core import ReviewCreate
from src.guzo.reviews.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("/pending", response_class=HTMLResponse)
async def get_pending_reviews(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Get pending reviews for current user."""
    pending = await ReviewService.get_pending_reviews(user)
    
    return templates.TemplateResponse(
        "partials/pending_reviews.html",
        {
            "request": request,
            "pending_reviews": pending,
            "user": user,
        },
    )


@router.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user_reviews(
    request: Request,
    user_id: str,
    user: User = Depends(get_current_user),
):
    """Get reviews for a specific user."""
    reviews = await ReviewService.get_reviews_for_user(user_id)
    
    return templates.TemplateResponse(
        "partials/user_reviews.html",
        {
            "request": request,
            "reviews": reviews,
            "user": user,
        },
    )


@router.post("", response_class=HTMLResponse)
async def create_review(
    request: Request,
    user: User = Depends(get_current_user),
    booking_id: str = Form(...),
    reviewee_id: str = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
):
    """Submit a review for a completed booking."""
    # Validate rating
    if rating < 1 or rating > 5:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "message": "Rating must be between 1 and 5",
            },
            status_code=400,
        )
    
    review_data = ReviewCreate(
        booking_id=booking_id,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment,
    )
    
    review = await ReviewService.create_review(review_data, user)
    
    if not review:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "message": "Unable to create review. You may have already reviewed this booking.",
            },
            status_code=400,
        )
    
    return templates.TemplateResponse(
        "partials/review_success.html",
        {
            "request": request,
            "review": review,
        },
    )


@router.get("/form/{booking_id}", response_class=HTMLResponse)
async def get_review_form(
    request: Request,
    booking_id: str,
    reviewee_id: str,
    user: User = Depends(get_current_user),
):
    """Get the review form for a booking."""
    from beanie import PydanticObjectId
    from src.guzo.auth.core import User as UserModel
    
    can_review = await ReviewService.can_review_booking(user, booking_id)
    
    if not can_review:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "message": "You cannot review this booking.",
            },
            status_code=400,
        )
    
    reviewee = await UserModel.get(PydanticObjectId(reviewee_id))
    
    return templates.TemplateResponse(
        "partials/review_form.html",
        {
            "request": request,
            "booking_id": booking_id,
            "reviewee": reviewee,
            "user": user,
        },
    )

