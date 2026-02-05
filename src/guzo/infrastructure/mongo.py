import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from src.guzo.config import settings


logger = logging.getLogger(__name__)

# MongoDB client instance
client: Optional[AsyncIOMotorClient] = None


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


async def init_db(max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Initialize database connection and Beanie ODM with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds
        
    Raises:
        DatabaseConnectionError: If connection fails after all retries
    """
    import asyncio
    global client
    
    # Import models here to avoid circular imports
    from src.guzo.auth.core import User
    from src.guzo.vehicles.core import Vehicle
    from src.guzo.trips.core import DriverTrip
    from src.guzo.bookings.core import Booking
    from src.guzo.wallet.core import (
        DriverWallet,
        TokenTransaction,
        TokenPackage,
        PlatformFeeConfig,
    )
    # Phase 2 models
    from src.guzo.reviews.core import Review
    from src.guzo.favorites.core import FavoriteRoute, FavoriteDriver
    from src.guzo.pricing.core import PricingRule, SurgeMultiplier
    from src.guzo.verification.core import DriverVerification, VerificationDocument
    
    last_error: Optional[Exception] = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting database connection (attempt {attempt}/{max_retries})...")
            
            # Create MongoDB client with connection timeout
            client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
            )
            
            # Verify connection by pinging the server
            await client.admin.command('ping')
            
            # Initialize Beanie with document models
            await init_beanie(
                database=client[settings.mongo_db],
                document_models=[
                    User,
                    Vehicle,
                    DriverTrip,
                    Booking,
                    # Wallet models
                    DriverWallet,
                    TokenTransaction,
                    TokenPackage,
                    PlatformFeeConfig,
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
            
            logger.info("Database connection established successfully")
            return
            
        except Exception as e:
            last_error = e
            logger.warning(f"Database connection attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
            else:
                # Close any partial connection
                if client:
                    client.close()
                    client = None
    
    raise DatabaseConnectionError(
        f"Failed to connect to database after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


async def close_db() -> None:
    """Close database connection properly."""
    global client
    if client:
        logger.info("Closing database connection...")
        client.close()
        client = None
        logger.info("Database connection closed")


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance.
    
    Returns:
        The database instance, or None if not connected.
    """
    if client is None:
        logger.warning("Database client not initialized")
        return None
    return client[settings.mongo_db]


async def check_db_health() -> dict:
    """Check database health and connectivity.
    
    Returns:
        Dictionary with health status information.
    """
    if client is None:
        return {
            "status": "disconnected",
            "message": "Database client not initialized"
        }
    
    try:
        # Ping the database
        await client.admin.command('ping')
        
        # Get server info
        server_info = await client.server_info()
        
        return {
            "status": "connected",
            "version": server_info.get("version", "unknown"),
            "database": settings.mongo_db
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

