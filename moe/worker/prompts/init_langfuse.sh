#!/bin/bash
# Langfuse Prompt Initialization Script
# This script initializes prompts in Langfuse from init_prompts.yml
#
# Requirements:
# - LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL must be set
# - Python 3.9+ with langfuse, pyyaml, requests installed
#
# Usage: ./init_langfuse.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_FILE="$SCRIPT_DIR/init_prompts.yml"

echo -e "${GREEN}=== Langfuse Prompt Initialization ===${NC}"

# Check required environment variables
if [ -z "$LANGFUSE_SECRET_KEY" ] || [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_BASE_URL" ]; then
    echo -e "${RED}Error: Required environment variables not set${NC}"
    echo "Please set: LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL"
    exit 1
fi

# Check if prompts file exists
if [ ! -f "$PROMPTS_FILE" ]; then
    echo -e "${RED}Error: Prompts file not found: $PROMPTS_FILE${NC}"
    exit 1
fi

echo "Langfuse URL: $LANGFUSE_BASE_URL"
echo "Prompts file: $PROMPTS_FILE"

# Create Python script to handle Langfuse operations
python3 - <<'PYTHON_SCRIPT'
import os
import sys
import yaml
import json
from langfuse import Langfuse

# Load environment variables
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")
SCRIPT_DIR = os.getenv("SCRIPT_DIR")

# Initialize Langfuse client
try:
    langfuse = Langfuse(
        secret_key=LANGFUSE_SECRET_KEY,
        public_key=LANGFUSE_PUBLIC_KEY,
        host=LANGFUSE_BASE_URL
    )
    print("✓ Connected to Langfuse")
except Exception as e:
    print(f"✗ Failed to connect to Langfuse: {e}")
    sys.exit(1)

# Load prompts from YAML
prompts_file = os.path.join(SCRIPT_DIR, "init_prompts.yml")
try:
    with open(prompts_file, 'r') as f:
        config = yaml.safe_load(f)
        prompts = config.get('prompts', [])
    print(f"✓ Loaded {len(prompts)} prompt(s) from configuration")
except Exception as e:
    print(f"✗ Failed to load prompts file: {e}")
    sys.exit(1)

# Check if prompts already exist in Langfuse
def check_existing_prompts():
    """Check if any prompts exist in Langfuse."""
    try:
        # Try to get a prompt to check if any exist
        # Langfuse API will return empty or error if no prompts exist
        # This is a simple check - in fresh install, this should be empty
        print("Checking for existing prompts in Langfuse...")
        
        # Check each prompt from our config
        existing_count = 0
        for prompt_config in prompts:
            prompt_name = prompt_config.get('name')
            try:
                # Try to get the prompt - if it exists, it will return data
                prompt = langfuse.get_prompt(prompt_name)
                if prompt:
                    existing_count += 1
                    print(f"  - Found existing prompt: {prompt_name}")
            except:
                # Prompt doesn't exist
                pass
        
        return existing_count
    except Exception as e:
        # If there's an error, assume no prompts exist (fresh install)
        print(f"  Note: {str(e)}")
        return 0

# Check for existing prompts
existing_prompts = check_existing_prompts()

if existing_prompts > 0:
    print(f"\n⚠ Found {existing_prompts} existing prompt(s) in Langfuse")
    print("Prompts already initialized. Skipping initialization.")
    print("To re-initialize, please delete prompts from Langfuse dashboard first.")
    sys.exit(0)

print("\n✓ No existing prompts found - proceeding with initialization")

# Initialize each prompt
success_count = 0
failed_count = 0

for prompt_config in prompts:
    prompt_name = prompt_config.get('name')
    description = prompt_config.get('description', '')
    template = prompt_config.get('template', '')
    config = prompt_config.get('config', {})
    labels = prompt_config.get('labels', [])
    
    print(f"\nInitializing prompt: {prompt_name}")
    print(f"  Description: {description}")
    
    try:
        # Create prompt in Langfuse
        langfuse.create_prompt(
            name=prompt_name,
            prompt=template,
            labels=labels,
            config=config
        )
        print(f"  ✓ Successfully created prompt: {prompt_name}")
        success_count += 1
    except Exception as e:
        print(f"  ✗ Failed to create prompt {prompt_name}: {e}")
        failed_count += 1

# Flush Langfuse client to ensure all data is sent
langfuse.flush()

# Summary
print(f"\n{'='*50}")
print(f"Initialization Summary:")
print(f"  Successful: {success_count}")
print(f"  Failed: {failed_count}")
print(f"{'='*50}")

if failed_count > 0:
    sys.exit(1)
else:
    print("\n✓ All prompts initialized successfully!")
    sys.exit(0)
PYTHON_SCRIPT

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "\n${GREEN}=== Initialization Complete ===${NC}"
else
    echo -e "\n${RED}=== Initialization Failed ===${NC}"
    exit 1
fi
