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

# Create a basic lakefile.lean if it doesn't exist
# Note: lean-toolchain will be created automatically by 'lake update' based on mathlib's requirements
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

# CRITICAL: Pre-download mathlib cache to avoid 10-15 min delays on first request
# This downloads precompiled mathlib binaries (~6 GB, 7726 files) during build time
# Without this, every container restart requires a fresh download
# Lake downloads cache to BOTH /app/.lake/packages/mathlib/.lake/build AND /root/.cache/mathlib
RUN echo "=== Step 1: Downloading and extracting mathlib cache (10-15 minutes) ===" && \
    echo "This downloads .ltar archives and extracts them to .olean files..." && \
    timeout 1200 lake exe cache get && \
    echo "" && \
    echo "Cache statistics after first extraction:" && \
    echo "  - Project build directory:" && \
    du -sh /app/.lake/packages/mathlib/.lake/build && \
    echo "  - User cache directory (.ltar files):" && \
    du -sh /root/.cache/mathlib && \
    echo "  - Extracted .olean files:" && \
    find /app/.lake/packages/mathlib/.lake/build -name "*.olean" 2>/dev/null | wc -l && \
    echo "" && \
    echo "=== Step 2: Running cache get again to ensure everything is extracted ===" && \
    echo "If this completes quickly (<30s), the cache is fully prepared." && \
    echo "If it takes minutes, leantar is still extracting remaining archives..." && \
    timeout 900 lake exe cache get && \
    echo "✓ Mathlib cache fully prepared and verified!"

# CRITICAL FIX: Patch mathlib's lakefile to disable post_update hook
# The post_update hook runs "lake exe cache get" every time a package loads,
# causing 3-5 minute delays on EVERY validation. We already have the cache,
# so we patch the lakefile to skip this automatic cache check.
RUN echo "=== Patching mathlib lakefile to disable automatic cache updates ===" && \
    cd /app/.lake/packages/mathlib && \
    cp lakefile.lean lakefile.lean.original && \
    sed -i 's/post_update pkg do/post_update pkg do\n  return -- PATCHED: Skip cache get to avoid runtime delays/' lakefile.lean && \
    echo "✓ Mathlib lakefile patched successfully" && \
    echo "  Post-update hook will now return immediately without running cache get"

# Create test files directory
RUN mkdir -p /app/test_files

# Copy test lean file to test_files directory
COPY src/test.lean /app/test_files/

# NOTE: Cache validation skipped - the mathlib cache is pre-downloaded above
# and will be used by the LSP server at runtime. The cache is located at:
# /app/.lake/packages/mathlib/.lake/build (~6GB)

# Set up PATH for lean commands
ENV PATH="/root/.elan/bin:$PATH"

# CRITICAL: Disable Lake cache downloads since we already have the cache pre-downloaded
# This prevents Lake from running 'cache get' on every validation request
# The cache is already present in /app/.lake/packages/mathlib/.lake/build and /root/.cache/mathlib
ENV LAKE_NO_CACHE=true
# Disable mathlib's post_update hook that automatically runs cache get
ENV MATHLIB_NO_CACHE_ON_UPDATE=1

# Expose port for MCP server
EXPOSE 8000

# Default command
CMD ["python3", "-m", "src.server"]