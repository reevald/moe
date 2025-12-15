# MOE (Math Olympiad Evaluator)

An automated system for evaluating mathematical proofs written in LaTeX by converting them to Lean4 formal proofs and verifying their correctness.

## Architecture

```mermaid
graph TB
    User[User] -->|HTTP Request| Nginx[Nginx Proxy :8154]
    Nginx -->|/api/v1/*| API[MOE API :8001]
    API -->|Store Submission| DB[(Supabase PostgreSQL)]
    API -->|Queue Task| Redis[(Redis :8479)]
    Redis -->|Process Task| Worker[Celery Worker]
    Worker -->|Verify Lean Proof| MCP[Lean LSP MCP :8002]
    Worker -->|LLM Conversion| OpenRouter[OpenRouter API]
    Worker -->|Store Result| DB
    Worker -->|Observability| Langfuse[Langfuse Cloud]
    
    style Nginx fill:#85C1E2
    style API fill:#8FBC8F
    style Worker fill:#DDA15E
    style MCP fill:#BC6C25
    style Redis fill:#DC143C
    style DB fill:#4682B4
```

## Flow

1. User submits a LaTeX solution via API
2. API stores submission in database (status: pending)
3. Celery task is queued in Redis
4. Worker processes the task:
   - Converts LaTeX to Lean4 using OpenRouter LLM
   - Validates Lean proof using Lean LSP MCP server
   - Stores result in database
5. User polls submission status and retrieves result

## API Endpoints

Base URL: `http://localhost:8154/api/v1`

### 1. Health Check
```http
GET /health
```
Check service health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

### 2. Get Random Problem
```http
GET /moe/problems/random
Authorization: Bearer <token>
```
Retrieve a random math problem from the database.

**Response:**
```json
{
  "success": true,
  "data": {
    "problem_id": "lean_workbook_plus_1234",
    "statement_latex": "Prove that for all positive integers n, ..."
  }
}
```

### 3. Get Problem by ID
```http
GET /moe/problems/{problem_id}
Authorization: Bearer <token>
```
Retrieve a specific problem by its ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "problem_id": "lean_workbook_plus_1234",
    "statement_latex": "Prove that for all positive integers n, ..."
  }
}
```

### 4. Submit Solution
```http
POST /moe/submissions
Authorization: Bearer <token>
Content-Type: application/json

{
  "problem_id": "lean_workbook_plus_1234",
  "solution_latex": "We proceed by induction. Base case: ..."
}
```
Submit a LaTeX solution for evaluation.

**Response:**
```json
{
  "success": true,
  "data": {
    "submission_id": "sub_abc123",
    "problem_id": "lean_workbook_plus_1234",
    "status": "pending",
    "submitted_at": "2025-12-15T10:30:00Z"
  }
}
```

### 5. Get Submission Status
```http
GET /moe/submissions/{submission_id}/status
Authorization: Bearer <token>
```
Check the current processing status of a submission.

**Response:**
```json
{
  "success": true,
  "data": {
    "submission_id": "sub_abc123",
    "problem_id": "lean_workbook_plus_1234",
    "status": "processing",
    "progress": 50,
    "submitted_at": "2025-12-15T10:30:00Z",
    "updated_at": "2025-12-15T10:30:15Z"
  }
}
```

### 6. Get Submission Result
```http
GET /moe/submissions/{submission_id}/result
Authorization: Bearer <token>
```
Retrieve the evaluation result of a completed submission.

**Response:**
```json
{
  "success": true,
  "data": {
    "submission_id": "sub_abc123",
    "problem_id": "lean_workbook_plus_1234",
    "status": "completed",
    "submitted_at": "2025-12-15T10:30:00Z",
    "evaluated_at": "2025-12-15T10:30:45Z",
    "result": {
      "verdict": "accepted",
      "lean_validation": {
        "is_valid": true,
        "status": "proved",
        "errors": [],
        "remaining_goals": []
      },
      "feedback": ["Proof is correct and complete"]
    }
  }
}
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Supabase account (PostgreSQL database)
- OpenRouter API key (for LLM)
- Langfuse account (for observability)

