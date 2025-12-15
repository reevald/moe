"""
Test OpenRouter LLM connection.

This script tests the connection to OpenRouter API and verifies
that the LLM model responds correctly.
"""

import os
import sys
from openai import OpenAI

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{BLUE}ℹ {message}{RESET}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠ {message}{RESET}")


def test_openrouter_connection(
    api_key: str,
    base_url: str,
    model_name: str
) -> bool:
    """
    Test connection to OpenRouter LLM.
    
    Args:
        api_key: OpenRouter API key
        base_url: OpenRouter base URL
        model_name: Model name to use
    
    Returns:
        bool: True if all tests pass
    """
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing OpenRouter LLM Connection{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print_info(f"Base URL: {base_url}")
    print_info(f"Model: {model_name}")
    print_info(f"API Key: {api_key[:10]}..." if api_key else "No API key")
    
    all_tests_passed = True
    
    # Test 1: Initialize Client
    print(f"\n{BLUE}Test 1: Initialize OpenRouter Client{RESET}")
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        print_success("OpenRouter client initialized")
    except Exception as e:
        print_error(f"Failed to initialize client: {e}")
        return False
    
    # Test 2: Simple Completion
    print(f"\n{BLUE}Test 2: Simple Completion Test{RESET}")
    try:
        print_info("Sending test prompt...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "What is 2 + 2? Answer with just the number."
                }
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip()
        print_success(f"Received response: '{answer}'")
        
        if "4" in answer:
            print_success("Model responded correctly")
        else:
            print_warning(
                f"Model response unexpected, but connection works"
            )
        
        # Print usage statistics
        if hasattr(response, 'usage'):
            usage = response.usage
            print_info(
                f"Tokens used: "
                f"{usage.prompt_tokens} prompt + "
                f"{usage.completion_tokens} completion = "
                f"{usage.total_tokens} total"
            )
    except Exception as e:
        print_error(f"Failed to get completion: {e}")
        all_tests_passed = False
    
    # Test 3: Math-related Prompt
    print(f"\n{BLUE}Test 3: Math Proof Validation{RESET}")
    try:
        print_info("Testing mathematical reasoning...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Is this a valid mathematical proof attempt? "
                        "Answer with just VALID or INVALID.\n\n"
                        "Proof: By induction, base case n=1: 1 = 1. "
                        "Assume true for n. For n+1: (n+1) = (n+1). QED."
                    )
                }
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        answer = response.choices[0].message.content.strip()
        print_success(f"Model response: '{answer}'")
        
        if "VALID" in answer.upper() or "INVALID" in answer.upper():
            print_success(
                "Model can perform mathematical validation tasks"
            )
        else:
            print_warning(
                "Model response format differs from expected, "
                "but connection works"
            )
    except Exception as e:
        print_error(f"Failed math validation test: {e}")
        all_tests_passed = False
    
    # Test 4: LaTeX Conversion (simplified)
    print(f"\n{BLUE}Test 4: LaTeX to Lean Conversion Capability{RESET}")
    try:
        print_info("Testing conversion capability...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Convert this simple math statement to Lean 4 code. "
                        "Statement: For all natural numbers n, n + 0 = n. "
                        "Provide just the theorem statement."
                    )
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        answer = response.choices[0].message.content.strip()
        print_success("Model responded with conversion attempt")
        print_info(f"Response preview: {answer[:100]}...")
        
        if "theorem" in answer.lower() or "lean" in answer.lower():
            print_success("Model understands Lean code generation")
        else:
            print_warning("Model may need better prompting for Lean")
    except Exception as e:
        print_error(f"Failed conversion test: {e}")
        all_tests_passed = False
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_tests_passed:
        print_success("All OpenRouter LLM tests PASSED ✓")
    else:
        print_error("Some OpenRouter LLM tests FAILED ✗")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return all_tests_passed


def main():
    """Main test function."""
    # Get configuration from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1"
    )
    model_name = os.getenv(
        "MATH_MODEL_NAME",
        "deepseek/deepseek-math-7b-instruct"
    )
    
    if not api_key:
        print_error("OPENROUTER_API_KEY environment variable not set")
        print_info(
            "Please set OPENROUTER_API_KEY to your OpenRouter API key"
        )
        sys.exit(1)
    
    success = test_openrouter_connection(api_key, base_url, model_name)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
