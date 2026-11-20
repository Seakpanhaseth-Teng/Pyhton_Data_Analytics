---
project: Cellcard MIS Reporting
status: active
updated: 2026-11-20
repo: C:\Users\Admin\Github_Projects\Pyhton_Data_Analytics
tags: [data-analytics, mis-reporting, duckdb, python, training]
---

# Cellcard MIS Reporting — Simulated Engagement

> Separate project from [[Library-Management-System]]. Different repo, different
> stack, different note. Nothing here is shared with the LMS work.

## Frame
- Fictional employer: Cellcard (Cambodian telecom). Role: MIS Analyst, Commercial Analytics.
- Reporting period: June 2026. Monthly recurring pack, not a one-off study.
- Learning mode: pair programming — coach builds one ticket as demo, learner builds the rest, coach reviews like a senior analyst.
- Goal: data analyst + MIS reporting skills on a genuinely zero-cost stack.

## Repo
- `C:\Users\Admin\Github_Projects\Pyhton_Data_Analytics`
- Pipeline: Excel -> audit -> DuckDB staging -> KPI layer -> Excel pack + dashboard + memo
- Structure: `src/` scripts, `sql/` queries, `docs/`, `tickets/`, `output/`, `legacy/`
- Original linear script archived to `legacy/analyze_cellcard.py`

## Ticket queue
- [x] T01 Data audit — 16 pass / 3 warn / 3 fail, verdict "conditionally fit"
- [ ] T02 SQL staging + data contract — **live assignment**, skeleton at `src/02_stage.py`
- [ ] T03 KPI dictionary & metric layer
- [ ] T04 Sales performance analysis
- [ ] T05 Customer & churn diagnostics
- [ ] T06 Automated Excel MIS pack
- [ ] T07 Dashboard + insight memo

## Audit ground rules (binding on every downstream number)
- Never rank reps on raw revenue — transaction volume varies 2.8x (50 vs 18). Use attainment % and revenue per call.
- Never derive Revenue from units x price — no price list in source; revenue is an amount only.
- Never join sales to customers — no shared key. Log as data gap, do not fake it.
- State the period on every page.

## Known dataset limits
- 200 sales rows / 150 customers / one month -> too shallow for trends, cohorts, seasonality.
- Decision: replace with a richer generated dataset; prompt at `docs/prompts/generate-richer-dataset.md`.
- Target shape: 18 months, ~150k sales lines, 12k customers, real join keys, price list, customer-month snapshots, planted defects + separate answer key.

## Session log
- 2026-11-20 — Scoped engagement; built T01 audit; restructured repo; T02 skeleton assigned. Wrote richer-dataset prompt and zero-cost stack doc. Obsidian REST API was offline at session start.

## Next session: start here
1. Read `docs/00-engagement-brief.md` for context.
2. If T02 is done: ask for code review of `src/02_stage.py`.
3. If the dataset was regenerated: re-run `python src/01_audit.py` and update audit findings before anything else.
