from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.guzo.config import settings


# MongoDB client instance
client: AsyncIOMotorClient = None


async def init_db():
    """Initialize database connection and Beanie ODM."""
    global client
    
    # Import models here to avoid circular imports
    from src.guzo.auth.core import User
    from src.guzo.vehicles.core import Vehicle
    from src.guzo.trips.core import DriverTrip
    from src.guzo.bookings.core import Booking
    from src.guzo.payments.core import Payment
    # Phase 2 models
    from src.guzo.reviews.core import Review
    from src.guzo.favorites.core import FavoriteRoute, FavoriteDriver
    from src.guzo.pricing.core import PricingRule, SurgeMultiplier
    from src.guzo.verification.core import DriverVerification, VerificationDocument
    
    # Create MongoDB client
    client = AsyncIOMotorClient(settings.mongodb_url)
    
    # Initialize Beanie with document models
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=[
            User,
            Vehicle,
            DriverTrip,
            Booking,
            Payment,
            # Phase 2 models
            Review,
            FavoriteRoute,
            FavoriteDriver,
            PricingRule,
            SurgeMultiplier,
            DriverVerification,
            VerificationDocument,
        ]
    )


async def close_db():
    """Close database connection."""
    global client
    if client:
        client.close()


def get_database():
    """Get database instance."""
    return client[settings.mongo_db]

