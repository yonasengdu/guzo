"""Reviews service - Business logic for reviews."""

from typing import Optional

from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import Booking, BookingStatus
from src.guzo.reviews.core import Review, ReviewCreate, ReviewResponse
from src.guzo.reviews.repository import ReviewRepository


class ReviewService:
    """Service for review business logic."""
    
    @staticmethod
    async def create_review(
        data: ReviewCreate,
        reviewer: User,
    ) -> Optional[Review]:
        """Create a new review for a completed booking."""
        from beanie import PydanticObjectId
        
        # Verify booking exists and is completed
        booking = await Booking.get(PydanticObjectId(data.booking_id))
        if not booking or booking.status != BookingStatus.COMPLETED:
            return None
        
        # Check if user is part of this booking
        is_customer = str(booking.customer_id) == str(reviewer.id)
        is_driver = str(booking.assigned_driver_id) == str(reviewer.id)
        
        if not (is_customer or is_driver):
            return None
        
        # Check if review already exists
        existing = await ReviewRepository.get_by_booking_and_reviewer(
            data.booking_id, str(reviewer.id)
        )
        if existing:
            return None
        
        # Create review
        review = Review(
            booking_id=data.booking_id,
            reviewer_id=str(reviewer.id),
            reviewee_id=data.reviewee_id,
            reviewer_role=reviewer.role,
            rating=data.rating,
            comment=data.comment,
        )
        
        await ReviewRepository.create(review)
        
        # Update reviewee's average rating
        await ReviewService.update_user_rating(data.reviewee_id)
        
        # Update booking with review reference
        if reviewer.role == UserRole.RIDER:
            booking.customer_review_id = str(review.id)
        else:
            booking.driver_review_id = str(review.id)
        await booking.save()
        
        return review
    
    @staticmethod
    async def update_user_rating(user_id: str) -> None:
        """Update a user's average rating based on reviews."""
        from beanie import PydanticObjectId
        
        avg_rating, total_count = await ReviewRepository.get_average_rating(user_id)
        
        user = await User.get(PydanticObjectId(user_id))
        if user:
            user.rating = avg_rating
            user.total_ratings = total_count
            await user.save()
    
    @staticmethod
    async def get_reviews_for_user(
        user_id: str,
        limit: int = 50,
    ) -> list[ReviewResponse]:
        """Get reviews received by a user with reviewer info."""
        reviews = await ReviewRepository.get_reviews_for_user(user_id, limit)
        
        responses = []
        for review in reviews:
            from beanie import PydanticObjectId
            reviewer = await User.get(PydanticObjectId(review.reviewer_id))
            
            responses.append(ReviewResponse(
                id=str(review.id),
                booking_id=review.booking_id,
                reviewer_id=review.reviewer_id,
                reviewee_id=review.reviewee_id,
                reviewer_role=review.reviewer_role,
                reviewer_name=reviewer.full_name if reviewer else "Unknown",
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at,
            ))
        
        return responses
    
    @staticmethod
    async def get_pending_reviews(user: User) -> list[dict]:
        """Get bookings that need a review from this user."""
        from beanie import PydanticObjectId
        
        # Get completed bookings for this user
        if user.role == UserRole.RIDER:
            bookings = await Booking.find(
                Booking.customer_id == str(user.id),
                Booking.status == BookingStatus.COMPLETED,
                Booking.customer_review_id == None,
            ).to_list()
        else:
            bookings = await Booking.find(
                Booking.assigned_driver_id == str(user.id),
                Booking.status == BookingStatus.COMPLETED,
                Booking.driver_review_id == None,
            ).to_list()
        
        pending = []
        for booking in bookings:
            # Get the other party's info
            if user.role == UserRole.RIDER:
                other_id = booking.assigned_driver_id
            else:
                other_id = booking.customer_id
            
            if other_id:
                other_user = await User.get(PydanticObjectId(other_id))
                pending.append({
                    "booking": booking,
                    "reviewee": other_user,
                })
        
        return pending
    
    @staticmethod
    async def can_review_booking(user: User, booking_id: str) -> bool:
        """Check if user can review a specific booking."""
        from beanie import PydanticObjectId
        
        booking = await Booking.get(PydanticObjectId(booking_id))
        if not booking or booking.status != BookingStatus.COMPLETED:
            return False
        
        # Check if user is part of booking
        is_customer = str(booking.customer_id) == str(user.id)
        is_driver = str(booking.assigned_driver_id) == str(user.id)
        
        if not (is_customer or is_driver):
            return False
        
        # Check if already reviewed
        existing = await ReviewRepository.get_by_booking_and_reviewer(
            booking_id, str(user.id)
        )
        
        return existing is None

