"""Application factory for Guzo Rideshare Platform."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.guzo.config import settings
from src.guzo.infrastructure import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    try:
        logger.info("Starting application...")
        await init_db()
        logger.info("Database initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        logger.info("Shutting down application...")
        await close_db()
        logger.info("Database connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="A ridesharing and charter platform for Ethiopia",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug,
    )
    
    # CORS middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )
    
    # Include routers from domain modules
    from src.guzo.auth import router as auth_router
    from src.guzo.trips import router as trips_router
    from src.guzo.bookings import router as bookings_router
    from src.guzo.vehicles import router as vehicles_router
    from src.guzo.wallet import router as wallet_router
    from src.guzo.admin import router as admin_router
    from src.guzo.reviews.resource import router as reviews_router
    from src.guzo.favorites.resource import router as favorites_router
    from src.guzo.pricing.resource import router as pricing_router
    from src.guzo.verification.resource import router as verification_router
    from src.guzo.analytics.resource import router as analytics_router
    
    # Register routers
    app.include_router(auth_router)
    app.include_router(trips_router)  # /driver routes
    app.include_router(bookings_router)  # /customer routes
    app.include_router(vehicles_router)
    app.include_router(wallet_router)
    app.include_router(admin_router)
    # Phase 2 routers
    app.include_router(reviews_router)
    app.include_router(favorites_router)
    app.include_router(pricing_router)
    app.include_router(verification_router)
    app.include_router(analytics_router)
    
    # Health check endpoint with database connectivity check
    @app.get("/health")
    async def health_check():
        """Health check endpoint with database status."""
        from src.guzo.infrastructure.mongo import get_database
        
        db_status = "unknown"
        try:
            db = get_database()
            if db is not None:
                # Ping the database to check connectivity
                await db.command("ping")
                db_status = "connected"
            else:
                db_status = "not_initialized"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "app": settings.app_name,
            "database": db_status,
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.guzo.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
