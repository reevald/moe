#!/usr/bin/env python3
"""Test MCP server with HTTP/SSE transport using the MCP client library."""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
import sys

async def test_http_sse_transport():
    """Test the MCP server over HTTP with SSE."""
    print("=" * 70)
    print("Testing MCP Server - HTTP SSE Transport")
    print("=" * 70)
    print()
    
    # The server is listening on http://localhost:8000/sse (for SSE transport)
    server_url = "http://localhost:8000/sse"
    
    try:
        async with AsyncExitStack() as stack:
            # Connect to the SSE endpoint
            print(f"Connecting to {server_url}...")
            
            # Create SSE client
            read_stream, write_stream = await stack.enter_async_context(
                sse_client(server_url)
            )
            
            # Create MCP session
            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize the connection
            print("Initializing MCP session...")
            await session.initialize()
            print("✓ Session initialized successfully")
            print()
            
            # List available tools
            print("Listing available tools...")
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"✓ Found {len(tools)} tools:")
            for tool in tools[:10]:  # Show first 10
                desc = (tool.description or "No description")[:60]
                print(f"  - {tool.name}: {desc}...")
            if len(tools) > 10:
                print(f"  ... and {len(tools) - 10} more")
            print()
            
            # Test a simple tool call - file_outline
            print("Testing tool: lean_file_outline")
            test_file = "/workspace/test_goal_example.lean"
            print(f"  File: {test_file}")
            
            try:
                result = await session.call_tool(
                    "lean_file_outline",
                    arguments={"file_path": test_file}
                )
                
                print(f"✓ Tool call successful")
                print(f"  Result: {str(result)[:200]}...")
                print()
            except Exception as e:
                print(f"✗ Tool call failed: {e}")
                print()
            
            # Test goal tool
            print("Testing tool: lean_goal")
            try:
                result = await session.call_tool(
                    "lean_goal",
                    arguments={
                        "file_path": test_file,
                        "line": 5,
                    }
                )
                
                print(f"✓ Goal tool successful")
                print(f"  Result: {str(result)[:200]}...")
                print()
            except Exception as e:
                print(f"✗ Goal tool failed: {e}")
                print()
            
            print("=" * 70)
            print("All tests completed!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_http_sse_transport())
