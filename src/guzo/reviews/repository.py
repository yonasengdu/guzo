"""Reviews repository - Database operations for reviews."""

from typing import Optional
from beanie import PydanticObjectId

from src.guzo.reviews.core import Review


class ReviewRepository:
    """Repository for review database operations."""
    
    @staticmethod
    async def create(review: Review) -> Review:
        """Create a new review."""
        await review.insert()
        return review
    
    @staticmethod
    async def get_by_id(review_id: str) -> Optional[Review]:
        """Get review by ID."""
        return await Review.get(PydanticObjectId(review_id))
    
    @staticmethod
    async def get_by_booking(booking_id: str) -> list[Review]:
        """Get all reviews for a booking."""
        return await Review.find(Review.booking_id == booking_id).to_list()
    
    @staticmethod
    async def get_by_booking_and_reviewer(
        booking_id: str, reviewer_id: str
    ) -> Optional[Review]:
        """Get a specific review by booking and reviewer."""
        return await Review.find_one(
            Review.booking_id == booking_id,
            Review.reviewer_id == reviewer_id
        )
    
    @staticmethod
    async def get_reviews_for_user(user_id: str, limit: int = 50) -> list[Review]:
        """Get reviews received by a user."""
        return await Review.find(
            Review.reviewee_id == user_id
        ).sort(-Review.created_at).limit(limit).to_list()
    
    @staticmethod
    async def get_reviews_by_user(user_id: str, limit: int = 50) -> list[Review]:
        """Get reviews given by a user."""
        return await Review.find(
            Review.reviewer_id == user_id
        ).sort(-Review.created_at).limit(limit).to_list()
    
    @staticmethod
    async def get_average_rating(user_id: str) -> tuple[float, int]:
        """Get average rating and total count for a user."""
        reviews = await Review.find(Review.reviewee_id == user_id).to_list()
        if not reviews:
            return 5.0, 0
        total = sum(r.rating for r in reviews)
        count = len(reviews)
        return round(total / count, 2), count
    
    @staticmethod
    async def delete(review_id: str) -> bool:
        """Delete a review."""
        review = await Review.get(PydanticObjectId(review_id))
        if review:
            await review.delete()
            return True
        return False

