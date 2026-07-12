#!/usr/bin/env bash
# Harness smoke checks that need no LaTeX toolchain.
# Covers script syntax, CSV validation, the plan-approval gate, and log parsing.
set -euo pipefail
cd "$(dirname "$0")/.."

SKILL=.codex/skills/arxiv-paper-writer
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-smoke.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export PYTHONPYCACHEPREFIX="$WORK/pycache"

echo "== 1. Script syntax =="
python3 -m py_compile "$SKILL"/scripts/*.py
echo "ok"

echo "== 2. Validator passes both example CSVs with no warnings =="
for csv in \
  "example/v0-single-SKILL/issues/2025-12-27_12-43-32-generative-image-models-review.csv" \
  "example/v0.5-sqlite-multi-SKILLs/video-world-simulators-3d4d-review/issues/2025-12-28_20-29-21-video-world-simulators-3d4d-review.csv"; do
  err="$(python3 "$SKILL/scripts/validate_paper_issues.py" "$csv" 2>&1 >/dev/null)"
  if [[ "$err" == *warning* ]]; then
    echo "FAIL: unexpected warnings for $csv:" >&2
    echo "$err" >&2
    exit 1
  fi
done
echo "ok"

echo "== 3. Validator flags a DONE writing row below target; --strict fails =="
cat > "$WORK/bad-issues.csv" <<'CSV'
ID,Phase,Title,Description,Target_Citations,Visualization,Acceptance,Status,Verified_Citations,Notes
W1,Writing,Test section,Write it,10,N/A,Done when cited,DONE,4,short
CSV
if python3 "$SKILL/scripts/validate_paper_issues.py" "$WORK/bad-issues.csv" --strict 2>/dev/null; then
  echo "FAIL: --strict should exit nonzero on warnings" >&2
  exit 1
fi
python3 "$SKILL/scripts/validate_paper_issues.py" "$WORK/bad-issues.csv" >/dev/null 2>&1
echo "ok"

echo "== 4. Scaffold round-trip honors the plan-approval gate =="
python3 "$SKILL/scripts/bootstrap_ieee_review_paper.py" \
  --stage kickoff --topic "smoke test topic" --out "$WORK" >/dev/null
PAPER="$WORK/smoke-test-topic"
if python3 "$SKILL/scripts/bootstrap_ieee_review_paper.py" \
  --stage issues --topic "smoke test topic" --out "$WORK" 2>/dev/null; then
  echo "FAIL: issues stage should refuse before the gate is checked" >&2
  exit 1
fi
python3 - "$PAPER"/plan/*.md <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_text(p.read_text().replace(
    "- [ ] User confirmed scope + outline in chat",
    "- [x] User confirmed scope + outline in chat"))
PY
python3 "$SKILL/scripts/bootstrap_ieee_review_paper.py" \
  --stage issues --topic "smoke test topic" --out "$WORK" --with-literature-notes >/dev/null
python3 "$SKILL/scripts/validate_paper_issues.py" "$PAPER"/issues/*.csv >/dev/null 2>&1
grep -q "ReferencesStart" "$PAPER/main.tex"
echo "ok"

echo "== 5. Log summary and page-count parsing (fixtures) =="
cat > "$WORK/main.log" <<'LOG'
LaTeX Warning: Citation `author2023paper' on page 1 undefined on input line 128.
Overfull \hbox (12.3pt too wide) in paragraph at lines 45--47
LaTeX Warning: Citation `smith2022deep' on page 2 undefined on input line 139.
Overfull \hbox (3.1pt too wide) in paragraph at lines 88--90
LaTeX Warning: There were undefined references.
Output written on main.pdf (11 pages, 123456 bytes).
LOG
cat > "$WORK/main.aux" <<'AUX'
\relax
\newlabel{fig:example}{{1}{2}}
\newlabel{ReferencesStart}{{}{10}}
AUX
python3 - "$SKILL/scripts" "$WORK" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import compile_paper as cp
d = Path(sys.argv[2])
text = (d / "main.log").read_text()
import re
assert len(re.findall(r"Citation .*? undefined", text)) == 2
assert len(re.findall(r"Overfull \\hbox", text)) == 2
assert cp.parse_total_pages(d / "main.log") == 11
assert cp.parse_label_page(d / "main.aux", "ReferencesStart") == 10
PY
echo "ok"

echo "All smoke checks passed."
