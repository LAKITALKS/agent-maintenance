"""Forge: groups merge candidates into clusters of related skills."""

from __future__ import annotations

from agent_maintenance.core.models import MergeCandidate, Skill


def cluster_merge_candidates(
    skills: list[Skill],
    candidates: list[MergeCandidate],
) -> list[list[Skill]]:
    """Group merge candidates into clusters via connected components (BFS).

    Skills connected by at least one merge candidate end up in the same cluster.
    Skills with no candidates are excluded — nothing to merge.

    Example:
        candidates: A↔B, A↔C  → one cluster: [A, B, C]
        candidates: A↔B, D↔E  → two clusters: [A, B], [D, E]

    Returns:
        List of clusters; each cluster contains 2 or more Skill objects.
    """
    if not candidates:
        return []

    # adjacency: skill name → set of connected skill names
    adjacency: dict[str, set[str]] = {}
    for c in candidates:
        adjacency.setdefault(c.skill_a.name, set()).add(c.skill_b.name)
        adjacency.setdefault(c.skill_b.name, set()).add(c.skill_a.name)

    skill_map: dict[str, Skill] = {s.name: s for s in skills}

    visited: set[str] = set()
    clusters: list[list[Skill]] = []

    for start in adjacency:
        if start in visited:
            continue

        # BFS to collect all connected nodes
        cluster_names: list[str] = []
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            cluster_names.append(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)

        cluster = [skill_map[n] for n in cluster_names if n in skill_map]
        if len(cluster) >= 2:
            clusters.append(cluster)

    return clusters
