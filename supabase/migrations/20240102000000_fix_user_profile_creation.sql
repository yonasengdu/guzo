-- Migration: Fix user profile creation with role handling
-- This migration updates the handle_new_user() trigger function to properly handle
-- role assignment with error handling and fallback mechanisms

-- Drop and recreate the trigger function with improved error handling
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

-- Ensure the trigger exists (it should already exist, but this ensures it's there)
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- Fix any existing users without profiles (backfill)
-- This handles cases where the trigger may have failed previously
do $$
declare
    missing_user record;
begin
    for missing_user in 
        select u.id, 
               coalesce(u.raw_user_meta_data->>'full_name', 'User') as full_name,
               coalesce(u.raw_user_meta_data->>'phone_number', '0000000000') as phone_number,
               coalesce(
                   case 
                       when (u.raw_user_meta_data->>'role')::text in ('admin', 'driver', 'customer') 
                       then (u.raw_user_meta_data->>'role')::user_role
                       else 'customer'::user_role
                   end,
                   'customer'::user_role
               ) as role
        from auth.users u
        left join public.profiles p on u.id = p.id
        where p.id is null
    loop
        begin
            insert into public.profiles (id, full_name, phone_number, role)
            values (missing_user.id, missing_user.full_name, missing_user.phone_number, missing_user.role);
        exception when others then
            raise warning 'Failed to backfill profile for user %: %', missing_user.id, sqlerrm;
        end;
    end loop;
end $$;

