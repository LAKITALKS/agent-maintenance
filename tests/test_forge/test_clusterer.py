"""Tests for the merge-candidate clusterer."""


from agent_maintenance.core.models import MergeCandidate, Skill, SkillMetadata
from agent_maintenance.forge.clusterer import cluster_merge_candidates


def make_skill(name: str) -> Skill:
    return Skill(metadata=SkillMetadata(name=name), content=f"Content of {name}")


def make_candidate(a: Skill, b: Skill, score: float = 0.9) -> MergeCandidate:
    return MergeCandidate(skill_a=a, skill_b=b, similarity_score=score)


class TestClusterMergeCandidates:
    def test_empty_candidates_returns_empty(self) -> None:
        skills = [make_skill("a"), make_skill("b")]
        assert cluster_merge_candidates(skills, []) == []

    def test_single_pair_forms_one_cluster(self) -> None:
        a, b = make_skill("a"), make_skill("b")
        candidates = [make_candidate(a, b)]
        clusters = cluster_merge_candidates([a, b], candidates)
        assert len(clusters) == 1
        assert {s.name for s in clusters[0]} == {"a", "b"}

    def test_chain_forms_one_cluster(self) -> None:
        # A↔B and B↔C → one cluster {A, B, C}
        a, b, c = make_skill("a"), make_skill("b"), make_skill("c")
        candidates = [make_candidate(a, b), make_candidate(b, c)]
        clusters = cluster_merge_candidates([a, b, c], candidates)
        assert len(clusters) == 1
        assert {s.name for s in clusters[0]} == {"a", "b", "c"}

    def test_disjoint_pairs_form_separate_clusters(self) -> None:
        a, b = make_skill("a"), make_skill("b")
        c, d = make_skill("c"), make_skill("d")
        candidates = [make_candidate(a, b), make_candidate(c, d)]
        clusters = cluster_merge_candidates([a, b, c, d], candidates)
        assert len(clusters) == 2
        cluster_sets = [{s.name for s in cl} for cl in clusters]
        assert {"a", "b"} in cluster_sets
        assert {"c", "d"} in cluster_sets

    def test_star_topology_forms_one_cluster(self) -> None:
        # A↔B, A↔C, A↔D → one cluster {A, B, C, D}
        a, b, c, d = make_skill("a"), make_skill("b"), make_skill("c"), make_skill("d")
        candidates = [make_candidate(a, b), make_candidate(a, c), make_candidate(a, d)]
        clusters = cluster_merge_candidates([a, b, c, d], candidates)
        assert len(clusters) == 1
        assert {s.name for s in clusters[0]} == {"a", "b", "c", "d"}

    def test_skills_not_in_candidates_are_excluded(self) -> None:
        a, b, lone = make_skill("a"), make_skill("b"), make_skill("lone")
        candidates = [make_candidate(a, b)]
        clusters = cluster_merge_candidates([a, b, lone], candidates)
        all_names = {s.name for cl in clusters for s in cl}
        assert "lone" not in all_names
