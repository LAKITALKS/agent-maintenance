---
name: code_review
description: Checklist and principles for constructive, thorough code reviews
tags: [code-review, collaboration, quality, git]
version: "1.0"
---

# Code Review

## What to check

- **Correctness** — does the code do what it claims? Are edge cases handled?
- **Readability** — would a new team member understand this in six months?
- **Test coverage** — are the critical paths tested?
- **Security** — any injection risks, secret leakage, or improper trust boundaries?
- **Performance** — any obvious N+1 queries, unbounded loops, or memory leaks?

## Tone

- Comment on code, not the author.
- Distinguish blockers from suggestions: prefix with `[blocking]` or `[nit]`.
- If something is unclear, ask — don't assume bad intent.

## Scope discipline

- Ignore changes outside the PR diff. File a separate ticket instead.
- If a PR is too large to review in one sitting, ask for a split.

## Quick checklist

- [ ] No credentials or secrets in the diff
- [ ] New public API has at least a docstring
- [ ] Tests added or updated for changed behaviour
- [ ] No dead code introduced
- [ ] Dependencies justified if added
