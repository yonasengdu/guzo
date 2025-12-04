# Database Migration Instructions

## Migration File
The migration file is located at: `supabase/migrations/20240101000000_shared_ride_system.sql`

## How to Run the Migration

### Option 1: Using Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to https://app.supabase.com
   - Select your project

2. **Navigate to SQL Editor**
   - Click on "SQL Editor" in the left sidebar

3. **Run the Migration**
   - Click "New Query"
   - Open the file `supabase/migrations/20240101000000_shared_ride_system.sql`
   - Copy the entire contents
   - Paste into the SQL Editor
   - Click "Run" or press `Ctrl+Enter` (Windows/Linux) or `Cmd+Enter` (Mac)

4. **Verify Migration**
   - Check that the migration completed without errors
   - You should see new tables: `driver_trips`
   - Check that `bookings` table has new columns: `customer_id`, `booking_type`, `driver_trip_id`, `seats_booked`
   - Verify that `profiles.phone_number` is now NOT NULL

### Option 2: Using Supabase CLI (If Installed)

If you have Supabase CLI installed:

```bash
# Link to your project (if not already linked)
supabase link --project-ref your-project-ref

# Run the migration
supabase db push
```

Or manually:

```bash
# Apply the migration
psql your-connection-string < supabase/migrations/20240101000000_shared_ride_system.sql
```

### Option 3: Using psql Directly

If you have direct database access:

```bash
psql -h your-db-host -U postgres -d postgres -f supabase/migrations/20240101000000_shared_ride_system.sql
```

## What the Migration Does

1. **Creates new enum types:**
   - `booking_type` (seat, whole_car, custom_request)
   - `trip_status` (scheduled, in_progress, completed, cancelled)

2. **Updates existing tables:**
   - Makes `profiles.phone_number` NOT NULL
   - Adds new columns to `bookings` table:
     - `customer_id` - Links booking to customer profile
     - `booking_type` - Type of booking (seat/whole_car/custom_request)
     - `driver_trip_id` - Links to driver trips
     - `seats_booked` - Number of seats booked

3. **Creates new table:**
   - `driver_trips` - Stores driver-created trips with origin, destination, seats, pricing

4. **Updates policies:**
   - Adds RLS policies for customers to view/insert their own bookings
   - Adds RLS policies for driver_trips table
   - Updates admin policies to be more granular

5. **Creates indexes:**
   - Performance indexes on frequently queried columns

6. **Updates functions:**
   - Updates `handle_new_user()` to include phone_number
   - Creates `update_updated_at_column()` for auto-updating timestamps

## Troubleshooting

### Error: "column already exists"
- This means the column was already added. The migration is idempotent and should handle this, but if you see this error, you can safely ignore it or comment out that specific line.

### Error: "type already exists"
- The enum types already exist. This is safe to ignore.

### Error: "policy already exists"
- The RLS policy already exists. The migration checks for existence before creating, so this shouldn't happen, but if it does, you can drop the policy first or ignore the error.

### Error: "constraint already exists"
- The foreign key constraint already exists. Safe to ignore.

## Verification Queries

After running the migration, verify it worked:

```sql
-- Check driver_trips table exists
SELECT * FROM driver_trips LIMIT 1;

-- Check bookings has new columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'bookings' 
AND column_name IN ('customer_id', 'booking_type', 'driver_trip_id', 'seats_booked');

-- Check phone_number is NOT NULL
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name = 'phone_number';

-- Check policies exist
SELECT policyname FROM pg_policies 
WHERE tablename IN ('bookings', 'driver_trips')
ORDER BY tablename, policyname;
```

## Rollback

If you need to rollback this migration, you would need to:

1. Drop the `driver_trips` table
2. Remove new columns from `bookings` table
3. Revert `phone_number` to nullable (if needed)
4. Drop new enum types
5. Remove new policies

However, **be careful** - this will delete all driver trips data. Consider backing up your database first.

