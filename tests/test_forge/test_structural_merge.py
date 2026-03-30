"""Tests for the improved structural merge path in SkillMerger."""

from __future__ import annotations

from agent_maintenance.core.models import Skill, SkillMetadata
from agent_maintenance.forge.merger import (
    SkillMerger,
    _dedup_bullets,
    _merged_description,
    _parse_sections,
    _structural_merge,
)
from agent_maintenance.providers.llm import StubLLMProvider


def make_skill(
    name: str,
    content: str = "",
    tags: list[str] | None = None,
    description: str = "",
) -> Skill:
    return Skill(
        metadata=SkillMetadata(
            name=name,
            description=description or f"About {name}",
            tags=tags or [],
        ),
        content=content or f"# {name}\n\nSome content.",
    )


# ── _parse_sections ────────────────────────────────────────────────────────────

class TestParseSections:
    def test_empty_content_returns_empty_dict(self) -> None:
        assert _parse_sections("") == {}

    def test_no_headings_returns_empty_dict(self) -> None:
        assert _parse_sections("plain content without headings") == {}

    def test_parses_single_section(self) -> None:
        content = "## When to apply\n\nUse this when X."
        sections = _parse_sections(content)
        assert "When to apply" in sections
        assert sections["When to apply"] == "Use this when X."

    def test_parses_multiple_sections(self) -> None:
        content = (
            "## When to apply\n\nCondition A.\n\n"
            "## Core steps\n\n1. Do X.\n2. Do Y.\n\n"
            "## Notes\n\nExtra context."
        )
        sections = _parse_sections(content)
        assert set(sections.keys()) == {"When to apply", "Core steps", "Notes"}
        assert "Condition A" in sections["When to apply"]
        assert "Do X" in sections["Core steps"]

    def test_body_does_not_include_next_heading(self) -> None:
        content = "## Section A\n\nBody A.\n\n## Section B\n\nBody B."
        sections = _parse_sections(content)
        assert "Section B" not in sections["Section A"]
        assert "Body A" not in sections["Section B"]

    def test_ignores_h1_headings(self) -> None:
        content = "# Top level\n\nPreamble.\n\n## Sub section\n\nBody."
        sections = _parse_sections(content)
        assert "Top level" not in sections
        assert "Sub section" in sections


# ── _dedup_bullets ─────────────────────────────────────────────────────────────

class TestDedupBullets:
    def test_empty_blocks(self) -> None:
        assert _dedup_bullets([]) == ""

    def test_single_block_unchanged(self) -> None:
        result = _dedup_bullets(["- item A\n- item B"])
        assert "item A" in result
        assert "item B" in result

    def test_removes_exact_duplicate_lines(self) -> None:
        result = _dedup_bullets(["- item A\n- item B", "- item B\n- item C"])
        lines = [line for line in result.splitlines() if line.strip()]
        # "- item B" should appear exactly once
        assert lines.count("- item B") == 1

    def test_preserves_unique_lines_from_all_blocks(self) -> None:
        result = _dedup_bullets(["- alpha", "- beta", "- gamma"])
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result

    def test_empty_lines_not_included(self) -> None:
        result = _dedup_bullets(["\n- item\n\n"])
        assert "\n\n" not in result or result.strip() == "- item"


# ── _merged_description ────────────────────────────────────────────────────────

class TestMergedDescription:
    def test_includes_source_names(self) -> None:
        skills = [make_skill("alpha"), make_skill("beta")]
        desc = _merged_description(skills)
        assert "alpha" in desc
        assert "beta" in desc

    def test_uses_source_descriptions_when_short(self) -> None:
        skills = [
            make_skill("a", description="Short desc A"),
            make_skill("b", description="Short desc B"),
        ]
        desc = _merged_description(skills)
        assert "Short desc A" in desc
        assert "Short desc B" in desc

    def test_falls_back_to_plain_attribution_when_descriptions_too_long(self) -> None:
        long_desc = "x" * 200
        skills = [make_skill("a", description=long_desc), make_skill("b", description=long_desc)]
        desc = _merged_description(skills)
        # Should not include the 200-char descriptions
        assert "Consolidated from:" in desc

    def test_falls_back_gracefully_with_no_descriptions(self) -> None:
        # Construct Skills directly to ensure descriptions are truly empty
        skills = [
            Skill(metadata=SkillMetadata(name="x", description=""), content=""),
            Skill(metadata=SkillMetadata(name="y", description=""), content=""),
        ]
        desc = _merged_description(skills)
        assert "Consolidated from:" in desc


# ── _structural_merge ──────────────────────────────────────────────────────────

class TestStructuralMerge:
    def test_includes_structural_merge_header(self) -> None:
        skills = [make_skill("a"), make_skill("b")]
        result = _structural_merge(skills)
        assert "Structural merge" in result

    def test_organises_when_to_apply_section(self) -> None:
        skill_a = make_skill("a", content="## When to apply\n\nUse when condition A.")
        skill_b = make_skill("b", content="## When to apply\n\nUse when condition B.")
        result = _structural_merge([skill_a, skill_b])
        assert "## When to apply" in result
        assert "condition A" in result
        assert "condition B" in result

    def test_deduplicates_warnings(self) -> None:
        shared_warning = "- Never do X"
        skill_a = make_skill("a", content=f"## Warnings\n\n{shared_warning}\n- Also avoid Y")
        skill_b = make_skill("b", content=f"## Warnings\n\n{shared_warning}\n- Never do Z")
        result = _structural_merge([skill_a, skill_b])
        # "Never do X" should appear only once in warnings
        assert result.count("Never do X") == 1
        assert "Also avoid Y" in result
        assert "Never do Z" in result

    def test_skills_without_sections_appended_verbatim(self) -> None:
        skill_a = make_skill("a", content="## Core steps\n\n1. Step one.")
        skill_b = make_skill("b", content="Plain content, no headings.")
        result = _structural_merge([skill_a, skill_b])
        assert "Plain content, no headings." in result
        assert "From: `b`" in result

    def test_non_standard_section_preserved_with_attribution(self) -> None:
        skill = make_skill("a", content="## Examples\n\nSome examples here.")
        result = _structural_merge([skill, make_skill("b")])
        assert "Examples" in result
        assert "from `a`" in result

    def test_recognises_alias_section_headings(self) -> None:
        # "Steps" is an alias for "Core steps"
        skill = make_skill("a", content="## Steps\n\n1. Do the thing.")
        result = _structural_merge([skill, make_skill("b")])
        assert "## Core steps" in result

    def test_full_structural_merge_via_merger(self) -> None:
        """Integration: StubLLMProvider → structural merge path."""
        merger = SkillMerger(llm_provider=StubLLMProvider())
        skill_a = make_skill(
            "react_hooks",
            content="## When to apply\n\nUse for state.\n\n## Warnings\n\n- Avoid in classes.",
            tags=["react"],
        )
        skill_b = make_skill(
            "react_effects",
            content=(
                "## When to apply\n\nUse for side-effects.\n\n"
                "## Warnings\n\n- Avoid in classes."
            ),
            tags=["react"],
        )
        result = merger.merge([skill_a, skill_b])
        assert result.raw_frontmatter["merge_method"] == "structural"
        assert "## When to apply" in result.content
        # Deduplicated: "Avoid in classes" appears once
        assert result.content.count("Avoid in classes") == 1
