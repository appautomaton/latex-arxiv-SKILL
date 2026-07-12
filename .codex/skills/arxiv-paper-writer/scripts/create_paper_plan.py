#!/usr/bin/env python3
"""Create a paper plan and/or issues CSV for an IEEE paper project.

This script supports a gated workflow:
  1) Create a draft plan (for user review)
  2) After user confirmation, create the issues CSV (execution contract)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from paper_utils import (
    build_issues_filename,
    build_plan_filename,
    check_latex_available,
    format_yaml_value,
    get_assets_dir,
    now_iso,
    now_timestamp,
    slugify,
    validate_slug,
    validate_timestamp,
)


def read_template(template_name: str) -> str:
    """Read a template file from assets."""
    template_path = get_assets_dir() / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def replace_placeholders(content: str, topic: str, timestamp: str, slug: str, latex_available: bool) -> str:
    """Replace placeholders in template content."""
    content = content.replace("<paper topic>", topic)
    content = content.replace("<topic>", topic)
    content = content.replace("<ISO8601 timestamp>", now_iso())
    content = content.replace("<YYYY-MM-DD_HH-mm-ss>", timestamp)
    content = content.replace("<slug>", slug)
    content = content.replace("<true|false>", "true" if latex_available else "false")
    return content


def kickoff_gate_confirmed(plan_path: Path) -> bool:
    """Return True if the plan indicates the kickoff gate is confirmed."""
    if not plan_path.exists():
        return False
    text = plan_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if re.search(r"^\s*-\s*\[\s*[xX]\s*\]\s*User confirmed scope \+ outline", line):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a paper plan for an IEEE paper project.")
    parser.add_argument("--topic", required=True, help="Paper topic description.")
    parser.add_argument(
        "--stage",
        default="plan",
        choices=["plan", "issues"],
        help="What to create: plan | issues (default: plan).",
    )
    parser.add_argument(
        "--complexity",
        default="medium",
        choices=["simple", "medium", "complex"],
        help="Plan complexity: simple|medium|complex.",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional timestamp override (YYYY-MM-DD_HH-mm-ss). Required for --stage issues.",
    )
    parser.add_argument(
        "--slug",
        help="Optional slug override for filenames (lower-case, hyphen-delimited).",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for plan and issues files (default: current directory).",
    )
    parser.add_argument(
        "--check-latex",
        action="store_true",
        help="Print LaTeX tool availability details (latex_available is always recorded in the plan frontmatter).",
    )
    parser.add_argument(
        "--with-literature-notes",
        action="store_true",
        help="Create notes/literature-notes.md to track paper summaries per citation key.",
    )
    args = parser.parse_args()

    topic = args.topic.strip()
    if not topic:
        print("error: Topic cannot be empty.", file=sys.stderr)
        return 1

    slug = args.slug.strip() if args.slug else slugify(topic)
    try:
        validate_slug(slug)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.timestamp:
        timestamp = args.timestamp.strip()
        try:
            validate_timestamp(timestamp)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    else:
        if args.stage == "issues":
            print("error: --timestamp is required when using --stage issues.", file=sys.stderr)
            return 1
        timestamp = now_timestamp()

    # Check LaTeX availability
    latex_info = check_latex_available()
    latex_available = latex_info["available"]

    if args.check_latex:
        print(f"LaTeX available: {latex_available}")
        if latex_available:
            print(f"  pdflatex: {latex_info['pdflatex']}")
            print(f"  bibtex: {latex_info['bibtex']}")
            if latex_info["latexmk"]:
                print(f"  latexmk: {latex_info['latexmk']}")
            print(f"  Recommended: {latex_info['recommended']}")
        else:
            print("  LaTeX not found. Paper will be created without compilation.")
            print("  User can compile later with Overleaf or local LaTeX installation.")

    # Read and process templates
    try:
        issues_template = read_template("paper-issues-template.csv")
        plan_template = read_template("paper-plan-template.md") if args.stage == "plan" else None
        literature_template = (
            read_template("literature-notes-template.md")
            if args.with_literature_notes and args.stage == "issues"
            else None
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Replace placeholders
    plan_content = (
        replace_placeholders(plan_template, topic, timestamp, slug, latex_available)
        if plan_template
        else None
    )
    issues_content = issues_template  # CSV doesn't need placeholder replacement
    literature_content = (
        replace_placeholders(literature_template, topic, timestamp, slug, latex_available)
        if literature_template
        else None
    )

    # Build output paths
    output_dir = Path(args.output_dir).resolve()
    plan_dir = output_dir / "plan"
    issues_dir = output_dir / "issues"

    plan_filename = build_plan_filename(timestamp, slug)
    issues_filename = build_issues_filename(timestamp, slug)

    plan_path = plan_dir / plan_filename
    issues_path = issues_dir / issues_filename
    literature_dir = output_dir / "notes"
    literature_path = literature_dir / "literature-notes.md"

    # Check for existing / prerequisite files
    if args.stage == "issues" and not plan_path.exists():
        print(
            f"error: Plan not found (create the plan first): {plan_path}",
            file=sys.stderr,
        )
        return 1
    if args.stage == "plan" and plan_path.exists():
        print(f"error: Plan already exists: {plan_path}", file=sys.stderr)
        return 1
    if args.stage == "issues" and issues_path.exists():
        print(f"error: Issues file already exists: {issues_path}", file=sys.stderr)
        return 1
    if literature_content and literature_path.exists():
        print(f"error: Literature notes already exists: {literature_path}", file=sys.stderr)
        return 1
    if args.stage == "issues" and not kickoff_gate_confirmed(plan_path):
        print(
            "error: Kickoff gate is not confirmed in the plan. "
            "Edit the plan and check the box '- [x] User confirmed scope + outline in chat' before creating issues.",
            file=sys.stderr,
        )
        return 1

    # Build frontmatter for plan
    frontmatter = (
        "---\n"
        f"mode: {format_yaml_value('paper-plan')}\n"
        f"topic: {format_yaml_value(topic)}\n"
        f"timestamp: {format_yaml_value(timestamp)}\n"
        f"slug: {format_yaml_value(slug)}\n"
        f"created_at: {format_yaml_value(now_iso())}\n"
        f"complexity: {format_yaml_value(args.complexity)}\n"
        f"latex_available: {str(latex_available).lower()}\n"
        "---\n\n"
    )

    # Remove template frontmatter from plan content
    if plan_content and plan_content.lstrip().startswith("---"):
        # Find the second --- and remove everything before it
        first_dash = plan_content.find("---")
        second_dash = plan_content.find("---", first_dash + 3)
        if second_dash != -1:
            plan_content = plan_content[second_dash + 3:].lstrip()

    # Write files
    if args.stage == "plan":
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(frontmatter + (plan_content or "") + "\n", encoding="utf-8")
        print(f"Created plan: {plan_path}")
    if args.stage == "issues":
        issues_dir.mkdir(parents=True, exist_ok=True)
        issues_path.write_text(issues_content, encoding="utf-8")
        print(f"Created issues: {issues_path}")
    if literature_content:
        literature_dir.mkdir(parents=True, exist_ok=True)
        literature_path.write_text(literature_content.rstrip() + "\n", encoding="utf-8")
        print(f"Created literature notes: {literature_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
