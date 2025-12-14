#!/usr/bin/env python3
"""
Hybrid Migration Manager for Supabase

Uses hybrid approach:
- DATABASE_URL (direct PostgreSQL) for schema migrations (CREATE TABLE, ALTER, etc.)
- PostgREST API (SUPABASE_URL) for data operations (seeding)

Usage:
    python manage_migration_rest.py test        # Test both connections
    python manage_migration_rest.py migrate     # Run migrations via DATABASE_URL
    python manage_migration_rest.py seed        # Seed database via PostgREST
    python manage_migration_rest.py all         # Run all operations

Environment Variables:
    DATABASE_URL - PostgreSQL connection string (for schema migrations)
    SUPABASE_URL - Supabase project REST API URL (for data operations)
    SUPABASE_SECRET_KEY - Supabase service role key (for data operations)
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

try:
    from supabase import create_client, Client  # type: ignore
    import requests  # type: ignore
    import psycopg2  # type: ignore
    HAS_DEPENDENCIES = True
except ImportError as e:
    HAS_DEPENDENCIES = False
    create_client = None  # type: ignore
    Client = None  # type: ignore
    requests = None  # type: ignore
    psycopg2 = None  # type: ignore
    print("ERROR: Required dependencies not installed.")
    print(f"Missing: {e}")
    print("Please install: pip install supabase requests psycopg2-binary")
    sys.exit(1)


class SupabaseRESTMigrationManager:
    """Manages database migrations and seeding using hybrid approach."""
    
    def __init__(self):
        """Initialize with both DATABASE_URL and Supabase credentials."""
        # Get DATABASE_URL for schema migrations
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            print("⚠ WARNING: DATABASE_URL not set. Schema migrations will not work.")
            self.database_url = None
        else:
            # Fix URL encoding if needed
            self.database_url = self._fix_database_url(self.database_url)
            print(f"✓ DATABASE_URL loaded (for schema migrations)")
        
        # Get Supabase REST API credentials for data operations
        supabase_url = os.environ.get("SUPABASE_URL", "")
        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        
        # Remove /rest/v1 if present to get base URL
        self.base_url = supabase_url.replace("/rest/v1", "").rstrip("/")
        self.rest_url = f"{self.base_url}/rest/v1"
        
        # Get service role key
        self.service_key = os.environ.get("SUPABASE_SECRET_KEY")
        if not self.service_key:
            raise ValueError("SUPABASE_SECRET_KEY environment variable is required")
        
        # Initialize Supabase client for data operations
        print(f"  Base URL: {self.base_url}")
        print(f"  REST URL: {self.rest_url}")
        
        # Check if key looks valid (service role keys are JWT tokens, typically 180-250 chars)
        if len(self.service_key) < 100:
            print(f"⚠ WARNING: SUPABASE_SECRET_KEY seems too short ({len(self.service_key)} chars)")
            print(f"  Service role keys are typically 180-250 characters (JWT tokens)")
            print(f"  Your key starts with: {self.service_key[:20]}...")
            print(f"  Make sure you're using the 'service_role' key, not 'anon' key")
            print(f"  REST API operations may fail")
        
        if not create_client:
            raise ImportError("supabase library not available")
        
        try:
            self.client = create_client(self.base_url, self.service_key)
            print(f"✓ Supabase REST client initialized (for data operations)")
        except Exception as e:
            print(f"✗ Failed to initialize Supabase client: {e}")
            print(f"  REST API operations will not work")
            self.client = None
    
    def _fix_database_url(self, url: str) -> str:
        """
        Fix DATABASE_URL encoding if password has special characters.
        
        Args:
            url: Original DATABASE_URL
            
        Returns:
            Fixed DATABASE_URL with properly encoded password
        """
        from urllib.parse import quote_plus, urlparse, urlunparse
        
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # If password contains special chars, re-encode
            if parsed.password and any(c in parsed.password for c in ['*', '%', '@', '!', '#']):
                # Reconstruct with encoded password
                netloc = f"{parsed.username}:{quote_plus(parsed.password)}@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                
                fixed = urlunparse((
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                return fixed
        except Exception:
            pass
        
        return url
    

    def test_connection(self) -> bool:
        """
        Test both DATABASE_URL and Supabase REST API connections.
        
        Returns:
            bool: True if both connections successful
        """
        print("=" * 60)
        print("Hybrid Connection Test")
        print("=" * 60)
        print()
        
        all_success = True
        
        # Test 1: DATABASE_URL connection
        print("Test 1: PostgreSQL Direct Connection (DATABASE_URL)")
        print("-" * 60)
        if not self.database_url:
            print("✗ DATABASE_URL not set")
            print("  Schema migrations will not work")
            all_success = False
        else:
            try:
                if not psycopg2:
                    raise ImportError("psycopg2 not available")
                conn = psycopg2.connect(self.database_url)
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"✓ PostgreSQL connection successful")
                if version:
                    print(f"  Version: {version[0][:50]}...")
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"✗ PostgreSQL connection failed: {e}")
                all_success = False
        
        print()
        
        # Test 2: REST API connection
        print("Test 2: Supabase REST API Connection")
        print("-" * 60)
        
        try:
            # Check if we can access the REST API
            if not requests:
                raise ImportError("requests library not available")
            headers = {
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}"
            }
            
            response = requests.get(f"{self.rest_url}/", headers=headers)  # type: ignore
            if response.status_code == 200:
                print("✓ REST API accessible")
            else:
                print(f"⚠ REST API returned status: {response.status_code}")
                all_success = False
            
            print()
            print("=" * 60)
            if all_success:
                print("✓ All connections successful!")
            else:
                print("⚠ Some connections failed")
            print("=" * 60)
            return all_success
            
        except Exception as e:
            print()
            print("=" * 60)
            print("✗ REST API connection failed!")
            print("=" * 60)
            print()
            print(f"Error: {e}")
            print()
            print("Troubleshooting:")
            print("  1. Check SUPABASE_URL is correct")
            print("  2. Check SUPABASE_SECRET_KEY is valid (service role)")
            print("  3. Verify project is active")
            print("  4. Check network connectivity")
            return False
    
    def run_migrations(self) -> bool:
        """
        Run database migrations using direct PostgreSQL connection.
        
        Uses DATABASE_URL to execute DDL statements (CREATE TABLE, etc.)
        
        Returns:
            bool: True if successful
        """
        print("=" * 60)
        print("Running Migrations via DATABASE_URL (Direct PostgreSQL)")
        print("=" * 60)
        print()
        
        if not self.database_url:
            print("✗ DATABASE_URL not set")
            print("  Cannot run schema migrations without DATABASE_URL")
            return False
        
        if not psycopg2:
            print("✗ psycopg2 not available")
            return False
        
        # Read create_tables.sql
        sql_file = Path("create_tables.sql")
        if not sql_file.exists():
            print(f"✗ SQL file not found: {sql_file.absolute()}")
            return False
        
        print(f"SQL file: {sql_file.absolute()}")
        print()
        
        try:
            print("Connecting to database...")
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            print("✓ Connected successfully")
            print()
            
            print("Reading create_tables.sql...")
            sql_content = sql_file.read_text(encoding='utf-8')
            
            print("Executing DDL statements...")
            cursor.execute(sql_content)
            conn.commit()
            print("✓ Tables created successfully!")
            print()
            
            # Verify tables exist
            print("Verifying tables...")
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('problems', 'submissions', 'submission_results')
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            if tables:
                print(f"✓ Created tables: {[t[0] for t in tables]}")
            else:
                print("⚠ No tables found (they might already exist)")
            
            cursor.close()
            conn.close()
            
            print()
            print("=" * 60)
            print("✓ Migration completed!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print()
            print("=" * 60)
            print("✗ Migration failed!")
            print("=" * 60)
            print()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def seed_database_direct(self, sql_file: str = "wkbk_lean.sql",
                            limit: Optional[int] = None) -> bool:
        """
        Seed database using direct PostgreSQL connection (DATABASE_URL).
        Fallback method when REST API is not available.
        
        Args:
            sql_file: Path to SQL file (wkbk_lean.sql)
            limit: Optional limit on number of rows to insert (for testing)
            
        Returns:
            bool: True if successful
        """
        print("=" * 60)
        print("Seeding Database via DATABASE_URL (Direct PostgreSQL)")
        print("=" * 60)
        print()
        
        if not self.database_url:
            print("✗ DATABASE_URL not set")
            return False
        
        if not psycopg2:
            print("✗ psycopg2 not available")
            return False
        
        # Check if SQL file exists
        sql_path = Path(sql_file)
        if not sql_path.exists():
            print(f"✗ SQL file not found: {sql_path.absolute()}")
            return False
        
        print(f"SQL file: {sql_path.absolute()}")
        print(f"File size: {sql_path.stat().st_size / 1024:.2f} KB")
        print()
        
        try:
            # Read and parse SQL file
            print("Reading SQL file...")
            sql_content = sql_path.read_text(encoding='utf-8')
            
            print("Parsing problems data...")
            problems_data = self._parse_problems_sql(sql_content)
            
            if not problems_data:
                print("✗ No data found in SQL file")
                return False
            
            print(f"Parsed {len(problems_data)} problems from SQL")
            print()
            
            # Apply limit if specified
            if limit and limit > 0:
                problems_data = problems_data[:limit]
                print(f"⚠ LIMIT APPLIED: Only inserting first {limit} rows")
                print()
            
            # Connect to database
            print("Connecting to database...")
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            print("✓ Connected successfully")
            print()
            
            # Insert data
            print(f"Inserting into problems table...")
            print(f"  Total rows: {len(problems_data)}")
            print()
            
            batch_size = 100
            total_batches = (len(problems_data) + batch_size - 1) // batch_size
            
            insert_sql = """
                INSERT INTO problems 
                (problem_id, tactic_lean, state_after_lean, state_before_lean, 
                 statement_latex, statement_lean)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (problem_id) DO NOTHING
            """
            
            for i in range(0, len(problems_data), batch_size):
                batch = problems_data[i:i+batch_size]
                batch_num = i//batch_size + 1
                
                try:
                    # Prepare batch data
                    batch_values = [
                        (
                            p['problem_id'],
                            p['tactic_lean'],
                            p['state_after_lean'],
                            p['state_before_lean'],
                            p['statement_latex'],
                            p['statement_lean']
                        )
                        for p in batch
                    ]
                    
                    # Execute batch insert
                    cursor.executemany(insert_sql, batch_values)
                    conn.commit()
                    
                    print(f"  ✓ Batch {batch_num}/{total_batches} ({len(batch)} rows)")
                except Exception as e:
                    print(f"  ✗ Error inserting batch {batch_num}: {e}")
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return False
            
            cursor.close()
            conn.close()
            
            print()
            print(f"✓ Completed problems table: {len(problems_data)} rows")
            print()
            print("=" * 60)
            print("✓ Database seeding completed!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print()
            print("=" * 60)
            print("✗ Seeding failed!")
            print("=" * 60)
            print()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def seed_database(self, sql_file: str = "wkbk_lean.sql",
                     limit: Optional[int] = None,
                     upsert: bool = False,
                     force_clear: bool = False) -> bool:
        """
        Seed database using Supabase PostgREST API.
        This is the preferred method for seeding data.
        
        Args:
            sql_file: Path to SQL file (wkbk_lean.sql)
            limit: Optional limit on number of rows to insert (for testing)
            upsert: If True, use UPSERT mode (update existing, insert new). Default: False
            force_clear: If True, clear table before seeding. Default: False
            
        Returns:
            bool: True if successful
        """
        print("=" * 60)
        print("Seeding Database via PostgREST API")
        print("=" * 60)
        print()
        
        # Show mode
        if force_clear:
            print("🔥 MODE: FORCE (Clear table before seeding)")
        elif upsert:
            print("🔄 MODE: UPSERT (Update existing, insert new)")
        else:
            print("➕ MODE: INSERT (Fail on duplicates - default)")
        print()
        
        # Check if Supabase client is initialized
        if not self.client:
            print("✗ Supabase client not initialized")
            print("  Check your SUPABASE_SECRET_KEY (should be service_role key)")
            return False
        
        # FORCE mode: Clear table first
        if force_clear:
            if not self.database_url:
                print("✗ FORCE mode requires DATABASE_URL to be set")
                return False
            
            try:
                print("Clearing problems table...")
                if not psycopg2:
                    raise ImportError("psycopg2 not available")
                conn = psycopg2.connect(self.database_url)
                cur = conn.cursor()
                cur.execute('DELETE FROM problems;')
                conn.commit()
                deleted_count = cur.rowcount
                cur.close()
                conn.close()
                print(f"✓ Cleared {deleted_count} rows from problems table")
                print()
            except Exception as e:
                print(f"✗ Failed to clear table: {e}")
                return False
        
        # Check if SQL file exists
        sql_path = Path(sql_file)
        if not sql_path.exists():
            print(f"✗ SQL file not found: {sql_path.absolute()}")
            return False
        
        print(f"SQL file: {sql_path.absolute()}")
        print(f"File size: {sql_path.stat().st_size / 1024:.2f} KB")
        print()
        
        try:
            # Read SQL file
            print("Reading SQL file...")
            sql_content = sql_path.read_text(encoding='utf-8')
            
            # Parse problems INSERT statements
            print("Parsing problems data...")
            problems_data = self._parse_problems_sql(sql_content)
            
            if not problems_data:
                print("✗ No data found in SQL file")
                return False
            
            print(f"Parsed {len(problems_data)} problems from SQL")
            print()
            
            # Apply limit if specified
            if limit and limit > 0:
                problems_data = problems_data[:limit]
                print(f"⚠ LIMIT APPLIED: Only inserting first {limit} rows")
                print()
            
            # Insert/Upsert data using PostgREST into problems table
            operation = "Upserting" if upsert else "Inserting"
            print(f"{operation} into problems table...")
            print(f"  Total rows: {len(problems_data)}")
            print()
            
            # Batch insert (PostgREST supports bulk inserts)
            batch_size = 100
            total_batches = (len(problems_data) + batch_size - 1) // batch_size
            
            for i in range(0, len(problems_data), batch_size):
                batch = problems_data[i:i+batch_size]
                batch_num = i//batch_size + 1
                
                try:
                    if upsert:
                        # UPSERT mode: update if exists, insert if not
                        response = self.client.table('problems').upsert(
                            batch
                        ).execute()
                    else:
                        # INSERT mode: fail on duplicate
                        response = self.client.table('problems').insert(
                            batch
                        ).execute()
                    print(f"  ✓ Batch {batch_num}/{total_batches} "
                          f"({len(batch)} rows)")
                except Exception as e:
                    print(f"  ✗ Error {operation.lower()} batch {batch_num}: {e}")
                    return False
            
            print()
            print(f"✓ Completed problems table: {len(problems_data)} rows")
            print()
            print("=" * 60)
            print("✓ Database seeding completed!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print()
            print("=" * 60)
            print("✗ Seeding failed!")
            print("=" * 60)
            print()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_problems_sql(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Parse problems table INSERT statements directly.
        
        The wkbk_lean.sql has format:
        INSERT INTO problems (problem_id, statement_latex, statement_lean, 
                             state_before_lean, state_after_lean, tactic_lean,
                             created_at, updated_at)
        VALUES ('id', 'latex', 'lean', 'before', 'after', 'tactic', ..., ...),
        
        Args:
            sql_content: SQL file content
            
        Returns:
            list: List of problem dictionaries ready for insertion
        """
        problems_data = []
        
        # Find ALL INSERT statements for problems table (there may be multiple)
        values_matches = re.finditer(
            r'INSERT INTO problems\s*\([^)]+\)\s*VALUES\s*(.+?)(?=INSERT INTO|$)',
            sql_content,
            re.DOTALL | re.IGNORECASE
        )
        
        # Collect all INSERT statements
        all_values_str = []
        for match in values_matches:
            all_values_str.append(match.group(1))
        
        if not all_values_str:
            print("⚠ No INSERT INTO problems found, trying lean_theorems format...")
            return self._parse_lean_theorems_to_problems(sql_content)
        
        # Combine all VALUES sections
        values_str = ' '.join(all_values_str)
        
        # Parse each row - handle nested parentheses and quotes properly
        rows = []
        depth = 0
        current_row = ""
        in_quote = False
        i = 0
        
        while i < len(values_str):
            char = values_str[i]
            
            # Handle quotes
            if char == "'" and (i == 0 or values_str[i-1] != '\\'):
                in_quote = not in_quote
                if depth > 0:
                    current_row += char
            # Handle parentheses only when not in quotes
            elif not in_quote:
                if char == '(':
                    depth += 1
                    if depth == 1:
                        current_row = ""
                    else:
                        current_row += char
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        if current_row.strip():  # Only add non-empty rows
                            rows.append(current_row)
                        current_row = ""
                    else:
                        current_row += char
                elif depth > 0:
                    current_row += char
            else:
                # Inside quotes
                if depth > 0:
                    current_row += char
            
            i += 1
        
        print(f"Found {len(rows)} problems to insert...")
        
        for i, row in enumerate(rows):
            # Parse the row values (problem_id, statement_latex, statement_lean, 
            # state_before_lean, state_after_lean, tactic_lean, created_at, updated_at)
            values = self._parse_sql_row(row)
            
            if len(values) >= 6:
                problem_id = values[0] or f'wkbk_{i+1:05d}'
                statement_latex = values[1] or 'No statement'
                statement_lean = values[2] or 'No statement'
                state_before_lean = values[3] or 'no state'
                state_after_lean = values[4] or 'no goals'
                tactic_lean = values[5] or ''
                
                problems_data.append({
                    'problem_id': problem_id,
                    'statement_latex': statement_latex,
                    'statement_lean': statement_lean,
                    'state_before_lean': state_before_lean,
                    'state_after_lean': state_after_lean,
                    'tactic_lean': tactic_lean
                })
            
            # Show progress
            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1} problems...")
        
        return problems_data
    
    def _parse_lean_theorems_to_problems(
        self, sql_content: str
    ) -> List[Dict[str, Any]]:
        """
        Parse lean_theorems INSERT statements and convert to problems format.
        
        The wkbk_lean.sql has format:
        INSERT INTO lean_theorems (tactic, state_after, state_before, 
                                   statement_latex, statement_lean)
        VALUES (...)
        
        We transform to problems table:
        - tactic -> tactic_lean
        - state_after -> state_after_lean
        - state_before -> state_before_lean  
        - statement_latex -> statement_latex
        - statement_lean -> statement_lean
        - generate problem_id from hash
        
        Args:
            sql_content: SQL file content
            
        Returns:
            list: List of problem dictionaries ready for insertion
        """
        import hashlib
        
        problems_data = []
        
        # Find the INSERT statement
        values_match = re.search(
            r'INSERT INTO lean_theorems.*?VALUES\s*(.+);',
            sql_content, 
            re.DOTALL | re.IGNORECASE
        )
        
        if not values_match:
            return []
        
        values_str = values_match.group(1)
        
        # Parse each row tuple - handle nested parentheses
        row_pattern = r'\(([^)]+(?:\([^)]*\)[^)]*)*)\)'
        rows = re.findall(row_pattern, values_str)
        
        print(f"Found {len(rows)} lean theorems to convert...")
        
        for i, row in enumerate(rows):
            # Parse the row values
            # Format: tactic, state_after, state_before, 
            # statement_latex, statement_lean
            values = self._parse_sql_row(row)
            
            if len(values) >= 5:
                tactic = values[0] or ''
                state_after = values[1] or 'no goals'
                state_before = values[2] or 'no state'
                statement_latex = values[3] or 'No statement'
                statement_lean = values[4] or 'No statement'
                
                # Generate problem_id from hash of content
                content_hash = hashlib.md5(
                    f"{statement_latex}{statement_lean}{tactic}".encode()
                ).hexdigest()[:16]
                problem_id = f"prob_{i+1:05d}_{content_hash}"
                
                problems_data.append({
                    'problem_id': problem_id,
                    'statement_latex': statement_latex,
                    'statement_lean': statement_lean,
                    'state_before_lean': state_before,
                    'state_after_lean': state_after,
                    'tactic_lean': tactic
                })
            
            # Show progress
            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1} theorems...")
        
        return problems_data
    
    def _parse_sql_row(self, row: str) -> List[str]:
        """
        Parse a single SQL row tuple into values.
        
        Args:
            row: Row string (inside parentheses)
            
        Returns:
            list: List of values
        """
        values = []
        current = ""
        in_quote = False
        
        for char in row + ',':
            if char == "'" and (not current or current[-1] != '\\'):
                in_quote = not in_quote
                current += char
            elif char == ',' and not in_quote:
                value = current.strip().strip("'")
                # Handle escaped quotes
                value = value.replace("''", "'")
                # Handle NULL
                if value.upper() == 'NULL':
                    value = None
                values.append(value)
                current = ""
            else:
                current += char
        
        return values

    
    def run_all(self, sql_file: str = "wkbk_lean.sql") -> bool:
        """
        Run all operations: test, migrate, seed.
        
        Args:
            sql_file: Path to SQL file for seeding
            
        Returns:
            bool: True if all successful
        """
        print()
        print("=" * 60)
        print("SUPABASE REST MIGRATION - Running All Operations")
        print("=" * 60)
        print()
        
        # Step 1: Test connection
        print("Step 1/3: Testing connection...")
        print()
        if not self.test_connection():
            print("\n✗ Cannot proceed - connection test failed")
            return False
        
        print()
        input("Press Enter to continue with migrations...")
        print()
        
        # Step 2: Run migrations (manual for now)
        print("Step 2/3: Migrations...")
        print()
        print("⚠ Migrations must be run manually via Supabase Dashboard")
        print("  Go to: SQL Editor in your Supabase Dashboard")
        print("  Run the migration SQL to create tables")
        print()
        
        input("Press Enter after completing migrations in Supabase Dashboard...")
        print()
        
        # Step 3: Seed database
        print("Step 3/3: Seeding database...")
        print()
        if not self.seed_database(sql_file):
            print("\n✗ Seeding failed")
            return False
        
        print()
        print("=" * 60)
        print("✓ SEEDING COMPLETED!")
        print("=" * 60)
        print()
        print("Note: For full automation, create the exec_sql RPC function")
        print("      in Supabase SQL Editor (see documentation)")
        return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Hybrid Migration Manager for Supabase")
        print()
        print("Usage:")
        print("  python manage_migration_rest.py test                         # Test connections")
        print("  python manage_migration_rest.py migrate                      # Run migrations (DATABASE_URL)")
        print("  python manage_migration_rest.py seed [sql_file] [limit]      # Seed via PostgREST")
        print("  python manage_migration_rest.py seed-direct [sql_file] [limit] # Seed via DATABASE_URL")
        print("  python manage_migration_rest.py all [sql_file]               # Run all")
        print()
        print("Environment Variables:")
        print("  DATABASE_URL - PostgreSQL connection (for schema migrations and direct seeding)")
        print("  SUPABASE_URL - Supabase REST API URL (optional, for REST API seeding)")
        print("  SUPABASE_SECRET_KEY - Supabase service role key (optional, for REST API seeding)")
        print()
        print("Examples:")
        print("  python manage_migration_rest.py test")
        print("  python manage_migration_rest.py seed-direct wkbk_lean.sql 150  # Seed first 150 rows")
        print("  python manage_migration_rest.py seed wkbk_lean.sql 100         # Seed via REST API")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        manager = SupabaseRESTMigrationManager()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    
    if command == "test":
        success = manager.test_connection()
        sys.exit(0 if success else 1)
    
    elif command == "migrate":
        success = manager.run_migrations()
        sys.exit(0 if success else 1)
    
    elif command == "seed":
        sql_file = sys.argv[2] if len(sys.argv) > 2 else "wkbk_lean.sql"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        success = manager.seed_database(sql_file, limit)
        sys.exit(0 if success else 1)
    
    elif command == "seed-direct":
        sql_file = sys.argv[2] if len(sys.argv) > 2 else "wkbk_lean.sql"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        success = manager.seed_database_direct(sql_file, limit)
        sys.exit(0 if success else 1)
    
    elif command == "all":
        sql_file = sys.argv[2] if len(sys.argv) > 2 else "wkbk_lean.sql"
        success = manager.run_all(sql_file)
        sys.exit(0 if success else 1)
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: test, migrate, seed, seed-direct, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
