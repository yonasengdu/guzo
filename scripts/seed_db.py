#!/usr/bin/env python3
"""Seed the database with sample data."""

import asyncio
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '.')

from src.guzo.infrastructure import init_db, close_db
from src.guzo.auth.core import User, UserRole, UserCreate
from src.guzo.trips.core import DriverTrip, TripStatus
from src.guzo.auth.service import AuthService


async def seed():
    """Seed the database with sample data."""
    print("Initializing database...")
    await init_db()
    
    # Create admin user
    print("Creating admin user...")
    try:
        admin = await AuthService.create_user(
            UserCreate(
                email='admin@guzo.et',
                phone='+251911000001',
                full_name='Admin User',
                password='admin123',
                role=UserRole.ADMIN,
                language='en',
            )
        )
        print(f"  Created admin: {admin.email}")
    except ValueError as e:
        print(f"  Admin already exists: {e}")
    
    # Create sample drivers
    print("Creating sample drivers...")
    drivers = [
        ('driver1@guzo.et', '+251911000002', 'Abebe Kebede'),
        ('driver2@guzo.et', '+251911000003', 'Tadesse Haile'),
        ('driver3@guzo.et', '+251911000004', 'Yohannes Desta'),
    ]
    
    driver_ids = []
    for email, phone, name in drivers:
        try:
            driver = await AuthService.create_user(
                UserCreate(
                    email=email,
                    phone=phone,
                    full_name=name,
                    password='driver123',
                    role=UserRole.DRIVER,
                    language='am',
                )
            )
            driver.is_online = True
            await driver.save()
            driver_ids.append(str(driver.id))
            print(f"  Created driver: {name}")
        except ValueError as e:
            print(f"  Driver {name} already exists: {e}")
            existing = await User.find_one(User.email == email)
            if existing:
                driver_ids.append(str(existing.id))
    
    # Create sample riders
    print("Creating sample riders...")
    riders = [
        ('rider1@guzo.et', '+251922000001', 'Tigist Haile'),
        ('rider2@guzo.et', '+251922000002', 'Meron Alemu'),
    ]
    
    for email, phone, name in riders:
        try:
            rider = await AuthService.create_user(
                UserCreate(
                    email=email,
                    phone=phone,
                    full_name=name,
                    password='rider123',
                    role=UserRole.RIDER,
                    language='en',
                )
            )
            print(f"  Created rider: {name}")
        except ValueError as e:
            print(f"  Rider {name} already exists: {e}")
    
    # Create sample trips
    print("Creating sample trips...")
    routes = [
        ('Addis Ababa', 'Bahir Dar', 800, 3000, 4),
        ('Addis Ababa', 'Hawassa', 400, 1500, 4),
        ('Addis Ababa', 'Adama', 150, 600, 4),
        ('Bahir Dar', 'Gondar', 300, 1200, 4),
        ('Addis Ababa', 'Mekelle', 1200, 4500, 4),
        ('Addis Ababa', 'Dire Dawa', 600, 2400, 4),
    ]
    
    for i, (origin, dest, price_seat, price_car, seats) in enumerate(routes):
        # Check if trip already exists
        existing = await DriverTrip.find_one({
            "origin": origin,
            "destination": dest,
            "status": TripStatus.SCHEDULED
        })
        if existing:
            print(f"  Trip {origin} → {dest} already exists")
            continue
            
        driver_id = driver_ids[i % len(driver_ids)] if driver_ids else None
        if not driver_id:
            continue
            
        trip = DriverTrip(
            driver_id=driver_id,
            origin=origin,
            destination=dest,
            departure_time=datetime.utcnow() + timedelta(days=i+1, hours=8),
            available_seats=seats,
            price_per_seat=float(price_seat),
            whole_car_price=float(price_car),
            status=TripStatus.SCHEDULED,
        )
        await trip.insert()
        print(f"  Created trip: {origin} → {dest}")
    
    print("\nSeeding complete!")
    print("\nTest accounts:")
    print("  Admin:  admin@guzo.et / admin123")
    print("  Driver: driver1@guzo.et / driver123")
    print("  Rider:  rider1@guzo.et / rider123")
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
