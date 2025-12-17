"""Application factory for Guzo Rideshare Platform."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from src.guzo.config import settings
from src.guzo.infrastructure import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    import os
    
    app = FastAPI(
        title=settings.app_name,
        description="A ridesharing and charter platform for Ethiopia",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Ensure upload directories exist
    os.makedirs("static/uploads/photos", exist_ok=True)
    os.makedirs("static/uploads/licenses", exist_ok=True)
    os.makedirs("static/uploads/registrations", exist_ok=True)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Include routers from domain modules
    from src.guzo.auth import router as auth_router
    from src.guzo.trips import router as trips_router
    from src.guzo.bookings import router as bookings_router
    from src.guzo.vehicles import router as vehicles_router
    from src.guzo.payments import router as payments_router
    from src.guzo.admin import router as admin_router
    from src.guzo.pages import router as pages_router
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
    app.include_router(payments_router)
    app.include_router(admin_router)
    app.include_router(pages_router)
    # Phase 2 routers
    app.include_router(reviews_router)
    app.include_router(favorites_router)
    app.include_router(pricing_router)
    app.include_router(verification_router)
    app.include_router(analytics_router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "app": settings.app_name}
    
    # PWA manifest route
    @app.get("/manifest.json")
    async def get_manifest():
        """Serve PWA manifest."""
        return {
            "name": "Guzo Rideshare",
            "short_name": "Guzo",
            "description": "Book rides across Ethiopia",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1a1a2e",
            "theme_color": "#16a34a",
            "icons": [
                {
                    "src": "/static/assets/logo.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/assets/logo.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
    
    # Service worker route
    @app.get("/sw.js")
    async def get_service_worker():
        """Serve service worker."""
        sw_content = """
const CACHE_NAME = 'guzo-v1';
const OFFLINE_URL = '/offline';

const PRECACHE_URLS = [
    '/',
    '/offline',
    '/static/assets/logo.png',
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        })
    );
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event
self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match(OFFLINE_URL);
            })
        );
    } else {
        event.respondWith(
            caches.match(event.request).then((response) => {
                return response || fetch(event.request);
            })
        );
    }
});
"""
        return Response(content=sw_content, media_type="application/javascript")
    
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

