#!/usr/bin/env bash
# Scaffold a fresh project from the template and compile it with a real
# LaTeX toolchain (latexmk, or pdflatex + bibtex). Asserts the log summary
# reports zero undefined citations and that ReferencesStart page counting
# works without manual template edits.
set -euo pipefail
cd "$(dirname "$0")/.."

SKILL=.codex/skills/arxiv-paper-writer
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-compile.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

python3 "$SKILL/scripts/bootstrap_ieee_review_paper.py" \
  --stage kickoff --topic "ci compile smoke" --out "$WORK"
PAPER="$WORK/ci-compile-smoke"

OUT="$WORK/compile-output.txt"
python3 "$SKILL/scripts/compile_paper.py" \
  --project-dir "$PAPER" --report-page-counts | tee "$OUT"

test -f "$PAPER/main.pdf"
grep -q "Undefined citations: 0" "$OUT"
grep -q "References start page (label 'ReferencesStart')" "$OUT"

echo "Compile smoke passed."
