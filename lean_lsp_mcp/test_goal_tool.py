#!/usr/bin/env python3
"""
Test script for lean_goal tool functionality.
This script tests the lean_goal tool with various scenarios.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the path for importing modules
sys.path.insert(0, '/app')

from src.server import mcp

# Test file content for goal testing
TEST_LEAN_CONTENT = '''import Mathlib.Tactic

-- Simple goal test
example (n : Nat) : n + 0 = n := by
  simp

-- More complex goal test
example (a b c : Nat) : a + (b + c) = (a + b) + c := by
  rw [Nat.add_assoc]

-- Goal with hypothesis
example (x y : Nat) (h : x = y) : x + 1 = y + 1 := by
  rw [h]

-- Complex goal with multiple steps
example (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  constructor
  · exact h.2
  · exact h.1
'''

class MockContext:
    """Mock context for testing the MCP tools."""
    
    def __init__(self):
        self.request_context = MockRequestContext()
        
    async def report_progress(self, progress: int, total: int, message: str):
        print(f"Progress: {progress}/{total} - {message}")

class MockRequestContext:
    """Mock request context."""
    
    def __init__(self):
        self.lifespan_context = MockLifespanContext()

class MockLifespanContext:
    """Mock lifespan context."""
    
    def __init__(self):
        self.lean_project_path = Path("/app")
        self.client = None
        self.rate_limit = {
            "leansearch": [],
            "loogle": [],
            "leanfinder": [],
            "lean_state_search": [],
            "hammer_premise": [],
        }
        self.lean_search_available = False
        self.loogle_manager = None
        self.loogle_local_available = False

async def test_lean_goal_tool():
    """Test the lean_goal tool with various scenarios."""
    
    print("🧪 Testing lean_goal tool...")
    
    # Create test file
    test_file_path = "/app/test_files/test_goals.lean"
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    
    with open(test_file_path, 'w') as f:
        f.write(TEST_LEAN_CONTENT)
    
    print(f"✅ Created test file: {test_file_path}")
    
    # Create mock context
    ctx = MockContext()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Simple goal at line 4 (simp tactic)",
            "line": 4,
            "column": None,
            "expected_contains": ["⊢", "n + 0 = n"]
        },
        {
            "name": "Goal with specific column at line 5",
            "line": 5,
            "column": 3,
            "expected_contains": ["simp"]
        },
        {
            "name": "Complex goal at line 8 (associativity)",
            "line": 8,
            "column": None,
            "expected_contains": ["⊢", "a + (b + c) = (a + b) + c"]
        },
        {
            "name": "Goal with hypothesis at line 12",
            "line": 12,
            "column": None,
            "expected_contains": ["h : x = y", "⊢", "x + 1 = y + 1"]
        },
        {
            "name": "Goal after intro at line 16",
            "line": 16,
            "column": None,
            "expected_contains": ["intro", "constructor"]
        },
        {
            "name": "Goal after constructor at line 17",
            "line": 17,
            "column": None,
            "expected_contains": ["constructor", "exact"]
        }
    ]
    
    success_count = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{total_tests}: {scenario['name']}")
        
        try:
            # Import the goal function from server
            from src.server import goal
            
            # Call the lean_goal tool
            result = goal(
                ctx=ctx,
                file_path=test_file_path,
                line=scenario["line"],
                column=scenario.get("column")
            )
            
            print(f"   📍 Line: {scenario['line']}, Column: {scenario.get('column', 'None')}")
            print(f"   📝 Line context: {result.line_context}")
            print(f"   🎯 Goals: {result.goals}")
            
            # Check if expected content is present
            goals_str = str(result.goals).lower()
            line_context_str = str(result.line_context).lower()
            combined_str = f"{goals_str} {line_context_str}"
            
            all_found = True
            for expected in scenario.get("expected_contains", []):
                if expected.lower() not in combined_str:
                    print(f"   ❌ Expected '{expected}' not found in result")
                    all_found = False
                else:
                    print(f"   ✅ Found expected content: '{expected}'")
            
            if all_found:
                print(f"   🎉 Test PASSED")
                success_count += 1
            else:
                print(f"   💥 Test FAILED - Missing expected content")
                
        except Exception as e:
            print(f"   💥 Test FAILED with exception: {e}")
            import traceback
            print(f"   📚 Traceback: {traceback.format_exc()}")
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All lean_goal tests passed!")
        return True
    else:
        print("💥 Some lean_goal tests failed!")
        return False

async def main():
    """Main test function."""
    
    print("🚀 Starting lean_goal tool tests...")
    print("=" * 50)
    
    try:
        success = await test_lean_goal_tool()
        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        print(f"📚 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())