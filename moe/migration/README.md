# MOE Database Migration System

Pure Alembic-based migration system for the MOE project using Supabase (PostgreSQL).

## Architecture

**Pure Alembic Approach:**
- Schema changes: Managed by Alembic migrations (DDL: CREATE TABLE, ALTER TABLE)
- Data seeding: Managed by PostgREST API (DML: INSERT, UPSERT)
- Version tracking: Alembic version files + `alembic_version` table in database

## Quick Start

### 1. Setup Environment

Create `.env.migration` file:
```bash
DATABASE_URL=postgresql://postgres.PROJECT_ID:PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_SECRET_KEY=eyJ...  # Service role key
```

### 2. Build and Start Container

```bash
make docker-build-migration   # Build image (~3-4 min)
make docker-migration-up      # Start container with volumes
```

### 3. Run Initial Migration

```bash
make docker-alembic-upgrade   # Apply schema migrations
```

### 4. Seed Data

```bash
# Seed all data from wkbk_lean.sql (18,985 problems)
make docker-seed FILE=/app/wkbk_lean.sql

# Seed limited rows
make docker-seed FILE=/app/wkbk_lean.sql LIMIT=100

# Re-seed with UPSERT mode (update existing, insert new)
make docker-seed FILE=/app/wkbk_lean.sql UPSERT=true

# Force clear and re-seed
make docker-seed FILE=/app/wkbk_lean.sql FORCE=true
```

## Migration Workflow

### Creating a New Migration

**Auto-generate from model changes:**
```bash
# 1. Edit models in common/models/
vim common/models/problem.py

# 2. Rebuild Docker image (models are in image)
make docker-migration-down
make docker-build-migration
make docker-migration-up

# 3. Auto-generate migration from model changes
make docker-alembic-autogenerate MSG="add_difficulty_column"

# 4. Review generated file
cat migration/versions/XXXXX_add_difficulty_column.py

# 5. Apply migration
make docker-alembic-upgrade
```

**Manual migration (empty template):**
```bash
make docker-alembic-revision MSG="add_custom_constraint"
# Edit the generated file
make docker-alembic-upgrade
```

### Checking Migration Status

```bash
make docker-alembic-current   # Current version
make docker-alembic-history   # Full history
```

### Rolling Back

```bash
make docker-alembic-downgrade  # Rollback last migration
make docker-alembic-upgrade    # Re-apply to latest
```

## Database Schema

Current schema (version `4ad734eb5a1a`):

### problems
- `problem_id` (String(50), PK, indexed)
- `statement_latex` (Text, required)
- `statement_lean` (Text, required)
- `state_before_lean` (Text, required)
- `state_after_lean` (Text, required)
- `tactic_lean` (Text, required)
- `created_at` (DateTime with timezone, auto)
- `updated_at` (DateTime with timezone, auto)

### submissions
- `submission_id` (String(50), PK, indexed)
- `problem_id` (String(50), FK → problems.problem_id, indexed)
- `submission_latex` (Text, required)
- `status` (String(20), default='pending')
- `progress` (Integer, default=0)
- `submitted_at` (DateTime with timezone, auto)
- `updated_at` (DateTime with timezone, auto)
- `evaluated_at` (DateTime with timezone, nullable)

### submission_results
- `id` (Integer, PK, autoincrement)
- `submission_id` (String(50), FK → submissions.submission_id, unique, indexed)
- `verdict` (String(20), required)
- `lean_is_valid` (Boolean, required)
- `lean_status` (String(20), required)
- `lean_errors` (JSON, nullable)
- `lean_remaining_goals` (JSON, nullable)
- `feedback` (JSON, nullable)
- `created_at` (DateTime with timezone, auto)

## Data Seeding Modes

### INSERT (Default)
```bash
make docker-seed FILE=/app/wkbk_lean.sql LIMIT=100
```
- Behavior: Plain INSERT, fails if duplicate key exists
- Use case: First-time seeding
- Safe: No accidental overwrites

### UPSERT
```bash
make docker-seed FILE=/app/wkbk_lean.sql UPSERT=true
```
- Behavior: ON CONFLICT UPDATE (updates existing, inserts new)
- Use case: Re-seeding, updating data when source changes
- Idempotent: Can run multiple times

