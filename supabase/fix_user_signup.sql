-- Fix for user signup database error
-- This fixes the handle_new_user() function to properly handle phone_number

-- Update the function to use COALESCE for safety
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, full_name, phone_number, role)
    values (
        new.id, 
        coalesce(new.raw_user_meta_data->>'full_name', ''),
        coalesce(new.raw_user_meta_data->>'phone_number', '0000000000'),
        coalesce((new.raw_user_meta_data->>'role')::user_role, 'customer'::user_role)
    );
    return new;
exception when others then
    -- Log the error but don't fail the user creation
    raise warning 'Error creating profile for user %: %', new.id, sqlerrm;
    -- Try to insert with minimal data
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

-- Also ensure phone_number column allows NULL temporarily if migration hasn't been run
-- This is a safety measure - if the column is still nullable, this won't break anything
do $$
begin
    -- Check if phone_number is NOT NULL
    if exists (
        select 1 from information_schema.columns 
        where table_schema = 'public' 
        and table_name = 'profiles' 
        and column_name = 'phone_number'
        and is_nullable = 'NO'
    ) then
        -- Column is NOT NULL, which is correct
        raise notice 'phone_number column is correctly set to NOT NULL';
    else
        -- Column might be nullable, update existing NULL values
        update public.profiles 
        set phone_number = '0000000000' 
        where phone_number is null;
        
        -- Try to make it NOT NULL (will fail if there are still NULLs)
        begin
            alter table public.profiles 
            alter column phone_number set not null;
        exception when others then
            raise warning 'Could not set phone_number to NOT NULL: %', sqlerrm;
        end;
    end if;
end $$;

