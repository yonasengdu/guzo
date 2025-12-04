-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Create Profiles table (extends auth.users)
create type user_role as enum ('admin', 'driver', 'customer');

create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  full_name text,
  phone_number text not null, -- Mandatory phone number
  role user_role default 'customer',
  is_active boolean default false, -- For drivers to toggle availability
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table public.profiles enable row level security;

-- Create policies for Profiles
create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- Create Bookings table
create type booking_status as enum ('pending', 'assigned', 'completed', 'cancelled');
create type booking_type as enum ('seat', 'whole_car', 'custom_request');

create table public.bookings (
  id uuid default uuid_generate_v4() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  customer_name text not null,
  customer_phone text not null,
  customer_id uuid references public.profiles(id), -- Link to customer profile
  pickup_location text not null,
  dropoff_location text not null,
  scheduled_time timestamp with time zone not null,
  status booking_status default 'pending',
  booking_type booking_type default 'custom_request', -- Type of booking
  assigned_driver_id uuid references public.profiles(id),
  driver_trip_id uuid, -- Will reference driver_trips table (added after table creation)
  seats_booked integer default 1, -- Number of seats booked
  price decimal(10,2),
  notes text
);

-- Enable RLS
alter table public.bookings enable row level security;

-- Create policies for Bookings
-- Admins can do everything
create policy "Admins can view all bookings"
  on bookings for select
  using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

create policy "Admins can insert bookings"
  on bookings for insert
  with check ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

create policy "Admins can update bookings"
  on bookings for update
  using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

create policy "Admins can delete bookings"
  on bookings for delete
  using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

-- Drivers can view assigned bookings or available pending bookings (optional logic)
create policy "Drivers can view assigned bookings"
  on bookings for select
  using ( assigned_driver_id = auth.uid() );

-- Drivers can update assigned bookings (e.g., mark as completed)
create policy "Drivers can update assigned bookings"
  on bookings for update
  using ( assigned_driver_id = auth.uid() );

-- Customers can view their own bookings
create policy "Customers can view own bookings"
  on bookings for select
  using ( customer_id = auth.uid() );

-- Customers can insert their own bookings
create policy "Customers can insert own bookings"
  on bookings for insert
  with check ( customer_id = auth.uid() );

-- Function to handle new user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, full_name, phone_number, role)
    values (
        new.id, 
        coalesce(new.raw_user_meta_data->>'full_name', 'User'),
        coalesce(new.raw_user_meta_data->>'phone_number', '0000000000'),
        coalesce(
            case 
                when (new.raw_user_meta_data->>'role')::text in ('admin', 'driver', 'customer') 
                then (new.raw_user_meta_data->>'role')::user_role
                else 'customer'::user_role
            end,
            'customer'::user_role
        )
    );
    return new;
exception when others then
    -- Log the error but don't fail the user creation
    raise warning 'Error creating profile for user %: %', new.id, sqlerrm;
    -- Try to insert with minimal data as fallback
    begin
        insert into public.profiles (id, full_name, phone_number, role)
        values (
            new.id,
            coalesce(new.raw_user_meta_data->>'full_name', 'User'),
            coalesce(new.raw_user_meta_data->>'phone_number', '0000000000'),
            'customer'::user_role
        );
    exception when others then
        raise warning 'Failed to create profile even with fallback: %', sqlerrm;
    end;
    return new;
end;
$$ language plpgsql security definer;

-- Trigger for new user signup
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Create Driver Trips table
create type trip_status as enum ('scheduled', 'in_progress', 'completed', 'cancelled');

create table public.driver_trips (
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

-- Enable RLS for driver_trips
alter table public.driver_trips enable row level security;

-- RLS Policies for driver_trips
-- Everyone can view scheduled trips (for customers to browse)
create policy "Everyone can view scheduled trips"
  on driver_trips for select
  using ( status = 'scheduled' );

-- Drivers can view their own trips
create policy "Drivers can view own trips"
  on driver_trips for select
  using ( driver_id = auth.uid() );

-- Admins can view all trips
create policy "Admins can view all trips"
  on driver_trips for select
  using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

-- Drivers can insert their own trips
create policy "Drivers can insert own trips"
  on driver_trips for insert
  with check ( driver_id = auth.uid() );

-- Drivers can update their own trips
create policy "Drivers can update own trips"
  on driver_trips for update
  using ( driver_id = auth.uid() );

-- Admins can update any trip (for price adjustments)
create policy "Admins can update any trip"
  on driver_trips for update
  using ( exists (select 1 from profiles where id = auth.uid() and role = 'admin') );

-- Add foreign key constraint for driver_trip_id in bookings
alter table public.bookings 
  add constraint bookings_driver_trip_id_fkey 
  foreign key (driver_trip_id) references public.driver_trips(id) on delete set null;

-- Create indexes for performance
create index idx_driver_trips_driver_id on public.driver_trips(driver_id);
create index idx_driver_trips_departure_time on public.driver_trips(departure_time);
create index idx_driver_trips_status on public.driver_trips(status);
create index idx_bookings_driver_trip_id on public.bookings(driver_trip_id);
create index idx_bookings_customer_id on public.bookings(customer_id);
create index idx_bookings_booking_type on public.bookings(booking_type);

-- Function to update updated_at timestamp
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

-- Trigger to auto-update updated_at
create trigger update_driver_trips_updated_at
  before update on public.driver_trips
  for each row
  execute procedure public.update_updated_at_column();
