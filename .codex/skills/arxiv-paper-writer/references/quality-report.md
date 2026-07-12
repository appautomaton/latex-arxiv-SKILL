# Internal QA (Agent Only)

Purpose: ensure coherence and consistency before delivery. Do NOT create a separate report file unless the user explicitly asks. Record pass/fail notes in the issues CSV.

## Coherence checks
- Outline alignment: each section matches the approved outline and stays in-scope
- Claims supported: every non-trivial claim has a citation
- No new claims in the conclusion
- Terminology consistent across sections

## Citation checks
- 100% of citations verified online before inclusion
- Citation density meets section targets
- BibTeX entries are clean (correct fields, escaped special characters)

## Writing-style checks
- No 3 consecutive sentences without citations (abstracts exempted)
- Rhythm refinement completed in Phase 2.5 (before QA)

## Visual checks
- All figures/tables referenced in text
- Two-column sizing respected; no overflow
- Use double-column spans only when necessary
- Externally sourced figure content includes in-text citations

## Structure checks
- Abstract, keywords, and section order consistent with the template
- Acronyms defined on first use
- Symbols and variables defined before use

## Delivery checks
- Page count within target (main text only): from this skill folder, run `python3 scripts/compile_paper.py --project-dir <paper_dir> --report-page-counts` and use "Main text pages (exclude ref-start page)". The required `ReferencesStart` label is provided by the template.
- Log summary clean: `compile_paper.py` prints undefined-citation and `Overfull \hbox` counts after each successful compile; both must be zero.
- No untracked work: any newly discovered non-trivial task exists as an issue row and is `DONE`/`SKIP` (with a short note if `SKIP`).
- No compilation errors (or LaTeX syntax validated if no compiler)
