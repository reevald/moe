# MOE Service Connection Tests

This directory contains test scripts to verify connections to all external services used by the MOE (Math Olympiad Exercises) system.

## Test Scripts

### 1. `test_openrouter_llm.py`
Tests connection to OpenRouter LLM API.

**Required Environment Variables:**
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `OPENROUTER_BASE_URL` - Base URL (default: https://openrouter.ai/api/v1)
- `MATH_MODEL_NAME` - Model name (default: deepseek/deepseek-math-7b-instruct)

**Tests:**
- Client initialization
- Simple completion
- Math proof validation
- LaTeX to Lean conversion capability

### 2. `test_langfuse.py`
Tests connection to Langfuse for prompt management and LLM observability.

**Required Environment Variables:**
- `LANGFUSE_SECRET_KEY` - Your Langfuse secret key
- `LANGFUSE_PUBLIC_KEY` - Your Langfuse public key
- `LANGFUSE_BASE_URL` - Base URL (default: https://cloud.langfuse.com)

**Tests:**
- Client initialization
- Trace creation
- Prompt fetching (guardrail_check, latex_to_lean, feedback_generation)
- Prompt compilation
- PromptManager module

### 3. `test_sentry.py`
Tests connection to Sentry.io for error tracking and performance monitoring.

**Required Environment Variables:**
- `SENTRY_DSN` - Your Sentry project DSN
- `SENTRY_ENVIRONMENT` - Environment name (default: development)
- `SENTRY_TRACES_SAMPLE_RATE` - Trace sampling rate (default: 0.1)

**Tests:**
- SDK initialization
- Message capture
- Exception capture
- Transaction creation
- Context and breadcrumbs

**Note:** Sentry is optional. Tests will warn but not fail if DSN is not provided.

### 4. `test_lean_lsp_mcp.py`
Tests connection to Lean LSP MCP server for Lean 4 proof verification.

**Required Environment Variables:**
- `LEAN_LSP_MCP_URL` - Server URL (default: http://localhost:8000)
- `LEAN_LSP_MCP_TOKEN` - Optional bearer token for authentication

**Tests:**
- Server health check
- List available tools
- `lean_goal` tool
- `lean_diagnostic_messages` tool

**Prerequisites:**
- Lean LSP MCP server must be running with `--transport streamable-http`

## Running Tests

### Run All Tests
```bash
./run_all_tests.sh
```

This will run all tests in sequence and provide a summary.

### Run Individual Tests
```bash
# Test OpenRouter LLM
python3 test_openrouter_llm.py

# Test Langfuse
python3 test_langfuse.py

# Test Sentry
python3 test_sentry.py

# Test Lean LSP MCP
python3 test_lean_lsp_mcp.py
```

## Environment Setup

### Option 1: Use .env.worker
Copy and configure the worker environment file:
```bash
cp ../moe/.env.worker.example ../moe/.env.worker
# Edit .env.worker with your credentials
```

The test runner will automatically load `.env.worker` if it exists.

### Option 2: Use .env.test
Create a test-specific environment file:
```bash
cp ../.env.test.example ../.env.test
# Edit .env.test with your credentials
```

### Option 3: Export Environment Variables
```bash
export OPENROUTER_API_KEY="your-key"
export LANGFUSE_SECRET_KEY="your-secret"
export LANGFUSE_PUBLIC_KEY="your-public-key"
# ... etc
```

## Expected Results

All tests should pass with green checkmarks:
```
✓ OpenRouter LLM Connection PASSED
✓ Langfuse Connection PASSED
⚠ Sentry Connection FAILED (optional)
✓ Lean LSP MCP Connection PASSED
```

## Troubleshooting

### OpenRouter LLM Tests Fail
- Verify your API key is correct
- Check your OpenRouter account has credits
- Ensure the model name is correct

### Langfuse Tests Fail
- Verify secret and public keys are correct
- Check if prompts are initialized (run `init_langfuse.sh`)
- Ensure you have access to the Langfuse project

### Sentry Tests Fail
- Verify DSN is correct
- Check Sentry project settings
- Note: Sentry is optional and warnings can be ignored

### Lean LSP MCP Tests Fail
- Ensure Lean LSP MCP server is running
- Check server URL is correct
- Verify server is using `streamable-http` transport
- Check token if authentication is enabled

## Integration with Docker

These tests can also be run inside Docker containers to verify deployed services:

```bash
# Test from within API container
docker exec moe-api python3 /app/tests/test_openrouter_llm.py

# Test from within Worker container
docker exec moe-worker python3 /app/tests/test_langfuse.py
```

## Notes

- Tests use colored output for better readability
- All tests include detailed logging
- Failed tests exit with code 1
- Successful tests exit with code 0
- Test scripts are safe to run multiple times
