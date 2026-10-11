# Archive (historical, do not use as input)

Material from the previous project iterations (methodologies v1, v2.1.3 and v2.2), kept as a record of what was tried and what each audit found. It is **superseded by** `docs/metrics_spec.md` (v3). The pipeline does not read from this folder.

Every Markdown file in this folder starts with a `HISTORICAL` banner. Numbers, thresholds and conclusions found here (for example the 34.5% risk figure of v2.2) are **not valid** and must not be cited as results.

## Contents

| Folder | Methodology | Why it was superseded |
| :--- | :--- | :--- |
| `methodology_v1_FAILED/` | v1: first 1,000 rows of each file | Convenience bias. The sample was dominated by legacy enrollments. See `docs/postmortem_convenience_biasv1.md` |
| `methodology_v2/` | v2 / v2.1.3 / v2.2: hardware filter (285 → 258 units), risk flag, Power BI | Instrument bias was solved, but loss was misinterpreted (`curr_udpcloss.packets` treated as a percentage), corrections masked data problems, and Python and Power BI differed. See `methodology_v2/README.md` and `methodology_v2/docs/` |

`methodology_v2/docs/data_lineage_v2.1.md` describes the data lineage of v2 and is the origin of the file inventory that v3 still uses (see below).

## What is still valid for v3

Not everything here is obsolete. The following items remain valid and are used by the current documentation:

- **Evidence images** in the repository root `evidence/` (copies are kept in `methodology_v2/evidence/` as part of the v2 record, and are not updated):
  - `contenido_tar_6.8GB.png`: content of `validated-data-sept2022.tar.gz` (16 files, 6,812,728,506 bytes uncompressed).
  - `validated-data-sept2022_filelist.png`: the extracted files and their sizes.
  - `filtrado_fiber_units.png`: the Excel filter on `Whitebox Model` that produced the 258-unit population (superseded by the reproducible rule in `docs/metrics_spec.md` section 1, which gives the same result).
- **Hardware finding:** legacy Whitebox models create artificial latency and loss. This is the reason for the 258-unit population in v3.

## Related documents

- `docs/decisions.md`: decisions of v3 and their alternatives.
- `docs/procedure_summary_v3.md`: what failed in v1 and v2 and what v3 changes.
- `README.md` (repository root): section "Why Version 3 Was Necessary".

Original repository (archived): https://github.com/sigloxiii/ftth-qoe-risk-optimization