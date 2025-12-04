-- Migration: Shared Ride System
-- This migration adds driver trips, booking types, and related features

-- Step 1: Create new enum types (if they don't exist)
do $$ 
begin
    if not exists (select 1 from pg_type where typname = 'booking_type') then
        create type booking_type as enum ('seat', 'whole_car', 'custom_request');
    end if;
    
    if not exists (select 1 from pg_type where typname = 'trip_status') then
        create type trip_status as enum ('scheduled', 'in_progress', 'completed', 'cancelled');
    end if;
end $$;

-- Step 2: Update profiles table - make phone_number NOT NULL
-- First, set a default for any NULL values (if any exist)
update public.profiles 
set phone_number = '0000000000' 
where phone_number is null;

-- Then alter the column to be NOT NULL
alter table public.profiles 
alter column phone_number set not null;

-- Step 3: Add new columns to bookings table (if they don't exist)
do $$
begin
    -- Add customer_id column
    if not exists (
        select 1 from information_schema.columns 
        where table_schema = 'public' 
        and table_name = 'bookings' 
        and column_name = 'customer_id'
    ) then
        alter table public.bookings 
        add column customer_id uuid references public.profiles(id);
    end if;

    -- Add booking_type column
    if not exists (
        select 1 from information_schema.columns 
        where table_schema = 'public' 
        and table_name = 'bookings' 
        and column_name = 'booking_type'
    ) then
        alter table public.bookings 
        add column booking_type booking_type default 'custom_request';
    end if;

    -- Add driver_trip_id column (will add foreign key after driver_trips table is created)
    if not exists (
        select 1 from information_schema.columns 
        where table_schema = 'public' 
        and table_name = 'bookings' 
        and column_name = 'driver_trip_id'
    ) then
        alter table public.bookings 
        add column driver_trip_id uuid;
    end if;

    -- Add seats_booked column
    if not exists (
        select 1 from information_schema.columns 
        where table_schema = 'public' 
        and table_name = 'bookings' 
        and column_name = 'seats_booked'
    ) then
        alter table public.bookings 
        add column seats_booked integer default 1;
    end if;
end $$;

-- Step 4: Create driver_trips table (if it doesn't exist)
create table if not exists public.driver_trips (
    id uuid default uuid_generate_v4() primary key,
    driver_id uuid references public.profiles(id) on delete cascade not null,
    origin text not null,
    destination text not null,
    departure_time timestamp with time zone not null,
    available_seats integer not null check (available_seats > 0),
    booked_seats integer default 0 check (booked_seats >= 0),
    price_per_seat decimal(10,2) not null,
    whole_car_price decimal(10,2) not null,
    status trip_status default 'scheduled',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    constraint seats_check check (booked_seats <= available_seats)
);

-- Step 5: Enable RLS on driver_trips (if not already enabled)
alter table public.driver_trips enable row level security;

-- Step 6: Drop existing policies if they exist and recreate them
-- This ensures we have the latest policies

-- Drop old admin policy if it exists (the old one was for all operations)
drop policy if exists "Admins can do everything on bookings" on public.bookings;

-- Create new admin policies
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Admins can view all bookings'
    ) then
        create policy "Admins can view all bookings"
            on public.bookings for select
            using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Admins can insert bookings'
    ) then
        create policy "Admins can insert bookings"
            on public.bookings for insert
            with check ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Admins can update bookings'
    ) then
        create policy "Admins can update bookings"
            on public.bookings for update
            using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Admins can delete bookings'
    ) then
        create policy "Admins can delete bookings"
            on public.bookings for delete
            using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;
end $$;

-- Add driver update policy if it doesn't exist
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Drivers can update assigned bookings'
    ) then
        create policy "Drivers can update assigned bookings"
            on public.bookings for update
            using ( assigned_driver_id = auth.uid() );
    end if;
end $$;

-- Add customer policies if they don't exist
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Customers can view own bookings'
    ) then
        create policy "Customers can view own bookings"
            on public.bookings for select
            using ( customer_id = auth.uid() );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'bookings' 
        and policyname = 'Customers can insert own bookings'
    ) then
        create policy "Customers can insert own bookings"
            on public.bookings for insert
            with check ( customer_id = auth.uid() );
    end if;
end $$;

-- Step 7: Create driver_trips policies
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Everyone can view scheduled trips'
    ) then
        create policy "Everyone can view scheduled trips"
            on public.driver_trips for select
            using ( status = 'scheduled' );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Drivers can view own trips'
    ) then
        create policy "Drivers can view own trips"
            on public.driver_trips for select
            using ( driver_id = auth.uid() );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Admins can view all trips'
    ) then
        create policy "Admins can view all trips"
            on public.driver_trips for select
            using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Drivers can insert own trips'
    ) then
        create policy "Drivers can insert own trips"
            on public.driver_trips for insert
            with check ( driver_id = auth.uid() );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Drivers can update own trips'
    ) then
        create policy "Drivers can update own trips"
            on public.driver_trips for update
            using ( driver_id = auth.uid() );
    end if;

    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'driver_trips' 
        and policyname = 'Admins can update any trip'
    ) then
        create policy "Admins can update any trip"
            on public.driver_trips for update
            using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );
    end if;
end $$;

-- Step 8: Add foreign key constraint for driver_trip_id (if constraint doesn't exist)
do $$
begin
    if not exists (
        select 1 from information_schema.table_constraints 
        where constraint_schema = 'public' 
        and table_name = 'bookings' 
        and constraint_name = 'bookings_driver_trip_id_fkey'
    ) then
        alter table public.bookings 
        add constraint bookings_driver_trip_id_fkey 
        foreign key (driver_trip_id) references public.driver_trips(id) on delete set null;
    end if;
end $$;

-- Step 9: Create indexes (if they don't exist)
create index if not exists idx_driver_trips_driver_id on public.driver_trips(driver_id);
create index if not exists idx_driver_trips_departure_time on public.driver_trips(departure_time);
create index if not exists idx_driver_trips_status on public.driver_trips(status);
create index if not exists idx_bookings_driver_trip_id on public.bookings(driver_trip_id);
create index if not exists idx_bookings_customer_id on public.bookings(customer_id);
create index if not exists idx_bookings_booking_type on public.bookings(booking_type);

-- Step 10: Create or replace function to update updated_at timestamp
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$ language plpgsql;

-- Step 11: Create trigger for updated_at (drop and recreate to ensure it's correct)
drop trigger if exists update_driver_trips_updated_at on public.driver_trips;
create trigger update_driver_trips_updated_at
    before update on public.driver_trips
    for each row
    execute procedure public.update_updated_at_column();

-- Step 12: Update handle_new_user function to include phone_number
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, full_name, phone_number, role)
    values (
        new.id, 
        new.raw_user_meta_data->>'full_name', 
        coalesce(new.raw_user_meta_data->>'phone_number', '0000000000'),
        coalesce((new.raw_user_meta_data->>'role')::user_role, 'customer'::user_role)
    );
    return new;
end;
$$ language plpgsql security definer;

