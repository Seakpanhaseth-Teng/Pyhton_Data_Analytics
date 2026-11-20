---
project: Cellcard MIS Reporting
status: active
updated: 2026-11-20
tags: [decisions, adr, cellcard]
---

# Cellcard MIS — Decision Log

- **D1 Role scope** — Train for both Data Analyst and MIS Reporting. MIS is the backbone; analyst depth applied on top. BA track deferred.
- **D2 Learning mode** — Pair programming: coach demos one ticket, learner builds the next from a spec, coach reviews like a senior analyst.
- **D3 Stack** — Python + DuckDB (SQL) + openpyxl Excel pack + matplotlib + static HTML dashboard. All free forever.
- **D4 Dataset** — Current practice file too shallow (1 month, 350 rows, no join keys). Replace with generated 18-month dataset; prompt at `docs/prompts/generate-richer-dataset.md`.
- **D5 Hosting** — GitHub Pages for dashboard, GitHub Actions for monthly refresh. No paid BI licence; Power BI Desktop optional, its sharing needs Pro.
- **D6 Repo layout** — Numbered pipeline scripts in `src/`, tickets as markdown with acceptance criteria, all outputs to `output/`, no hard-coded paths (all via `src/config.py`).
- **D7 Archive policy** — Original linear script kept in `legacy/`, never deleted; data files live only in `data/raw/`.
