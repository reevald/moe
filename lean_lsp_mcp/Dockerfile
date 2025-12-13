# Use Ubuntu as base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LEAN_PROJECT_PATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    unzip \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Lean 4
RUN curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- --default-toolchain leanprover/lean4:stable -y
ENV PATH="/root/.elan/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY src/ ./src/
COPY pyproject.toml ./
COPY requirements.txt ./
COPY README.md ./
COPY LICENSE ./

# Install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install -e .

# Create a basic lean-toolchain file if it doesn't exist
RUN if [ ! -f lean-toolchain ]; then \
    echo "leanprover/lean4:stable" > lean-toolchain; \
    fi

# Create a basic lakefile.lean if it doesn't exist
RUN if [ ! -f lakefile.lean ]; then \
    echo 'import Lake' > lakefile.lean && \
    echo 'open Lake DSL' >> lakefile.lean && \
    echo '' >> lakefile.lean && \
    echo 'package "lean_lsp_mcp_test" where' >> lakefile.lean && \
    echo '  leanOptions := #[' >> lakefile.lean && \
    echo '    ⟨`pp.unicode.fun, true⟩' >> lakefile.lean && \
    echo '  ]' >> lakefile.lean && \
    echo '' >> lakefile.lean && \
    echo 'require mathlib from git' >> lakefile.lean && \
    echo '  "https://github.com/leanprover-community/mathlib4.git"' >> lakefile.lean && \
    echo '' >> lakefile.lean && \
    echo '@[default_target]' >> lakefile.lean && \
    echo 'lean_lib LeanLspMcpTest where' >> lakefile.lean; \
    fi

# Update lake and get mathlib dependencies
RUN lake update

# Get mathlib cache to speed up builds (this downloads precompiled mathlib)
RUN curl -L https://raw.githubusercontent.com/leanprover-community/mathlib4/master/scripts/get-cache.sh -o get-cache.sh && \
    bash get-cache.sh || echo "Manual cache get failed, trying lake exe cache get..."

RUN lake exe cache get || echo "Lake cache get failed, will build core dependencies..."

# Build core mathlib components that are commonly used
# Note: We build as much as we can without failing the docker build
RUN lake build Mathlib.Tactic.Basic Mathlib.Tactic.Ring Mathlib.Tactic.Linarith Mathlib.Data.Nat.Basic || \
    echo "Some mathlib components had build issues, continuing with partial build..."

# Build Mathlib.Init which is fundamental
RUN lake build Mathlib.Init || echo "Mathlib.Init build had issues..."

# Create test files directory
RUN mkdir -p /app/test_files

# Copy test lean file to test_files directory
COPY src/test.lean /app/test_files/

# Set up PATH for lean commands
ENV PATH="/root/.elan/bin:$PATH"

# Expose port for MCP server
EXPOSE 8000

# Default command
CMD ["python3", "-m", "src.server"]