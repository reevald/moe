#!/bin/bash
# MOE Stop Script
# Stops all MOE services gracefully

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Stopping MOE Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop services in reverse order
echo -e "${YELLOW}[1/3] Stopping MOE Services...${NC}"
cd "$SCRIPT_DIR/svc-moe"
docker compose down
echo -e "${GREEN}✓ MOE services stopped${NC}"
echo ""

echo -e "${YELLOW}[2/3] Stopping Lean LSP MCP Server...${NC}"
cd "$SCRIPT_DIR/svc-lean-lsp-mcp"
docker compose down
echo -e "${GREEN}✓ Lean LSP MCP stopped${NC}"
echo ""

echo -e "${YELLOW}[3/3] Stopping Nginx Proxy...${NC}"
cd "$SCRIPT_DIR/svc-nginx-proxy"
docker compose down
echo -e "${GREEN}✓ Nginx Proxy stopped (proxy-net network removed)${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   All services stopped${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}To start services again:${NC}"
echo "  cd deployments && ./run.sh"
echo ""
