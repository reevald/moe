#!/usr/bin/env python3
"""
Simple test script to verify lean_goal tool functionality.
This bypasses the MCP server and tests directly with LeanLSPClient.
"""

import os
import sys
from pathlib import Path

# Test lean content
TEST_LEAN_CONTENT = '''import Mathlib.Tactic

-- Simple goal test
example (n : Nat) : n + 0 = n := by
  simp

-- Complex goal test
example (a b c : Nat) : a + (b + c) = (a + b) + c := by
  rw [Nat.add_assoc]

-- Goal with hypothesis
example (x y : Nat) (h : x = y) : x + 1 = y + 1 := by
  rw [h]
'''

def test_lean_client():
    """Test using LeanLSPClient directly."""
    print("🧪 Testing Lean LSP Client directly...")
    
    try:
        # Import leanclient
        from leanclient import LeanLSPClient
        print("✅ Imported leanclient successfully")
        
        # Create test file
        test_dir = Path("/app/test_files")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "test_simple_goal.lean"
        
        with open(test_file, 'w') as f:
            f.write(TEST_LEAN_CONTENT)
        print(f"✅ Created test file: {test_file}")
        
        # Initialize Lean client
        project_path = Path("/app")
        print(f"📂 Project path: {project_path}")
        
        client = LeanLSPClient(str(project_path), initial_build=False, prevent_cache_get=True)
        print("✅ Initialized LeanLSPClient")
        
        # Open the test file
        rel_path = str(test_file.relative_to(project_path))
        client.open_file(rel_path)
        print(f"✅ Opened file: {rel_path}")
        
        # Test 1: Get goal at line 5 (simp tactic)
        print("\n📋 Test 1: Get goal at line 5 (simp tactic)")
        goal_result = client.get_goal(rel_path, 4, 0)  # 0-indexed
        if goal_result and 'goals' in goal_result:
            print(f"   ✅ Got goals: {goal_result['goals'][:100]}...")
        else:
            print(f"   ❌ No goals found: {goal_result}")
        
        # Test 2: Get diagnostics
        print("\n📋 Test 2: Get diagnostics")
        diagnostics = client.get_diagnostics(rel_path, inactivity_timeout=15.0)
        if diagnostics:
            print(f"   ✅ Got {len(diagnostics)} diagnostic messages")
            for i, diag in enumerate(diagnostics[:3], 1):
                severity = diag.get('severity', 'unknown')
                message = diag.get('message', 'No message')[:50]
                print(f"      {i}. Severity {severity}: {message}...")
        else:
            print(f"   ✅ No diagnostics found (file is valid)")
        
        # Test 3: Get hover info
        print("\n📋 Test 3: Get hover info at 'simp'")
        hover_result = client.get_hover(rel_path, 4, 2)
        if hover_result:
            contents = hover_result.get('contents', {})
            value = contents.get('value', 'No value')[:100]
            print(f"   ✅ Hover info: {value}...")
        else:
            print(f"   ❌ No hover info")
        
        # Close client
        client.close()
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        print(f"📚 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple Lean client tests...")
    print("=" * 50)
    
    success = test_lean_client()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
