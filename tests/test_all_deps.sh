#!/bin/bash
# Master test runner for all MOE service connections
# This script runs all connection tests in sequence

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  MOE Service Connection Tests${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Check if .env file exists
if [ -f "$SCRIPT_DIR/../moe/.env.worker" ]; then
    echo -e "${GREEN}Loading environment from .env.worker${NC}"
    set -a
    source "$SCRIPT_DIR/../moe/.env.worker"
    set +a
elif [ -f "$SCRIPT_DIR/../.env.test" ]; then
    echo -e "${GREEN}Loading environment from .env.test${NC}"
    set -a
    source "$SCRIPT_DIR/../.env.test"
    set +a
else
    echo -e "${YELLOW}No .env file found. Using environment variables.${NC}"
fi

echo ""

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Function to run a test
run_test() {
    local test_name=$1
    local test_script=$2
    local optional=$3
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Running: ${test_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if python3 "$SCRIPT_DIR/$test_script"; then
        echo -e "${GREEN}✓ ${test_name} PASSED${NC}"
        ((TESTS_PASSED++))
    else
        if [ "$optional" = "true" ]; then
            echo -e "${YELLOW}⚠ ${test_name} FAILED (optional)${NC}"
        else
            echo -e "${RED}✗ ${test_name} FAILED${NC}"
            FAILED_TESTS+=("$test_name")
        fi
        ((TESTS_FAILED++))
    fi
}

# Run tests
echo -e "${BLUE}Starting connection tests...${NC}\n"

# Test 1: LLM (OpenRouter)
run_test "OpenRouter LLM Connection" "test_openrouter_llm.py" "false"

# Test 2: Langfuse
run_test "Langfuse Connection" "test_langfuse.py" "false"

# Test 3: Sentry (Optional)
run_test "Sentry Connection" "test_sentry.py" "true"

# Test 4: Lean LSP MCP
run_test "Lean LSP MCP Connection" "test_lean_lsp_mcp.py" "false"

# Print summary
echo -e "\n${BLUE}===============================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "${RED}  - $test${NC}"
    done
fi

echo -e "${BLUE}===============================================${NC}\n"

# Exit with appropriate code
if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    exit 1
else
    echo -e "${GREEN}All critical tests passed!${NC}\n"
    exit 0
fi
