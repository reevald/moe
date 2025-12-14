#!/usr/bin/env python3
"""
Migration Management Helper Script

This script provides a simple interface for managing database migrations
and seeding operations for the MOE project using Supabase.

Usage:
    python migration/migrate.py migrate              # Run schema migrations
    python migration/migrate.py seed <file> [limit]  # Seed data from file
    python migration/migrate.py test                 # Test connections

Examples:
    python migration/migrate.py migrate
    python migration/migrate.py seed /app/wkbk_lean.sql 100
    python migration/migrate.py seed /app/wkbk_lean.sql
    python migration/migrate.py test
"""

import sys
import os
from pathlib import Path

# Add current directory to path to import manage_migration_rest
sys.path.insert(0, str(Path(__file__).parent))

from manage_migration_rest import SupabaseRESTMigrationManager


def print_usage():
    """Print usage information."""
    print("Migration Management Helper")
    print()
    print("Usage:")
    print("  python migration/migrate.py migrate                    # Run schema migrations")
    print("  python migration/migrate.py seed <file> [limit] [flags] # Seed data from file")
    print("  python migration/migrate.py test                       # Test connections")
    print()
    print("Commands:")
    print("  migrate         Run database schema migrations via DATABASE_URL")
    print("  seed <file>     Seed database from SQL file via PostgREST API")
    print("                  Optional [limit] parameter to limit number of rows")
    print("                  Optional flags: --upsert, --force")
    print("  test            Test both DATABASE_URL and REST API connections")
    print()
    print("Seed Modes:")
    print("  Default         INSERT only (fails on duplicates)")
    print("  --upsert        UPSERT mode (update existing, insert new)")
    print("  --force         FORCE mode (clear table before seeding)")
    print()
    print("Environment Variables Required:")
    print("  DATABASE_URL          PostgreSQL connection string (for schema migrations)")
    print("  SUPABASE_URL          Supabase REST API URL")
    print("  SUPABASE_SECRET_KEY   Supabase service role key")
    print()
    print("Examples:")
    print("  python migration/migrate.py test")
    print("  python migration/migrate.py migrate")
    print("  python migration/migrate.py seed /app/wkbk_lean.sql")
    print("  python migration/migrate.py seed /app/wkbk_lean.sql 100")
    print("  python migration/migrate.py seed /app/wkbk_lean.sql 100 --upsert")
    print("  python migration/migrate.py seed /app/wkbk_lean.sql --force")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Validate command
    if command not in ['migrate', 'seed', 'test']:
        print(f"Error: Unknown command '{command}'")
        print()
        print_usage()
        sys.exit(1)
    
    try:
        # Initialize manager
        manager = SupabaseRESTMigrationManager()
        
        if command == 'test':
            print("Testing database connections...")
            print()
            success = manager.test_connection()
            sys.exit(0 if success else 1)
        
        elif command == 'migrate':
            print("Running schema migrations...")
            print()
            success = manager.run_migrations()
            sys.exit(0 if success else 1)
        
        elif command == 'seed':
            if len(sys.argv) < 3:
                print("Error: seed command requires a file path")
                print()
                print("Usage: python migration/migrate.py seed <file_path> [limit] [--upsert|--force]")
                print()
                print("Examples:")
                print("  python migration/migrate.py seed /app/wkbk_lean.sql")
                print("  python migration/migrate.py seed /app/wkbk_lean.sql 100")
                print("  python migration/migrate.py seed /app/wkbk_lean.sql 100 --upsert")
                print("  python migration/migrate.py seed /app/wkbk_lean.sql --force")
                sys.exit(1)
            
            sql_file = sys.argv[2]
            
            # Parse remaining arguments (limit and flags)
            limit = None
            upsert = False
            force_clear = False
            
            for i in range(3, len(sys.argv)):
                arg = sys.argv[i]
                if arg == '--upsert':
                    upsert = True
                elif arg == '--force':
                    force_clear = True
                elif arg.isdigit():
                    limit = int(arg)
                else:
                    print(f"Error: Unknown argument '{arg}'")
                    print()
                    print("Valid arguments: <limit_number>, --upsert, --force")
                    sys.exit(1)
            
            # Validate: can't use both --upsert and --force
            if upsert and force_clear:
                print("Error: Cannot use both --upsert and --force together")
                print("  --upsert: Update existing rows, insert new")
                print("  --force:  Clear table first, then insert")
                sys.exit(1)
            
            # Check if file exists
            if not Path(sql_file).exists():
                print(f"Error: File not found: {sql_file}")
                sys.exit(1)
            
            print(f"Seeding database from: {sql_file}")
            if limit:
                print(f"Limit: {limit} rows")
            print()
            
            success = manager.seed_database(
                sql_file=sql_file,
                limit=limit,
                upsert=upsert,
                force_clear=force_clear
            )
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print()
        print("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
