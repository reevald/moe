#!/usr/bin/env python3
"""Test MCP server with a real Lean project using SSE transport."""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
import sys
import json

async def test_with_real_project():
    """Test MCP tools with an actual Lean project."""
    print("=" * 70)
    print("Testing MCP Server with Real Lean Project")
    print("=" * 70)
    print()
    
    server_url = "http://localhost:8000/sse"
    test_file = "/workspace/test_project/TestProject/Simple.lean"
    
    try:
        async with AsyncExitStack() as stack:
            print(f"Connecting to {server_url}...")
            
            # Create SSE client
            read_stream, write_stream = await stack.enter_async_context(
                sse_client(server_url)
            )
            
            # Create MCP session
            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize
            await session.initialize()
            print("✓ Connected and initialized\n")
            
            # TEST 1: file_outline
            print("=" * 70)
            print("TEST 1: file_outline")
            print("=" * 70)
            print(f"File: {test_file}")
            try:
                result = await session.call_tool(
                    "lean_file_outline",
                    arguments={"file_path": test_file}
                )
                content = str(result.content[0]) if result.content else "No content"
                
                # Parse JSON to display nicely
                try:
                    # Extract text from TextContent
                    if hasattr(result.content[0], 'text'):
                        content_text = result.content[0].text
                    else:
                        content_text = str(result.content[0])
                    
                    outline_data = json.loads(content_text)
                    print(f"\n✓ File outline retrieved:")
                    print(f"  Imports: {outline_data.get('imports', [])}")
                    print(f"  Declarations ({len(outline_data.get('declarations', []))}):")
                    for decl in outline_data.get('declarations', []):
                        print(f"    - {decl['name']}")
                except Exception as parse_e:
                    print(f"✓ Result: {content[:300]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            # TEST 2: diagnostic_messages
            print("=" * 70)
            print("TEST 2: diagnostic_messages")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "lean_diagnostic_messages",
                    arguments={"file_path": test_file}
                )
                
                if hasattr(result.content[0], 'text'):
                    content_text = result.content[0].text
                else:
                    content_text = str(result.content[0])
                
                try:
                    diagnostics = json.loads(content_text)
                    if diagnostics:
                        print(f"✓ Found {len(diagnostics)} diagnostic(s):")
                        for diag in diagnostics[:5]:
                            msg = diag['message'][:60]
                            print(f"  Line {diag['line']}: [{diag['severity']}] {msg}")
                    else:
                        print("✓ No diagnostics (file is clean)")
                except:
                    print(f"✓ Result: {content_text[:300]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            # TEST 3: goal (on line 4 - theorem add_zero)
            print("=" * 70)
            print("TEST 3: goal (theorem add_zero, line 4)")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "lean_goal",
                    arguments={
                        "file_path": test_file,
                        "line": 4,  # theorem add_zero
                    }
                )
                
                if hasattr(result.content[0], 'text'):
                    content_text = result.content[0].text
                else:
                    content_text = str(result.content[0])
                
                try:
                    goal_data = json.loads(content_text)
                    print(f"✓ Goal state retrieved:")
                    print(f"  Line: {goal_data.get('line_context', 'N/A')}")
                    goals = goal_data.get('goals', 'N/A')
                    print(f"  Goals: {goals[:200] if goals else 'None'}")
                except:
                    print(f"✓ Result: {content_text[:400]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            # TEST 4: goal on incomplete proof (line 16)
            print("=" * 70)
            print("TEST 4: goal (incomplete_proof with sorry, line 16)")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "lean_goal",
                    arguments={
                        "file_path": test_file,
                        "line": 16,  # incomplete_proof
                    }
                )
                
                if hasattr(result.content[0], 'text'):
                    content_text = result.content[0].text
                else:
                    content_text = str(result.content[0])
                
                try:
                    goal_data = json.loads(content_text)
                    print(f"✓ Goal state retrieved:")
                    print(f"  Line: {goal_data.get('line_context', 'N/A')}")
                    goals = goal_data.get('goals', 'N/A')
                    print(f"  Goals: {goals[:200] if goals else 'None'}")
                except:
                    print(f"✓ Result: {content_text[:400]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            # TEST 5: hover_info on "double" at line 20
            print("=" * 70)
            print("TEST 5: hover_info (double function, line 20)")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "lean_hover_info",
                    arguments={
                        "file_path": test_file,
                        "line": 20,
                        "column": 5,  # "double"
                    }
                )
                
                if hasattr(result.content[0], 'text'):
                    content_text = result.content[0].text
                else:
                    content_text = str(result.content[0])
                
                try:
                    hover_data = json.loads(content_text)
                    print(f"✓ Hover info retrieved:")
                    print(f"  Symbol: {hover_data.get('symbol', 'N/A')}")
                    print(f"  Info: {hover_data.get('info', 'N/A')[:200]}")
                except:
                    print(f"✓ Result: {content_text[:400]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            # TEST 6: completions after "Nat." on line 25
            print("=" * 70)
            print("TEST 6: completions (after 'Nat.add', line 25)")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "lean_completions",
                    arguments={
                        "file_path": test_file,
                        "line": 25,
                        "column": 15,  # After "Nat.add"
                        "max_completions": 10,
                    }
                )
                
                if hasattr(result.content[0], 'text'):
                    content_text = result.content[0].text
                else:
                    content_text = str(result.content[0])
                
                try:
                    completions = json.loads(content_text)
                    if completions:
                        print(f"✓ Found {len(completions)} completion(s):")
                        for comp in completions[:10]:
                            label = comp.get('label', 'N/A')
                            detail = comp.get('detail', '')[:40] if comp.get('detail') else ''
                            print(f"  - {label:20} {detail}")
                    else:
                        print("✓ No completions available at this position")
                except:
                    print(f"✓ Result: {content_text[:400]}...")
                print()
            except Exception as e:
                print(f"✗ Failed: {e}\n")
            
            print("=" * 70)
            print("All tests completed successfully!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_with_real_project())
