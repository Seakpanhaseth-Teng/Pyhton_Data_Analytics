# Cellcard Commercial Analytics — MIS Reporting Engagement

A simulated month-end reporting cycle for a telecom sales organisation, built as
a training ground for **MIS reporting / data analyst** work. The company is
fictional, the dataset is synthetic, and the process is the real thing.

> **You are the analyst.** Start with [`docs/00-engagement-brief.md`](docs/00-engagement-brief.md)
> for the company context and the ticket queue, then open
> [`tickets/T02-staging.md`](tickets/T02-staging.md) — that is your live assignment.

---

## Where things stand

| Ticket | Deliverable | Status |
|---|---|---|
| T01 | Data audit → `output/audit_report.txt` | ✅ done |
| T02 | SQL staging layer + data contract | 🔲 **your turn** |
| T03 | KPI dictionary & metric layer | pending |
| T04 | Sales performance analysis | pending |
| T05 | Customer & churn diagnostics | pending |
| T06 | Automated Excel MIS pack | pending |
| T07 | Dashboard + insight memo | pending |

**Audit verdict:** 16 pass / 3 warn / 3 fail. Fit for purpose *conditionally* —
report at rep × region × product level only. Three hard constraints came out of
it and they govern every downstream number. See
[`tickets/T01-data-audit.md`](tickets/T01-data-audit.md).

## Repository layout

```
data/raw/     Cellcard_Interview_Practice_Dataset.xlsx   source of truth (never edited)
data/clean/   cellcard.duckdb                            built by 02_stage.py (git-ignored)

src/config.py        all paths, domains, thresholds
src/01_audit.py      T01  audit rules -> PASS/FAIL report
src/02_stage.py      T02  Excel -> DuckDB staging        <- skeleton, your ticket

sql/                 analytical queries (T03+)
docs/                engagement brief, zero-cost stack, data contract, KPI defs
docs/prompts/        prompts for generating a richer dataset
docs/obsidian/       project notes staged for the vault
tickets/             one file per ticket: ask, criteria, hints, review notes
output/              every artifact you would attach to a ticket
tools/               helper scripts (note sync)

legacy/              the original linear script, archived for reference
```

## Reading order

1. [`docs/00-engagement-brief.md`](docs/00-engagement-brief.md) — the company, the role, the rules
2. [`docs/02-zero-cost-stack.md`](docs/02-zero-cost-stack.md) — every tool, licence, and free-tier limit
3. [`tickets/T01-data-audit.md`](tickets/T01-data-audit.md) — what the audit found and why it binds everything after it
4. [`tickets/T02-staging.md`](tickets/T02-staging.md) — your assignment

## Obsidian

Project notes are drafted in `docs/obsidian/` and copied into the vault:

```powershell
powershell -File tools/sync_obsidian.ps1
```

Targets `10-Projects/Cellcard-MIS-Engagement.md` and
`20-Decisions/Cellcard-MIS-Decisions.md`. The existing
`Library-Management-System` note is never touched.

## Setup

```powershell
python -m pip install pandas duckdb openpyxl xlsxwriter matplotlib
```

## Run

```powershell
python src/01_audit.py      # prints verdicts, writes output/audit_report.txt
python src/02_stage.py      # builds data/clean/cellcard.duckdb   (not built yet)
```

## The rules this project enforces

1. No script hard-codes a path — everything imports from `src/config.py`.
2. Every ticket has acceptance criteria. A ticket is done when they pass review.
3. Every number in a deliverable must reconcile to the same number in another view.
4. Data gaps are reported in writing, never worked around silently.
5. The pack must rebuild from raw source with one command.

## What this is not

- Not a notebook. Notebooks are for exploring; this is a pipeline that must rerun
  next month unattended.
- Not a chart gallery. Every chart has to answer one of the three questions in
  the brief, or it gets cut.
