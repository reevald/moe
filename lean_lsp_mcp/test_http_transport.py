#!/usr/bin/env python3
"""Test MCP server HTTP transport."""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_session_endpoint():
    """Test if we can establish a session with the MCP server."""
    print("Testing HTTP transport endpoints...")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Try different endpoint patterns that MCP might use
    endpoints_to_try = [
        "/",
        "/mcp",
        "/session",
        "/v1/session",
        "/api/session",
    ]
    
    for endpoint in endpoints_to_try:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying POST {url}...")
        try:
            response = requests.post(
                url,
                json={},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"  Status: {response.status_code}")
            if response.status_code != 404:
                print(f"  Response: {response.text[:200]}")
                print()
                return url
        except Exception as e:
            print(f"  Error: {e}")
        print()
    
    # Try GET requests
    print("\nTrying GET requests...")
    for endpoint in endpoints_to_try:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying GET {url}...")
        try:
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            if response.status_code != 404:
                print(f"  Response: {response.text[:200]}")
                print()
                return url
        except Exception as e:
            print(f"  Error: {e}")
        print()
    
    return None

def test_mcp_client():
    """Try using the MCP Python client library."""
    print("\nTrying MCP Python client...")
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        
        print("MCP client library is available")
        # This would need async context, skipping for now
        print("(Full client test would require async setup)")
        
    except ImportError as e:
        print(f"MCP client not available in host environment: {e}")
        print("This is expected - the client is in the container")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP HTTP Transport Test")
    print("=" * 60)
    print()
    
    # First check if server is reachable
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"Server is reachable (status: {response.status_code})")
        print()
    except Exception as e:
        print(f"ERROR: Cannot reach server at {BASE_URL}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Test endpoints
    working_endpoint = test_session_endpoint()
    
    if working_endpoint:
        print(f"\nFound working endpoint: {working_endpoint}")
    else:
        print("\nNo working endpoints found.")
        print("\nThe streamable-http transport may require a specific client.")
        print("Let me check the FastMCP documentation pattern...")
    
    # Try to understand what the server expects
    test_mcp_client()
