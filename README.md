# Guzo Rideshare Platform

A Progressive Web App for ridesharing and charter services in Ethiopia, built with FastAPI + HTMX + MongoDB.

## Features

- **For Riders**: Search trips, book seats, request charters
- **For Drivers**: Create trips, manage bookings, toggle availability
- **For Admins**: Manage users, trips, and match booking requests
- **PWA**: Installable, works offline, push notifications

## Tech Stack

- **Backend**: FastAPI, Beanie ODM, MongoDB
- **Frontend**: HTMX, Jinja2 Templates, Tailwind CSS + DaisyUI
- **Infrastructure**: Docker, Redis

## Quick Start with Docker (Recommended)

### Prerequisites

- Docker & Docker Compose

### Run the Application

1. **Start all services** (MongoDB, Redis, App):
   ```bash
   docker-compose up --build
   ```

2. **Open the app**: http://localhost:8000

3. **Seed the database** (optional, creates test users):
   ```bash
   docker-compose exec app python scripts/seed_db.py
   ```

### Test Accounts (after seeding)

| Role   | Email              | Password   |
|--------|-------------------|------------|
| Admin  | admin@guzo.et     | admin123   |
| Driver | driver1@guzo.et   | driver123  |
| Rider  | rider1@guzo.et    | rider123   |

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- MongoDB running locally
- Poetry (Python package manager)

### Setup

1. **Install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install poetry
   poetry install
   ```

2. **Start MongoDB** (if not using Docker):
   ```bash
   docker run -d -p 27017:27017 --name guzo_mongodb mongo:7.0
   ```

3. **Run the development server**:
   ```bash
   make dev
   # or
   poetry run uvicorn src.guzo.app:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Seed the database**:
   ```bash
   make seed
   # or
   poetry run python scripts/seed_db.py
   ```

5. **Open the app**: http://localhost:8000

## Project Structure (Domain-Driven)

```
guzo/
├── src/
│   └── guzo/                  # Main application package
│       ├── app.py             # FastAPI app factory
│       ├── config.py          # Settings from environment
│       ├── core.py            # Shared utilities
│       ├── middleware.py      # Auth dependencies
│       │
│       ├── infrastructure/    # Database and base classes
│       │   ├── mongo.py       # MongoDB/Beanie connection
│       │   └── repository.py  # Base repository class
│       │
│       ├── auth/              # Authentication domain
│       │   ├── core.py        # User model + schemas
│       │   ├── repository.py  # User database operations
│       │   ├── service.py     # Auth business logic
│       │   └── resource.py    # Auth API routes
│       │
│       ├── trips/             # Trips domain
│       │   ├── core.py        # Trip model + schemas
│       │   ├── repository.py  # Trip database operations
│       │   ├── service.py     # Trip business logic
│       │   └── resource.py    # Driver API routes
│       │
│       ├── bookings/          # Bookings domain
│       │   ├── core.py        # Booking model + schemas
│       │   ├── repository.py  # Booking database operations
│       │   ├── service.py     # Booking business logic
│       │   └── resource.py    # Customer API routes
│       │
│       ├── vehicles/          # Vehicles domain
│       │   ├── core.py        # Vehicle model + schemas
│       │   ├── repository.py  # Vehicle database operations
│       │   ├── service.py     # Vehicle business logic
│       │   └── resource.py    # Vehicle API routes
│       │
│       ├── payments/          # Payments domain
│       │   ├── core.py        # Payment model + schemas
│       │   ├── repository.py  # Payment database operations
│       │   ├── service.py     # Payment business logic
│       │   └── resource.py    # Payment API routes
│       │
│       ├── admin/             # Admin functionality
│       │   └── resource.py    # Admin API routes
│       │
│       ├── pages/             # Public pages
│       │   └── resource.py    # Landing, login, signup pages
│       │
│       └── templates/         # Jinja2 HTML templates
│           ├── base.html
│           ├── landing.html
│           ├── auth/
│           ├── customer/
│           ├── driver/
│           ├── admin/
│           └── partials/
│
├── static/                    # Static assets (images, PWA)
├── scripts/                   # Database seeding, utilities
├── docker-compose.yml         # Full stack deployment
├── Dockerfile
└── pyproject.toml             # Python dependencies
```

## Domain Module Pattern

Each domain module follows this structure:

- **`core.py`**: Document models (Beanie) + Pydantic schemas (enums, DTOs)
- **`repository.py`**: Database operations (CRUD, queries)
- **`service.py`**: Business logic (validation, orchestration)
- **`resource.py`**: API routes (FastAPI router)

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Landing page |
| `/login` | User login |
| `/signup` | User registration |
| `/customer` | Rider dashboard |
| `/customer/search` | Search available trips |
| `/driver` | Driver dashboard |
| `/admin` | Admin dashboard |
| `/auth/*` | Authentication API |
| `/vehicles` | Vehicle management API |
| `/payments` | Payment API |

## Environment Variables

┌─────────────────────────────────────────────────┐
│  resource.py (API/HTTP Layer)                   │
│  - Routes, request handling, response formatting│
└─────────────────┬───────────────────────────────┘
                  │ calls
┌─────────────────▼───────────────────────────────┐
│  service.py (Business Logic Layer)              │
│  - Business rules, orchestration, validation    │
└─────────────────┬───────────────────────────────┘
                  │ calls
┌─────────────────▼───────────────────────────────┐
│  repository.py (Data Access Layer)              │
│  - CRUD operations, queries                     │
└─────────────────┬───────────────────────────────┘
                  │ uses
┌─────────────────▼───────────────────────────────┐
│  core.py (Domain Layer)                         │
│  - Models, schemas, enums                       │
└─────────────────────────────────────────────────┘
Create a `.env` file:

```bash
MONGODB_URL=mongodb://guzo:guzopass123@localhost:27017/guzo_db?authSource=admin
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=true
```

## License

MIT
