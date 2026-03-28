---
name: api_design
description: Principles for designing clean, stable, and usable APIs
tags: [api, design, rest, python, interfaces]
version: "1.0"
---

# API Design

## Core principles

1. **Be boring.** Predictable beats clever. Follow conventions your users already know.
2. **Fail loudly.** Raise clear errors early rather than returning ambiguous success.
3. **Minimal surface.** Every public method is a contract. Add only what is necessary.
4. **Names matter.** A well-named function needs no docstring.

## REST conventions

| Method | Semantics | Idempotent? |
|--------|-----------|-------------|
| GET    | Read      | Yes         |
| POST   | Create    | No          |
| PUT    | Replace   | Yes         |
| PATCH  | Update    | No          |
| DELETE | Remove    | Yes         |

- Use nouns for resources, not verbs: `/users/42`, not `/getUser?id=42`.
- Return 422 for validation errors, 409 for conflicts, 404 for not found.
- Version in the path: `/v1/users` — never break existing clients.

## Python library APIs

- Prefer keyword-only arguments for optional parameters.
- Return meaningful types, not raw dicts when the shape is known.
- Keep `__init__` lightweight; defer expensive work to explicit `connect()` / `build()` calls.
