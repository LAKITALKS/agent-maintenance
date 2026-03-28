---
name: testing_strategy
description: Pragmatic testing approach — what to test, how much, and in what order
tags: [testing, pytest, quality, tdd]
version: "1.0"
---

# Testing Strategy

## What to test

- **Happy paths** — the core contract of each function.
- **Edge cases** — empty inputs, single items, boundary values.
- **Error paths** — invalid inputs, missing files, API failures.
- **Regression cases** — one test per bug fixed, forever.

## What not to over-test

- Pure language mechanics (stdlib behaviour).
- Private helper functions — test through the public interface.
- Implementation details that change often.

## Test structure (AAA)

```python
def test_select_returns_top_k():
    # Arrange
    skills = [make_skill(f"s{i}") for i in range(10)]
    selector = SkillSelector(top_k=3)

    # Act
    result = selector.select("debug Python code", skills)

    # Assert
    assert len(result) == 3
```

## Pytest tips

- Name tests `test_<what>_<condition>_<expectation>`.
- Use `tmp_path` fixture for filesystem tests — no manual cleanup needed.
- Parametrize with `@pytest.mark.parametrize` instead of loops in tests.
- Use `pytest -x` during development to stop at first failure.

## Coverage target

Aim for high coverage on `core/` and domain logic. Lower expectations for CLI glue code — test that manually.
