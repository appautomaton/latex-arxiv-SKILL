#!/usr/bin/env python3
"""Validate paper issues CSV schema and required fields."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "ID",
    "Phase",
    "Title",
    "Description",
    "Target_Citations",
    "Visualization",
    "Acceptance",
    "Status",
    "Verified_Citations",
    "Notes",
]

ALLOWED_STATUS = {"TODO", "DOING", "DONE", "SKIP"}
ALLOWED_PHASES = {"Research", "Writing", "Refinement", "QA"}


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2:
        return fail("usage: validate_paper_issues.py <issues.csv> [--strict]  (--strict: warnings also fail)")

    path = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    if not path.exists():
        return fail(f"file not found: {path}")

    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append(row)

    if not rows:
        return fail("csv is empty")

    header = rows[0]
    if header != REQUIRED_COLUMNS:
        return fail(
            "invalid header. expected: "
            + ",".join(REQUIRED_COLUMNS)
            + " | got: "
            + ",".join(header)
        )

    seen_ids: set[str] = set()
    total_target_citations = 0
    total_verified_citations = 0
    status_counts = {"TODO": 0, "DOING": 0, "DONE": 0, "SKIP": 0}
    phase_counts = {"Research": 0, "Writing": 0, "Refinement": 0, "QA": 0}
    errors = 0
    warnings = 0

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != len(REQUIRED_COLUMNS):
            print(f"error: row {idx}: expected {len(REQUIRED_COLUMNS)} columns, got {len(row)}", file=sys.stderr)
            errors += 1
            continue

        row_data = dict(zip(REQUIRED_COLUMNS, row))

        # Check required fields
        for col in ["ID", "Phase", "Title", "Description", "Acceptance", "Status"]:
            if not row_data[col].strip():
                print(f"error: row {idx}: '{col}' is empty", file=sys.stderr)
                errors += 1

        # Validate Status
        status = row_data["Status"].strip()
        if status not in ALLOWED_STATUS:
            print(f"error: row {idx}: 'Status' must be one of {sorted(ALLOWED_STATUS)}, got '{status}'", file=sys.stderr)
            errors += 1
        else:
            status_counts[status] += 1

        # Validate Phase
        phase = row_data["Phase"].strip()
        if phase not in ALLOWED_PHASES:
            print(f"error: row {idx}: 'Phase' must be one of {sorted(ALLOWED_PHASES)}, got '{phase}'", file=sys.stderr)
            errors += 1
        else:
            phase_counts[phase] += 1

        # Check for duplicate IDs
        issue_id = row_data["ID"].strip()
        if issue_id in seen_ids:
            print(f"error: row {idx}: duplicate ID '{issue_id}'", file=sys.stderr)
            errors += 1
        seen_ids.add(issue_id)

        # Parse citation counts
        target = None
        try:
            target = int(row_data["Target_Citations"].strip())
            total_target_citations += target
        except ValueError:
            print(f"warning: row {idx}: 'Target_Citations' is not a number", file=sys.stderr)
            warnings += 1

        verified = None
        try:
            verified = int(row_data["Verified_Citations"].strip())
            total_verified_citations += verified
        except ValueError:
            print(f"warning: row {idx}: 'Verified_Citations' is not a number", file=sys.stderr)
            warnings += 1

        # A DONE writing issue should meet its citation target
        if (
            phase == "Writing"
            and status == "DONE"
            and target is not None
            and verified is not None
            and verified < target
        ):
            print(
                f"warning: row {idx}: Writing issue '{issue_id}' is DONE but "
                f"Verified_Citations ({verified}) < Target_Citations ({target})",
                file=sys.stderr,
            )
            warnings += 1

    if errors > 0:
        print(f"\nValidation failed with {errors} error(s).", file=sys.stderr)
        return 1

    if strict and warnings > 0:
        print(f"\nValidation failed: {warnings} warning(s) in strict mode.", file=sys.stderr)
        return 1

    # Print summary
    print("Validation passed!")
    print(f"\nSummary:")
    print(f"  Total issues: {len(rows) - 1}")
    print(
        "  By phase: "
        f"Research={phase_counts['Research']}, "
        f"Writing={phase_counts['Writing']}, "
        f"Refinement={phase_counts['Refinement']}, "
        f"QA={phase_counts['QA']}"
    )
    print(f"  By status: TODO={status_counts['TODO']}, DOING={status_counts['DOING']}, DONE={status_counts['DONE']}, SKIP={status_counts['SKIP']}")
    print(f"  Target citations: {total_target_citations}")
    print(f"  Verified citations: {total_verified_citations}")

    if total_target_citations > 0:
        progress = (total_verified_citations / total_target_citations) * 100
        print(f"  Citation progress: {progress:.1f}%")

    if status_counts["DONE"] > 0:
        completion = (status_counts["DONE"] / (len(rows) - 1)) * 100
        print(f"  Task completion: {completion:.1f}%")

    if warnings > 0:
        print(f"\n{warnings} warning(s) found.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
