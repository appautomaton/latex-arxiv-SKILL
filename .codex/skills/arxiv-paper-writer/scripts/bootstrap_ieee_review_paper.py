#!/usr/bin/env python3
"""Bootstrap an IEEE review paper project (scaffold + plan/issues).

This script exists to make the recommended workflow hard to forget:
1) Kickoff: scaffold + draft plan (for user review)
2) Continue: create issues CSV (execution contract) after user approval
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from paper_utils import get_template_dir, now_timestamp, slugify, validate_slug, validate_timestamp


def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd)
    return proc.returncode


def scaffold_project(topic: str, folder_name: str, out_dir: Path) -> Path:
    dest_dir = out_dir / folder_name
    if dest_dir.exists():
        raise SystemExit(f"Destination already exists: {dest_dir}")

    template_dir = get_template_dir()
    ignore = shutil.ignore_patterns(
        "*.aux",
        "*.bbl",
        "*.blg",
        "*.fdb_latexmk",
        "*.fls",
        "*.lof",
        "*.log",
        "*.lot",
        "*.out",
        "*.synctex",
        "*.synctex.gz",
        "*.toc",
        "main.template.pdf",
    )
    shutil.copytree(template_dir, dest_dir, ignore=ignore)

    main_template = dest_dir / "main.template.tex"
    bib_template = dest_dir / "references.template.bib"
    main_tex = dest_dir / "main.tex"
    ref_bib = dest_dir / "ref.bib"

    if main_template.exists():
        main_template.rename(main_tex)
    if bib_template.exists():
        bib_template.rename(ref_bib)

    if main_tex.exists():
        content = main_tex.read_text(encoding="utf-8")
        content = content.replace("\\bibliography{references}", "\\bibliography{ref}")
        main_tex.write_text(content, encoding="utf-8")

    print(f"Created paper scaffold at: {dest_dir}")
    return dest_dir


def infer_latest_plan_timestamp_and_slug(plan_dir: Path) -> tuple[str, str] | None:
    if not plan_dir.exists():
        return None
    candidates = sorted(p for p in plan_dir.glob("*.md") if p.is_file())
    if not candidates:
        return None
    latest = candidates[-1].name  # lexicographic works for YYYY-MM-DD_HH-mm-ss prefix
    if not latest.endswith(".md"):
        return None
    stem = latest[:-3]
    if len(stem) < 21 or stem[19] != "-":
        return None
    ts = stem[:19]
    slug = stem[20:]
    try:
        validate_timestamp(ts)
        validate_slug(slug)
    except ValueError:
        return None
    return ts, slug


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap an IEEE review paper project (kickoff plan first, then issues)."
    )
    parser.add_argument(
        "--stage",
        default="kickoff",
        choices=["kickoff", "issues"],
        help="kickoff=scaffold+plan; issues=create issues CSV (default: kickoff).",
    )
    parser.add_argument("--topic", required=True, help="Paper topic description.")
    parser.add_argument("--name", help="Folder name override (default: slugified topic).")
    parser.add_argument("--out", default=".", help="Output directory (default: current directory).")
    parser.add_argument(
        "--complexity",
        default="medium",
        choices=["simple", "medium", "complex"],
        help="Plan complexity: simple|medium|complex.",
    )
    parser.add_argument(
        "--timestamp",
        help="Timestamp override (YYYY-MM-DD_HH-mm-ss). Optional for kickoff/all; used for issues stage.",
    )
    parser.add_argument(
        "--slug",
        help="Optional slug override for plan/issues filenames (lower-case, hyphen-delimited).",
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

    out_dir = Path(args.out).resolve()
    folder_name = (args.name or slugify(topic)).strip()
    if not folder_name:
        print("error: Folder name cannot be empty.", file=sys.stderr)
        return 1

    project_dir = out_dir / folder_name
    if args.stage == "issues":
        if not project_dir.exists():
            print(f"error: Project does not exist: {project_dir}", file=sys.stderr)
            return 1
    else:
        if project_dir.exists():
            print(f"error: Destination already exists: {project_dir}", file=sys.stderr)
            return 1

    slug = args.slug.strip() if args.slug else slugify(folder_name)
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
        timestamp = now_timestamp()

    scripts_dir = Path(__file__).resolve().parent
    plan_script = scripts_dir / "create_paper_plan.py"

    if args.stage == "kickoff":
        scaffold_project(topic, folder_name, out_dir)

        plan_cmd = [
            sys.executable,
            str(plan_script),
            "--topic",
            topic,
            "--stage",
            "plan",
            "--complexity",
            args.complexity,
            "--timestamp",
            timestamp,
            "--slug",
            slug,
            "--output-dir",
            str(project_dir),
        ]
        if args.check_latex:
            plan_cmd.append("--check-latex")
        code = run(plan_cmd)
        if code != 0:
            print(
                f"warning: Project scaffold was created but plan generation failed: {project_dir}",
                file=sys.stderr,
            )
            return code

    if args.stage == "issues":
        if not args.timestamp:
            inferred = infer_latest_plan_timestamp_and_slug(project_dir / "plan")
            if inferred is None:
                print(
                    f"error: Could not infer timestamp/slug; pass --timestamp/--slug or create a plan first in: {project_dir / 'plan'}",
                    file=sys.stderr,
                )
                return 1
            timestamp, slug = inferred

        issues_cmd = [
            sys.executable,
            str(plan_script),
            "--topic",
            topic,
            "--stage",
            "issues",
            "--complexity",
            args.complexity,
            "--timestamp",
            timestamp,
            "--slug",
            slug,
            "--output-dir",
            str(project_dir),
        ]
        if args.check_latex:
            issues_cmd.append("--check-latex")
        if args.with_literature_notes:
            issues_cmd.append("--with-literature-notes")
        code = run(issues_cmd)
        if code != 0:
            return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
