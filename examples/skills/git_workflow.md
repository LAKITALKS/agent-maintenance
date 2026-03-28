---
name: git_workflow
description: Branch strategy, commit hygiene, and PR conventions for clean git history
tags: [git, workflow, branching, commits]
version: "1.0"
---

# Git Workflow

## Branch naming

```
feat/<short-description>
fix/<issue-id>-<short-description>
chore/<what>
docs/<what>
```

## Commit messages

Follow Conventional Commits:

```
<type>(<scope>): <short summary>

<optional body — why, not what>
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`

- Keep the summary under 72 characters.
- Write in the imperative mood: "add", not "added" or "adds".
- Reference issues in the body: `Closes #42`

## Pull requests

- One logical change per PR.
- Link the issue in the description.
- Keep diffs under ~400 lines for reviewability.
- Squash commits when merging to keep `main` clean.

## Dangerous operations

Always confirm before:
- `git push --force` (use `--force-with-lease` instead)
- `git reset --hard`
- `git rebase` on a shared branch
