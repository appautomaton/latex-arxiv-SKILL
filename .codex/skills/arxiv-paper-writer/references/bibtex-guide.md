# BibTeX Guide (IEEE + arXiv)

## Citation keys
- Use `firstauthorYEARfirstword` (e.g., `smith2023transformer`).
- Keep keys consistent with `\cite{key}` usage.

## Author formatting
- Format names as `Last, First` and separate with `and`.
- Use `and others` for large author lists when appropriate.
- Escape special characters in names and titles (e.g., `&`, `%`, `_`, `#`, `{`, `}`) and represent accented characters with LaTeX commands when needed (e.g., `Garc{\'i}a`, `Fran{\c{c}}ois`, `Gr{\"o}bner`).

## Required fields by type
- `@article`: author, title, journal, year.
- `@inproceedings`: author, title, booktitle, year.
- `@article` (arXiv): author, title, journal (`arXiv preprint arXiv:<id>`), year, eprint, archivePrefix, primaryClass. `arxiv_registry.py export-bibtex` emits this format.
- `@book`: author/editor, title, publisher, year.
- `@misc`: author/title, howpublished or url, year.

## Quality tips
- Include DOI and URL when available.
- Use braces to protect capitalization in titles (e.g., `{BERT}`, `{CNN}`).
- Use three-letter month abbreviations: jan, feb, mar, etc.
- Never put `%` comments inside an entry; BibTeX treats them as content and breaks the entry. Full-line comments between entries are fine.
