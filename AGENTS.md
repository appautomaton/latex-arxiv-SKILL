# AGENTS.md

This repo uses an **issues‑driven paper writing workflow** for arXiv LaTeX review papers.

These rules govern paper-writing runs. Changes to the harness itself (scripts, skills, docs) follow normal engineering practice.

## Workflow (issue‑driven)
1) **Research snapshot (no prose)**: translate topic → keywords → search 10–20 key papers.
2) **Scaffold project**: create the folder and base LaTeX files; compile early to catch errors.
3) **Framework + titles**: build a section framework (headings + bullets + seed citations) and propose 2–4 titles.
4) **Draft plan**: document the framework, section/subsection plan, and writing approach.
5) **Gate**: after framework generation, only headings/bullets/seed cites until user approves the plan **and** issues CSV exists (no prose).
6) **Create issues CSV**: this is the execution contract; validate it and update as it evolves.
7) **Write per issue**: research → write → verify citations → update issue status + verified counts.
8) **Refine rhythm**: after all writing issues are DONE, apply the `latex-rhythm-refiner` skill section by section.
9) **QA + compile**: run internal QA checks and compile; fix errors before delivery.

## Non‑negotiable rules
- **No prose before approval**: do not write into `main.tex` until plan approved and issues CSV exists.
- **Issues CSV is the contract**: update it as you progress; only mark DONE when criteria met.
- **Insert issues when scope grows**: if a new non-trivial task is discovered mid-run, add/split/insert an issue row and keep going until all issues are `DONE`/`SKIP` (re-validate after edits).
- **Citations must be verified**: every citation must be checked against an online source before adding to `ref.bib`.
- **Use skill scripts**: prefer the provided tooling for scaffolding, validation, compile, and citation workflows; avoid ad‑hoc commands.
- **LaTeX is required**: compile and resolve errors before delivery.
- **Keep issues CSV valid**: re‑validate after edits.
