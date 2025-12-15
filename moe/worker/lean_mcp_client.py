"""
MCP client for Lean LSP validation.

This module provides a synchronous wrapper around the async MCP client
for validating Lean code via the Lean LSP MCP server.
"""

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


async def validate_lean_code_async(mcp_url: str, lean_code: str) -> dict[str, Any]:
    """
    Validate Lean code using the MCP server asynchronously.
    
    Args:
        mcp_url: Base URL of the MCP server (e.g., http://localhost:8000)
        lean_code: Lean code to validate
        
    Returns:
        dict: Validation result with keys:
            - is_valid: bool
            - status: str
            - errors: list
            - remaining_goals: list
    """
    # The streamable HTTP endpoint for FastMCP is at /mcp
    mcp_endpoint = f"{mcp_url}/mcp"
    
    try:
        async with AsyncExitStack() as stack:
            # Connect to the streamable HTTP endpoint
            logger.debug(f"Connecting to MCP server at {mcp_endpoint}")
            read_stream, write_stream, get_session_id = await stack.enter_async_context(
                streamablehttp_client(mcp_endpoint)
            )
            
            # Create MCP session
            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize the connection
            logger.debug("Initializing MCP session")
            await session.initialize()
            logger.debug("MCP session initialized successfully")
            
            # Call the lean_run_code tool
            logger.debug("Calling lean_run_code tool")
            result = await session.call_tool(
                "lean_run_code",
                arguments={"code": lean_code}
            )
            
            logger.debug(f"MCP tool result: {result}")
            
            # Parse the result
            # The result should have a 'content' field with a list of content items
            if hasattr(result, 'content') and result.content:
                # Get the first text content item
                for item in result.content:
                    if hasattr(item, 'type') and item.type == 'text':
                        # Parse the JSON result
                        run_result = json.loads(item.text)
                        
                        success = run_result.get("success", False)
                        diagnostics = run_result.get("diagnostics", [])
                        
                        # Filter errors from diagnostics
                        errors = [
                            {
                                "message": diag.get("message", ""),
                                "line": diag.get("line"),
                                "column": diag.get("column"),
                                "severity": diag.get("severity", "error")
                            }
                            for diag in diagnostics
                            if diag.get("severity") == "error"
                        ]
                        
                        # Get remaining goals if any
                        remaining_goals = []
                        for diag in diagnostics:
                            msg = diag.get("message", "")
                            if "unsolved goals" in msg.lower() or "goals remaining" in msg.lower():
                                remaining_goals.append(msg)
                        
                        is_valid = success and len(errors) == 0
                        status = "success" if is_valid else "failed"
                        
                        logger.info(
                            f"Validation result: is_valid={is_valid}, "
                            f"errors={len(errors)}, remaining_goals={len(remaining_goals)}"
                        )
                        
                        return {
                            "is_valid": is_valid,
                            "status": status,
                            "errors": errors,
                            "remaining_goals": remaining_goals
                        }
                
                # If we get here, no text content was found
                logger.error("No text content in MCP result")
                return {
                    "is_valid": False,
                    "status": "error",
                    "errors": [{"message": "Invalid response format from MCP server"}],
                    "remaining_goals": []
                }
            else:
                logger.error("Invalid MCP result structure")
                return {
                    "is_valid": False,
                    "status": "error",
                    "errors": [{"message": "Invalid response structure from MCP server"}],
                    "remaining_goals": []
                }
                
    except Exception as e:
        logger.error(f"Error validating Lean code via MCP: {e}", exc_info=True)
        return {
            "is_valid": False,
            "status": "error",
            "errors": [{"message": f"MCP validation error: {str(e)}"}],
            "remaining_goals": []
        }


def validate_lean_code(mcp_url: str, lean_code: str) -> dict[str, Any]:
    """
    Synchronous wrapper for validate_lean_code_async.
    
    This function creates an event loop and runs the async validation.
    Safe to call from synchronous contexts like Celery tasks.
    
    Args:
        mcp_url: Base URL of the MCP server
        lean_code: Lean code to validate
        
    Returns:
        dict: Validation result
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new loop
            # This can happen in some Celery configurations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(validate_lean_code_async(mcp_url, lean_code))
            finally:
                loop.close()
        else:
            return loop.run_until_complete(validate_lean_code_async(mcp_url, lean_code))
    except RuntimeError:
        # No event loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(validate_lean_code_async(mcp_url, lean_code))
        finally:
            loop.close()
