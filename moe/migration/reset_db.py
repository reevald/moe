#!/usr/bin/env python3
"""
Reset database - Drop all tables and clear alembic version history.
WARNING: This will delete ALL data!
"""

import os
import sys
from sqlalchemy import create_engine, text

def get_database_url():
    """Get database URL from environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    return database_url

def reset_database():
    """Drop all tables and clear alembic version."""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("WARNING: This will drop ALL tables and delete ALL data!")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    with engine.connect() as conn:
        # Drop tables in correct order (respect foreign keys)
        print("\n1. Dropping tables...")
        
        # Drop submission_results first (has FK to submissions)
        try:
            conn.execute(text("DROP TABLE IF EXISTS submission_results CASCADE"))
            print("   ✓ Dropped submission_results")
        except Exception as e:
            print(f"   - submission_results: {e}")
        
        # Drop submissions (has FK to problems)
        try:
            conn.execute(text("DROP TABLE IF EXISTS submissions CASCADE"))
            print("   ✓ Dropped submissions")
        except Exception as e:
            print(f"   - submissions: {e}")
        
        # Drop problems
        try:
            conn.execute(text("DROP TABLE IF EXISTS problems CASCADE"))
            print("   ✓ Dropped problems")
        except Exception as e:
            print(f"   - problems: {e}")
        
        # Drop lean_theorems (if exists from old migrations)
        try:
            conn.execute(text("DROP TABLE IF EXISTS lean_theorems CASCADE"))
            print("   ✓ Dropped lean_theorems")
        except Exception as e:
            print(f"   - lean_theorems: {e}")
        
        # Clear alembic version history
        print("\n2. Clearing alembic version history...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            print("   ✓ Cleared alembic_version")
        except Exception as e:
            print(f"   - alembic_version: {e}")
        
        conn.commit()
    
    print("\n✓ Database reset complete!")
    print("\nNext steps:")
    print("  1. Delete migration files: rm migration/versions/*.py")
    print("  2. Create new migration: make docker-alembic-revision MSG=\"initial_schema\"")
    print("  3. Apply migration: make docker-alembic-upgrade")
    print("  4. Seed data: make docker-seed FILE=/app/wkbk_lean.sql")

if __name__ == "__main__":
    try:
        reset_database()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
