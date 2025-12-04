#!/usr/bin/env node

/**
 * Migration Runner for Supabase
 * 
 * This script runs the migration SQL file against your Supabase database.
 * 
 * Usage:
 * 1. Set your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as environment variables
 * 2. Run: node supabase/run-migration.js
 * 
 * Or run directly in Supabase Dashboard:
 * 1. Go to your Supabase project dashboard
 * 2. Navigate to SQL Editor
 * 3. Copy and paste the contents of supabase/migrations/20240101000000_shared_ride_system.sql
 * 4. Click "Run"
 */

import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
    console.error('Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set');
    console.error('\nTo run this migration:');
    console.error('1. Get your Supabase URL and Service Role Key from your Supabase project settings');
    console.error('2. Run: SUPABASE_URL=your_url SUPABASE_SERVICE_ROLE_KEY=your_key node supabase/run-migration.js');
    console.error('\nOr run the SQL file directly in Supabase Dashboard SQL Editor');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
    auth: {
        autoRefreshToken: false,
        persistSession: false
    }
});

async function runMigration() {
    try {
        const migrationFile = join(__dirname, 'migrations', '20240101000000_shared_ride_system.sql');
        const sql = readFileSync(migrationFile, 'utf8');

        console.log('Running migration...');
        console.log('Migration file: 20240101000000_shared_ride_system.sql\n');

        // Split SQL by semicolons and execute each statement
        // Note: This is a simplified approach. For production, consider using a proper SQL parser
        const statements = sql
            .split(';')
            .map(s => s.trim())
            .filter(s => s.length > 0 && !s.startsWith('--'));

        for (const statement of statements) {
            if (statement.trim()) {
                try {
                    const { error } = await supabase.rpc('exec_sql', { sql: statement });
                    if (error) {
                        // If exec_sql doesn't exist, we'll need to use a different approach
                        console.warn('Note: exec_sql function not available. Please run migration manually in Supabase Dashboard.');
                        console.warn('The migration file is located at: supabase/migrations/20240101000000_shared_ride_system.sql');
                        break;
                    }
                } catch (err) {
                    console.warn('Note: Cannot execute SQL programmatically. Please run migration manually.');
                    console.warn('The migration file is located at: supabase/migrations/20240101000000_shared_ride_system.sql');
                    break;
                }
            }
        }

        console.log('\n✅ Migration instructions:');
        console.log('Since Supabase doesn\'t support direct SQL execution via JS client,');
        console.log('please run the migration manually:');
        console.log('\n1. Go to your Supabase project dashboard');
        console.log('2. Navigate to SQL Editor');
        console.log('3. Copy and paste the contents of:');
        console.log('   supabase/migrations/20240101000000_shared_ride_system.sql');
        console.log('4. Click "Run" button');
        console.log('\nMigration file location:');
        console.log(migrationFile);

    } catch (error) {
        console.error('Error reading migration file:', error.message);
        process.exit(1);
    }
}

runMigration();

