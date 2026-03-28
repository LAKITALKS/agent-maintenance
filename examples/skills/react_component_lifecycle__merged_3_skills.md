---
name: react_component_lifecycle__merged_3_skills
description: 'Consolidated from: react_component_lifecycle, react_useeffect_patterns,
  react_hooks_debugging'
tags:
- react
- hooks
- lifecycle
- useeffect
- cleanup
- frontend
- typescript
- debugging
version: '1.0'
source_skills:
- react_component_lifecycle
- react_useeffect_patterns
- react_hooks_debugging
merged_by: agent-maintenance
merge_method: llm
---

## When to apply

When reasoning about when side effects run in functional React components—managing subscriptions, async operations, timers, and cleanup in relation to renders and unmounts.

## Core steps

1. **Declare all reactive dependencies in the `useEffect` deps array.**
   Every variable from component scope read inside the effect must be listed. This ensures the effect re-runs when those values change and prevents stale closures.

2. **Use mount phase (empty deps `[]`) for one-time setup.**
   Code runs after the first render. Use for initial data fetch, event listener registration, and third-party library initialization.

3. **Use update phase (specific deps) for reactive side effects.**
   List the variables that trigger re-execution (e.g., `[userId]` if the effect depends on userId). The effect runs on mount and whenever a dep changes.

4. **Return a cleanup function to prevent memory leaks.**
   Cleanup runs before the next effect and on unmount. Use it for unsubscribing, clearing timers, and cancelling in-flight requests:
   ```tsx
   useEffect(() => {
     const id = setInterval(tick, 1000);
     return () => clearInterval(id);
   }, [tick]);
   ```

5. **Guard async operations against unmount.**
   Use a cancel flag or `AbortController` to prevent state updates after the component unmounts:
   ```tsx
   useEffect(() => {
     let cancelled = false;
     fetchData().then(data => { if (!cancelled) setData(data); });
     return () => { cancelled = true; };
   }, []);
   ```

6. **Use functional state updates in effects with empty deps.**
   When state depends on its previous value, use `setState(prev => ...)` to avoid adding state as a dependency and causing unnecessary re-runs.

7. **Stabilize object/array literals with `useMemo` or `useCallback`.**
   New `{}` and `[]` on every render break deps tracking. Memoize callbacks and objects before listing them as deps.

8. **Debug with exhaustive-deps linter or React DevTools.**
   Fix all linter warnings; disabling the rule almost always indicates a wrong deps array, not a linting error.

## Warnings / Anti-patterns

- Omitting reactive variables from deps (or disabling `exhaustive-deps`) causes stale closures and state inconsistency.
- Subscriptions without cleanup cause memory leaks and phantom updates on unmounted components.
- Conditional async operations without cancellation guards lead to race conditions.
- Effects with multiple unrelated side effects make dependencies harder to track—split into separate effects.
- Nested or conditional hooks violate the rules of hooks; hooks must run in the same order every render.
- Using effects as a lifecycle replacement (e.g., "run once on mount") instead of syncing with externals leads to missing dependencies.
- Infinite loops: an effect updating state that appears in its own deps. Fix by moving the update into a condition, using a ref, or restructuring the logic.

## Notes

Strict Mode runs effects twice in development to surface missing cleanup. In development, expect: mount → cleanup → mount again. This is intentional and helps catch incomplete cleanup.
