#!/usr/bin/env python3
"""Compile main.tex for a paper project."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from paper_utils import check_latex_available


def run(cmd: list[str], cwd: Path) -> int:
    result = subprocess.run(cmd, cwd=str(cwd))
    return result.returncode


def parse_total_pages(log_path: Path) -> int | None:
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Output written on .*?\((\d+)\s+pages?", text)
    if not match:
        return None
    return int(match.group(1))


def report_log_summary(project_dir: Path) -> None:
    log_path = project_dir / "main.log"
    if not log_path.exists():
        print("warning: main.log not found; skipping log summary", file=sys.stderr)
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")

    undefined_citations = len(re.findall(r"Citation .*? undefined", text))
    overfull_hboxes = len(re.findall(r"Overfull \\hbox", text))

    print("\nLog summary:")
    print(f"  Undefined citations: {undefined_citations}")
    print(f"  Overfull \\hbox warnings: {overfull_hboxes}")
    if undefined_citations or overfull_hboxes:
        print("  Fix these before marking issues DONE (see Layout Hygiene in SKILL.md).")


def parse_label_page(aux_path: Path, label: str) -> int | None:
    if not aux_path.exists():
        return None
    text = aux_path.read_text(encoding="utf-8", errors="replace")

    def parse_braced_group(content: str, start_idx: int) -> tuple[str, int] | None:
        if start_idx >= len(content) or content[start_idx] != "{":
            return None
        depth = 0
        i = start_idx + 1
        group_start = i
        while i < len(content):
            ch = content[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth == 0:
                    return content[group_start:i], i + 1
                depth -= 1
            i += 1
        return None

    label_prefix = f"\\newlabel{{{label}}}"
    for line in text.splitlines():
        if not line.startswith(label_prefix):
            continue
        brace_start = line.find("{", len(label_prefix))
        if brace_start == -1:
            continue
        outer = parse_braced_group(line, brace_start)
        if outer is None:
            continue
        outer_content, _ = outer

        idx = 0
        first = parse_braced_group(outer_content, idx)
        if first is None:
            continue
        _, idx = first
        while idx < len(outer_content) and outer_content[idx].isspace():
            idx += 1
        second = parse_braced_group(outer_content, idx)
        if second is None:
            continue
        page_str, _ = second
        page_str = page_str.strip()
        if page_str.isdigit():
            return int(page_str)
    return None


def report_page_counts(project_dir: Path, label: str) -> None:
    log_path = project_dir / "main.log"
    aux_path = project_dir / "main.aux"

    total_pages = parse_total_pages(log_path)
    if total_pages is None:
        print("warning: could not read total page count from main.log", file=sys.stderr)
        return

    bib_start_page = parse_label_page(aux_path, label)
    if bib_start_page is None:
        print(
            f"warning: could not find label '{label}' in main.aux; "
            "add a label at bibliography start to enable main-text page counting",
            file=sys.stderr,
        )
        return

    main_text_pages_excl_bib_start = max(bib_start_page - 1, 0)
    reference_pages_incl_bib_start = max(total_pages - main_text_pages_excl_bib_start, 0)

    main_text_pages_incl_bib_start = bib_start_page
    reference_pages_excl_bib_start = max(total_pages - main_text_pages_incl_bib_start, 0)

    print("\nPage count report:")
    print(f"  Total pages (incl. references): {total_pages}")
    print(f"  References start page (label '{label}'): {bib_start_page}")
    print(f"  Main text pages (exclude ref-start page): {main_text_pages_excl_bib_start}")
    print(f"  Reference pages (include ref-start page): {reference_pages_incl_bib_start}")
    print(f"  Main text pages (include ref-start page): {main_text_pages_incl_bib_start}")
    print(f"  Reference pages (exclude ref-start page): {reference_pages_excl_bib_start}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile main.tex (pdflatex/bibtex or latexmk).")
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Project directory containing main.tex and ref.bib.",
    )
    parser.add_argument(
        "--report-page-counts",
        action="store_true",
        help="Print total and main-text page counts (requires a bibliography-start label).",
    )
    parser.add_argument(
        "--references-start-label",
        default="ReferencesStart",
        help="Label name recorded at bibliography start (default: ReferencesStart).",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    tex_path = project_dir / "main.tex"

    if not tex_path.exists():
        print(f"error: main.tex not found in {project_dir}", file=sys.stderr)
        return 1

    latex_info = check_latex_available()
    if not latex_info["available"]:
        print("error: LaTeX tools not available (pdflatex + bibtex required).", file=sys.stderr)
        return 1

    latexmk = latex_info.get("latexmk")
    if latexmk:
        cmd = [
            latexmk,
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "main.tex",
        ]
        code = run(cmd, project_dir)
        if code == 0:
            report_log_summary(project_dir)
            if args.report_page_counts:
                report_page_counts(project_dir, args.references_start_label)
        return code

    # Fallback: pdflatex + bibtex
    steps = [
        [latex_info["pdflatex"], "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        [latex_info["bibtex"], "main"],
        [latex_info["pdflatex"], "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        [latex_info["pdflatex"], "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
    ]

    for cmd in steps:
        code = run(cmd, project_dir)
        if code != 0:
            return code

    report_log_summary(project_dir)
    if args.report_page_counts:
        report_page_counts(project_dir, args.references_start_label)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