### 1. Configuration

Create environment files from examples:

```bash
# Lean LSP MCP configuration
cp deployments/svc-lean-lsp-mcp/.env.example deployments/svc-lean-lsp-mcp/.env

# MOE API & Worker configuration
cp deployments/svc-moe/.env.example deployments/svc-moe/.env
```

Edit `deployments/svc-moe/.env` with your credentials:

```bash
# Authentication
STATIC_TOKEN=your-secure-token-here

# OpenRouter LLM
OPENROUTER_API_KEY=sk-or-v1-...
MATH_MODEL_NAME=deepseek/deepseek-v3.2

# Langfuse Observability
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Supabase Database
SUPABASE_URL=https://PROJECT_ID.supabase.co/rest/v1
SUPABASE_SECRET_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.PROJECT_ID:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres

# Network Configuration
NETWORK_NAME=proxy-net         # Use proxy-net created by nginx
EXTERNAL_NETWORK_STATUS=true   # Join external network
```

**Important:** The `.env` files control network configuration:
- `svc-nginx-proxy` creates the `proxy-net` network
- `svc-moe` and `svc-lean-lsp-mcp` join as external network (controlled by NETWORK_NAME and EXTERNAL_NETWORK_STATUS)

### 2. Build Docker Images

Build all required images using Makefile:

```bash
cd moe

# Build all images at once
make docker-build-all

# Or build individually
make docker-build-api
make docker-build-worker
make docker-build-migration
```

Build Lean LSP MCP image:

```bash
cd lean_lsp_mcp
docker build -t lean_lsp_mcp:latest .
```

### 3. Initialize Langfuse Prompts

```bash
cd moe/worker/prompts
source ../../.env.worker  # or export your Langfuse credentials
./init_langfuse.sh
```

### 4. Database Migration & Seeding

Use Makefile commands for database operations:

```bash
cd moe

# Start migration container
make docker-migration-up

# Run migrations
make docker-migrate

# Seed database (all 18,985 problems)
make docker-seed FILE=/app/wkbk_lean.sql

# Optional: Seed limited rows for testing
make docker-seed FILE=/app/wkbk_lean.sql LIMIT=100

# Optional: Force re-seed (clear existing data)
make docker-seed FILE=/app/wkbk_lean.sql FORCE=true

# Stop migration container when done
make docker-migration-down
```

See `moe/Makefile` for more migration commands including:
- `make docker-alembic-upgrade` - Apply migrations
- `make docker-alembic-history` - View migration history
- `make docker-alembic-current` - Show current version

### 5. Start All Services

Use the docker compose runner:

```bash
cd deployments
./run.sh
```

This script will:
1. Check `.env` configurations
2. Start Nginx first (creates `proxy-net` network)
3. Start Lean LSP MCP (joins `proxy-net`)
4. Start MOE services (API and Worker join `proxy-net`)
5. Verify all containers are running
6. Restart Nginx to reload configuration and properly connect with moe-api

**Network Architecture:**
- Nginx creates `proxy-net` network
- All services join `proxy-net` as external network
- This allows nginx → API and worker → Lean LSP MCP communication

**Stop Services:**

```bash
cd deployments
./stop.sh
```

### 6. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8154/api/v1/health

# Get a random problem (replace token)
curl -H "Authorization: Bearer test-token-12345" \
  http://localhost:8154/api/v1/moe/problems/random
```

## Credits

### Lean LSP MCP
Based on [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp) by oOo0oOo

**Adjustments:**
- Containerization with Docker
- HTTP transport support
- Health check endpoint
- Integration testing scripts

### Lean Workbook Dataset
Based on [Lean-Workbook](https://huggingface.co/datasets/internlm/Lean-Workbook) by InternLM

**Adjustments:**
- Converted Parquet to SQL format
- Filtered for "proved" status only (18,985 problems)
- Optimized for PostgreSQL bulk import
- Used as seed data for initial problem database

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.
