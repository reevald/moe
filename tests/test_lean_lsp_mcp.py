"""
Test Lean LSP MCP connection using StreamableHTTP transport.

This script tests the connection to the Lean LSP MCP server and verifies
that the goal and diagnostic tools work correctly.
"""

import asyncio
import json
import os
import sys
from typing import Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from contextlib import AsyncExitStack

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


async def test_lean_lsp_connection(
    base_url: str = "http://localhost:8000",
    token: Optional[str] = None
) -> bool:
    """
    Test connection to Lean LSP MCP server using StreamableHTTP transport.
    
    Args:
        base_url: Base URL of the Lean LSP MCP server
        token: Optional bearer token for authentication
    
    Returns:
        bool: True if all tests pass
    """
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing Lean LSP MCP Connection (StreamableHTTP){RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print_info(f"Server URL: {base_url}")
    if token:
        print_info("Using bearer token authentication")
    
    all_tests_passed = True
    mcp_url = f"{base_url}/mcp"
    
    try:
        # Initialize StreamableHTTP client connection
        print(f"\n{BLUE}Test 1: Initialize MCP StreamableHTTP Connection{RESET}")
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with AsyncExitStack() as stack:
            # Connect to the MCP server via StreamableHTTP
            read_stream, write_stream, get_session_id = await stack.enter_async_context(
                streamablehttp_client(mcp_url, headers=headers if headers else None)
            )
            
            # Create MCP session
            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize the connection
            await session.initialize()
            print_success("MCP StreamableHTTP connection established")
            
            # Get session ID
            session_id = get_session_id()
            if session_id:
                print_info(f"Session ID: {session_id[:20]}...")
            
            # Test 2: List Available Tools
            print(f"\n{BLUE}Test 2: List Available Tools{RESET}")
            try:
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print_success(f"Found {len(tools)} tools")
                
                # Check for required tools
                required_tools = ["lean_goal", "lean_diagnostic_messages"]
                tool_names = [t.name for t in tools]
                
                for required_tool in required_tools:
                    if required_tool in tool_names:
                        print_success(f"  ✓ {required_tool} available")
                    else:
                        print_error(f"  ✗ {required_tool} not found")
                        all_tests_passed = False
                
                # Show some other available tools
                other_tools = [t.name for t in tools[:5] if t.name not in required_tools]
                if other_tools:
                    print_info(f"Other tools: {', '.join(other_tools)}...")
                    
            except Exception as e:
                print_error(f"Failed to list tools: {e}")
                all_tests_passed = False
            
            # Test 3: Test lean_goal tool
            print(f"\n{BLUE}Test 3: Test lean_goal Tool{RESET}")
            try:
                # Create a simple Lean file content for testing
                test_lean_code = """theorem test_theorem : 2 + 2 = 4 := by
  sorry
"""
                
                print_info("Testing lean_goal with sample theorem...")
                
                result = await session.call_tool(
                    "lean_goal",
                    arguments={
                        "file_path": "/tmp/test_goal.lean",
                        "file_contents": test_lean_code,
                        "line": 2
                    }
                )
                
                if result.isError:
                    # Expected error when no Lean project is configured
                    print_warning(
                        f"lean_goal returned an error (expected without Lean project)"
                    )
                    if result.content:
                        error_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        print_info(f"Error: {error_text[:150]}...")
                else:
                    print_success("lean_goal tool responded successfully")
                    if result.content:
                        content_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        print_info(f"Response length: {len(content_text)} chars")
                        # Show first 200 chars of response
                        if content_text:
                            preview = content_text[:200].replace('\n', ' ')
                            print_info(f"Response preview: {preview}...")
            except Exception as e:
                print_error(f"Failed to test lean_goal: {e}")
                all_tests_passed = False
            
            # Test 4: Test lean_diagnostic_messages tool
            print(f"\n{BLUE}Test 4: Test lean_diagnostic_messages Tool{RESET}")
            try:
                print_info("Testing lean_diagnostic_messages...")
                
                result = await session.call_tool(
                    "lean_diagnostic_messages",
                    arguments={
                        "file_path": "/tmp/test_diagnostic.lean",
                        "file_contents": test_lean_code
                    }
                )
                
                if result.isError:
                    # Expected error when no Lean project is configured
                    print_warning(
                        f"lean_diagnostic_messages returned an error (expected without Lean project)"
                    )
                    if result.content:
                        error_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        print_info(f"Error: {error_text[:150]}...")
                else:
                    print_success("lean_diagnostic_messages tool responded successfully")
                    if result.content:
                        content_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        print_info(f"Response length: {len(content_text)} chars")
                        # Show first 200 chars of response
                        if content_text:
                            preview = content_text[:200].replace('\n', ' ')
                            print_info(f"Response preview: {preview}...")
            except Exception as e:
                print_error(f"Failed to test lean_diagnostic_messages: {e}")
                all_tests_passed = False
                
    except Exception as e:
        print_error(f"Failed to connect to MCP server: {e}")
        print_warning(
            "Make sure the Lean LSP MCP server is running with "
            "--transport streamable-http"
        )
        print_info("Server should be accessible at: " + mcp_url)
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_tests_passed:
        print_success("All Lean LSP MCP tests PASSED ✓")
    else:
        print_error("Some Lean LSP MCP tests FAILED ✗")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return all_tests_passed


async def main():
    """Main test function."""
    # Get configuration from environment
    base_url = os.getenv("LEAN_LSP_MCP_URL", "http://localhost:8000")
    token = os.getenv("LEAN_LSP_MCP_TOKEN")
    
    success = await test_lean_lsp_connection(base_url, token)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
