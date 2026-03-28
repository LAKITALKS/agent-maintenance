---
name: python_debugging
description: Structured approach to debugging Python code efficiently
tags: [python, debugging, testing, logging]
version: "1.0"
---

# Python Debugging

## Approach

1. **Reproduce first.** Write a minimal failing test before touching code.
2. **Read the traceback bottom-up.** The last frame is usually where the error lives.
3. **Use `breakpoint()`.** Drop `breakpoint()` at the suspected location; use `p`, `n`, `s` in pdb.
4. **Check assumptions with assertions.** Temporarily add `assert` statements to narrow the search.
5. **Bisect.** Comment out half the suspect code to isolate the cause quickly.

## Logging over print

Prefer `logging` over `print` for anything beyond a one-off session:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("value=%s", value)
```

## Common traps

- Mutable default arguments: `def f(items=[])` — use `None` sentinel instead.
- Off-by-one in slices: `a[1:n]` excludes index `n`.
- Late-binding closures in loops — capture the variable explicitly.
