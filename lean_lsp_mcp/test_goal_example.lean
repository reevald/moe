import Mathlib.Tactic

-- Test file for lean_goal tool
-- This file contains examples with various proof states

example (n : Nat) : n + 0 = n := by
  -- Goal: ⊢ n + 0 = n
  simp

example (a b c : Nat) : a + (b + c) = (a + b) + c := by
  -- Goal: ⊢ a + (b + c) = (a + b) + c
  rw [Nat.add_assoc]

-- Example with multiple tactics
example (x y : Nat) (h : x = y) : x + 1 = y + 1 := by
  -- Goal: ⊢ x + 1 = y + 1
  rw [h]
  -- Goal should be: no goals (proof complete)

-- Example with complex goal state
example (P Q : Prop) : P ∧ Q → Q ∧ P := by
  -- Goal: ⊢ P ∧ Q → Q ∧ P
  intro h
  -- Goal: h : P ∧ Q ⊢ Q ∧ P
  constructor
  -- Goal 1: h : P ∧ Q ⊢ Q
  -- Goal 2: h : P ∧ Q ⊢ P
  · exact h.2
  · exact h.1

-- Example with type goal
def test_function : Nat → Nat := by
  -- Type goal should show: ⊢ Nat → Nat
  intro n
  -- Should show: ⊢ Nat
  exact n + 1

-- Example that will have errors (for diagnostic testing)
example (n : Nat) : n + 1 = n := by
  -- This should produce a diagnostic error
  sorry  -- Remove this sorry to see the actual error