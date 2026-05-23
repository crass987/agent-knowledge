---
name: tdd
description: Test-driven development workflow
---

# TDD Skill

## When to use

- Writing new functions or modules.
- Fixing bugs (write a failing test first that reproduces the bug).
- Refactoring existing code (tests are the safety net).

## Workflow

```
1. RED    — Write a failing test for the desired behavior.
2. GREEN  — Write the minimum code to make the test pass.
3. REFACTOR — Clean up while keeping tests green.
4. REPEAT — Move to the next behavior.
```

## Rules

1. Never write production code except to make a failing test pass.
2. Write the simplest test that could fail. Don't test multiple things at once.
3. Make it work, then make it right, then make it fast.
4. Run all tests after each change. If they're slow, fix the test speed.

## Test structure (Arrange-Act-Assert)

```
def test_user_creation_sets_defaults():
    # Arrange
    data = {"name": "Alice"}

    # Act
    user = User.create(data)

    # Assert
    assert user.role == "member"
    assert user.active is True
```

## Common mistakes

- Testing implementation details instead of behavior.
- Skipping the refactor step.
- Writing too many tests at once before making any pass.
- Not running tests frequently enough.