### FORCE
```bash
make docker-seed FILE=/app/wkbk_lean.sql FORCE=true
```
- Behavior: DELETE FROM table first, then INSERT
- Use case: Development/testing, need clean slate
- Destructive: Removes all existing data

## Reset and Clean Slate

To completely reset the database and migration history:

```bash
make docker-reset-db
```

This will:
1. Drop all tables (problems, submissions, submission_results)
2. Clear alembic_version table
3. Reset migration history

After reset, you need to:
1. Delete migration files: `rm migration/versions/*.py`
2. Create new initial migration
3. Apply migration
4. Seed data

## Project Structure

```
migration/
├── alembic.ini                 # Alembic configuration
├── env.py                      # Alembic environment (DATABASE_URL support)
├── reset_db.py                 # Reset script (drop all tables)
├── manage_migration_rest.py    # PostgREST seeding manager
├── migrate.py                  # CLI helper
└── versions/                   # Migration files (version controlled)
    └── 4ad734eb5a1a_initial_schema.py
```

## Available Commands

### Container Management
```bash
make docker-migration-up        # Start container
make docker-migration-down      # Stop and remove container
make docker-build-migration     # Build Docker image
```

### Database Operations
```bash
make docker-test-db             # Test connections
make docker-migrate             # Run schema migrations (alias for upgrade)
make docker-seed FILE=<file>    # Seed data
make docker-reset-db            # Drop all tables
```

### Alembic Commands
```bash
make docker-alembic-autogenerate MSG="description"  # Auto-generate from models
make docker-alembic-revision MSG="description"      # Create empty migration
make docker-alembic-upgrade                         # Apply migrations
make docker-alembic-downgrade                       # Rollback last migration
make docker-alembic-history                         # Show history
make docker-alembic-current                         # Show current version
```

## Connection Details

### DATABASE_URL (Direct PostgreSQL)
- Used for: Schema migrations (DDL operations)
- Port: 6543 (transaction pooler)
- Better for: CREATE TABLE, ALTER TABLE, indexes

### PostgREST API
- Used for: Data operations (DML operations)
- Endpoint: https://PROJECT_ID.supabase.co/rest/v1
- Better for: Bulk INSERT, batch operations

## Troubleshooting

### Migration file not appearing in container
**Problem:** Created migration on host but container can't see it  
**Solution:** Migration files are volume-mounted at `migration/versions/`, changes should sync automatically

### lean_theorems table being created
**Problem:** Old model still in Docker image  
**Solution:** Rebuild image with `make docker-build-migration`

### Can't connect to database
**Problem:** DATABASE_URL or credentials incorrect  
**Solution:** Check `.env.migration`, test with `make docker-test-db`

### Duplicate key errors during seeding
**Problem:** Data already exists  
**Solution:** Use `UPSERT=true` or `FORCE=true` mode

## Best Practices

1. **Always version control migrations** - `migration/versions/*.py` files
2. **Review auto-generated migrations** - Alembic may miss custom constraints
3. **Test migrations on dev first** - Never run untested migrations on production
4. **Use descriptive migration messages** - "add_difficulty_column" not "update"
5. **Keep migrations small** - One logical change per migration
6. **Don't edit applied migrations** - Create new migration to fix issues
7. **Separate schema from data** - Use Alembic for schema, PostgREST for data

## Migration History

- `4ad734eb5a1a` - initial_schema (2025-12-14)
  - Created problems, submissions, submission_results tables
  - Added indexes and foreign key constraints
  - Pure schema, no data seeding

## Future Migrations

When adding new features:
1. Update SQLAlchemy models in `common/models/`
2. Rebuild Docker image
3. Auto-generate migration
4. Review and test
5. Apply to database
6. Commit migration file to git

Example:
```bash
# Add difficulty field to Problem model
vim common/models/problem.py

# Rebuild and create migration
make docker-migration-down
make docker-build-migration
make docker-migration-up
make docker-alembic-autogenerate MSG="add_difficulty_to_problems"

# Review
cat migration/versions/XXXXX_add_difficulty_to_problems.py

# Apply
make docker-alembic-upgrade

# Commit
git add migration/versions/XXXXX_add_difficulty_to_problems.py
git commit -m "migration: add difficulty column to problems table"
```
