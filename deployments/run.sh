#!/bin/bash
# MOE Docker Compose Runner
# Starts all services using docker compose
# 
# Prerequisites:
#   - Docker images built (use: cd ../moe && make docker-build-all)
#   - Database migrated (use: cd ../moe && make docker-migrate)
#   - Database seeded (use: cd ../moe && make docker-seed FILE=/app/wkbk_lean.sql)
#   - .env files configured in each svc-* directory

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
echo -e "${BLUE}   MOE Docker Compose Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if .env file exists
check_env_file() {
    local env_file="$1"
    local service_name="$2"
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}✗ $service_name .env file not found${NC}"
        echo -e "${YELLOW}  Please create: cp ${env_file}.example ${env_file}${NC}"
        return 1
    fi
    echo -e "${GREEN}✓${NC} $service_name .env configured"
    return 0
}

# Check configurations
echo -e "${YELLOW}Checking configurations...${NC}"
echo ""

ENV_CHECK_FAILED=false

if ! check_env_file "$SCRIPT_DIR/svc-lean-lsp-mcp/.env" "Lean LSP MCP"; then
    ENV_CHECK_FAILED=true
fi

if ! check_env_file "$SCRIPT_DIR/svc-moe/.env" "MOE"; then
    ENV_CHECK_FAILED=true
fi

if [ "$ENV_CHECK_FAILED" = true ]; then
    echo ""
    echo -e "${RED}Configuration check failed. Please fix the issues above.${NC}"
    exit 1
fi

echo ""

# Stop any existing containers
echo -e "${YELLOW}Stopping any existing containers...${NC}"
cd "$SCRIPT_DIR/svc-nginx-proxy" && docker compose down 2>/dev/null || true
cd "$SCRIPT_DIR/svc-moe" && docker compose down 2>/dev/null || true
cd "$SCRIPT_DIR/svc-lean-lsp-mcp" && docker compose down 2>/dev/null || true
echo ""

# Start services in correct order
echo -e "${BLUE}Starting services...${NC}"
echo ""

# 1. Start Nginx first (creates proxy-net network)
echo -e "${YELLOW}[1/3] Starting Nginx Proxy (port 8154)...${NC}"
echo -e "${BLUE}       → Creates proxy-net network${NC}"
cd "$SCRIPT_DIR/svc-nginx-proxy"
docker compose up -d || {
    echo -e "${RED}Failed to start Nginx proxy${NC}"
    exit 1
}
echo -e "${GREEN}✓ Nginx Proxy started and proxy-net network created${NC}"
echo ""

# Wait a moment for network to be ready
sleep 2

# 2. Start Lean LSP MCP (port 8002)
echo -e "${YELLOW}[2/3] Starting Lean LSP MCP Server (port 8002)...${NC}"
echo -e "${BLUE}       → Joins proxy-net network${NC}"
cd "$SCRIPT_DIR/svc-lean-lsp-mcp"
docker compose up -d || {
    echo -e "${RED}Failed to start Lean LSP MCP${NC}"
    exit 1
}
echo -e "${GREEN}✓ Lean LSP MCP started${NC}"
echo ""

# Wait for Lean LSP MCP to initialize
echo -e "${YELLOW}   Waiting for Lean LSP MCP to initialize...${NC}"
sleep 10

# 3. Start MOE services (API, Worker, Redis)
echo -e "${YELLOW}[3/3] Starting MOE Services (API :8001, Worker, Redis :8479)...${NC}"
echo -e "${BLUE}       → API joins proxy-net (for nginx)${NC}"
echo -e "${BLUE}       → Worker joins proxy-net (for lean_lsp_mcp_server)${NC}"
cd "$SCRIPT_DIR/svc-moe"
docker compose up -d redis api worker || {
    echo -e "${RED}Failed to start MOE services${NC}"
    exit 1
}
echo -e "${GREEN}✓ MOE services started${NC}"
echo ""

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5
echo ""

# Verify deployment
echo -e "${BLUE}Verifying deployment...${NC}"
echo ""

# Check container status
CONTAINERS_OK=true

check_container() {
    local container_name="$1"
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✓${NC} $container_name is running"
    else
        echo -e "${RED}✗${NC} $container_name is not running"
        CONTAINERS_OK=false
    fi
}

check_container "nginx-proxy"
check_container "lean_lsp_mcp_server"
check_container "moe-redis"
check_container "moe-api"
check_container "moe-worker"

echo ""

if [ "$CONTAINERS_OK" = false ]; then
    echo -e "${RED}Some containers failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker logs <container-name>${NC}"
    exit 1
fi

# Test health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
sleep 3
if curl -sf http://localhost:8154/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
else
    echo -e "${YELLOW}! Health endpoint not responding yet${NC}"
    echo -e "${YELLOW}  Services may still be starting up. Check logs if issue persists.${NC}"
fi

echo ""

# Restart nginx to reload configuration now that moe-api is running
echo -e "${BLUE}Final step: Restarting Nginx...${NC}"
echo -e "${YELLOW}Reloading nginx configuration to properly connect with moe-api...${NC}"
cd "$SCRIPT_DIR/svc-nginx-proxy"
if [ -f "restart-config-nginx.sh" ]; then
    chmod +x restart-config-nginx.sh
    ./restart-config-nginx.sh || {
        echo -e "${YELLOW}! Nginx restart via script failed, trying direct restart...${NC}"
        docker exec -i nginx-proxy /bin/bash -c "nginx -t && nginx -s reload" || {
            echo -e "${YELLOW}! Nginx reload failed, container may need manual restart${NC}"
        }
    }
    echo -e "${GREEN}✓ Nginx restarted and configuration reloaded${NC}"
else
    echo -e "${YELLOW}! restart-config-nginx.sh not found, using direct reload...${NC}"
    docker exec -i nginx-proxy /bin/bash -c "nginx -t && nginx -s reload" || {
        echo -e "${YELLOW}! Nginx reload failed, container may need manual restart${NC}"
    }
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   All Services Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Network Architecture:${NC}"
echo "  proxy-net (created by nginx):"
echo "    ├─ nginx-proxy"
echo "    ├─ moe-api"
echo "    └─ lean_lsp_mcp_server"
echo ""
echo -e "${BLUE}Access Points:${NC}"
echo "  API:           http://localhost:8154/api/v1"
echo "  Health Check:  http://localhost:8154/api/v1/health"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View containers:   docker ps"
echo "  View API logs:     docker logs moe-api -f"
echo "  View Worker logs:  docker logs moe-worker -f"
echo "  View MCP logs:     docker logs lean_lsp_mcp_server -f"
echo "  Stop services:     cd deployments && ./stop.sh"
echo ""
echo -e "${BLUE}Test the API:${NC}"
echo '  curl http://localhost:8154/api/v1/health'
echo '  curl -H "Authorization: Bearer YOUR_TOKEN" \'
echo '       http://localhost:8154/api/v1/moe/problems/random'
echo ""
