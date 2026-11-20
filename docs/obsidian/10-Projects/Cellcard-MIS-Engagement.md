---
project: Cellcard MIS Reporting
status: active
updated: 2026-11-20
repo: C:\Users\Admin\Github_Projects\Pyhton_Data_Analytics
tags: [data-analytics, mis-reporting, duckdb, python, training, handoff]
---

# Cellcard MIS Reporting — Full Session Record

> **Separate project from [[Library-Management-System]].** Different repo, different
> stack, different note. Nothing here is shared with the LMS work.

This is the complete record of the session on 2026-11-20: what we decided, what we
built, what we found, and exactly where to resume.

---

## 1. What this project is

- **Fictional employer:** Cellcard, a Cambodian telecom. **Role:** MIS Analyst, Commercial Analytics (dual-hatted analyst + reporting owner).
- **Ask:** produce the June 2026 month-end performance pack for the Sales Director by 5 July.
- **Nature:** a **recurring monthly pack**, not a one-off study. That distinction drives every technical choice — the output must rebuild unattended.
- **Three stakeholder questions, always in this order:**
  1. Are we going to hit the number? (target vs actual)
  2. Where is the gap coming from? (region, product, rep)
  3. What do we do about it? (a decision, not a chart)
- **Learning goal:** data analyst + MIS reporting skills, built only with free tools.

## 2. Decisions made (D1–D8)

- **D1 Role scope** — train for both Data Analyst and MIS Reporting; MIS is the backbone, analyst depth on top. BA track deferred, not cancelled.
- **D2 Learning mode** — pair programming: coach demos one ticket narrating decisions, learner builds the next from a spec, coach reviews like a senior analyst and sends it back if wrong.
- **D3 Stack** — Python + DuckDB (SQL) + openpyxl Excel pack + matplotlib + static HTML dashboard. Free forever.
- **D4 Dataset** — the supplied practice file is too shallow (1 month, 350 rows, no join keys). Replace with a generated 18-month dataset via the prompt in `docs/prompts/generate-richer-dataset.md`.
- **D5 Hosting** — GitHub Pages for the dashboard, GitHub Actions for monthly refresh. No paid BI licence.
- **D6 Repo layout** — numbered pipeline scripts in `src/`, tickets as markdown with acceptance criteria, outputs to `output/`, no hard-coded paths (all via `src/config.py`).
- **D7 Archive policy** — original linear script kept in `legacy/`, never deleted; source data only in `data/raw/`.
- **D8 Note sync** — this agent can read but not write `C:\Users\Admin\Documents`. Notes are authored in `docs/obsidian/` and copied to the vault with `tools/sync_obsidian.ps1`.

## 3. What was built

Repo: `C:\Users\Admin\Github_Projects\Pyhton_Data_Analytics`

- `src/config.py` — single source for paths, reporting period, valid domains, audit thresholds.
- `src/01_audit.py` — **T01**, 22 audit rules → PASS/FAIL, writes `output/audit_report.txt`.
- `src/02_stage.py` — **T02**, TODO skeleton (learner's live assignment).
- `tickets/T01-data-audit.md` — findings + the two mistakes made while building it.
- `tickets/T02-staging.md` — assignment: ask, acceptance criteria, 4 progressive hints, review checklist.
- `docs/00-engagement-brief.md` — company, role, pipeline, ticket queue, binding rules.
- `docs/02-zero-cost-stack.md` — every tool with licence, cost, free-tier limit.
- `docs/prompts/generate-richer-dataset.md` — copy-paste prompt for Claude.
- `tools/sync_obsidian.ps1` — copies staged notes into the vault, idempotent.
- `legacy/analyze_cellcard.py` — original linear script, archived, path fixed.
- Data moved to `data/raw/`; `output/`, `data/clean/`, `*.duckdb` git-ignored.

Commits: `6b95c5d` (T01 + scaffold), `6847c97` (prompt, free stack, notes), `aca5d61` (write-blocker + sync decision).

## 4. T01 audit result — the part that constrains everything else

**16 PASS / 3 WARN / 3 FAIL. Verdict: "conditionally fit" — report at rep × region × product level only.**

The three fails, each of which *forbids* a specific analysis:

| Finding | Binding consequence |
|---|---|
| Revenue per unit is a random $8–$20 draw for **every** product (SIM and Home Internet bill identically) | Never derive Revenue from units × price. Sum Revenue only. |
| `Sales_Data` has **no CustomerID**; zero shared columns with `Customer_Data` | Revenue-per-customer is impossible. It's a written data request to the source owner, not a task. |
| Busiest rep 50 transactions, quietest 18 (2.8×); Nita has no Sihanoukville rows | Never rank reps on raw revenue — it rewards territory, not talent. Use attainment % and revenue-per-call. |

Warns: `Sales_Data` has no business key (transaction-grained, unique across all 10 columns — sum, don't count); Revenue usable as an amount but not reconstructable; one rep/region pair has zero activity.

**Two lessons worth keeping:**
- "32 duplicate records" was wrong. Adding `Region` to the key gave 9, and those rows still had different Revenue → separate transactions. A repeated key is a *question about grain*, not a verdict about quality. Read the colliding rows.
- `check()` used `passed is True`, but pandas returns `numpy.bool_` and `numpy.True_ is True` is `False`, so six passing checks printed as FAIL. Coerce with `bool()` at the boundary. This bug ships to production constantly.

## 5. The dataset gap and the fix

Current data cannot teach trends, cohorts, seasonality, retention, or variance analysis. The prompt in `docs/prompts/generate-richer-dataset.md` requests:

- 18 months (2025-01 → 2026-06), ~150k sales lines, 12k customers, 14 reps, 6 products.
- Real `customer_id` on sales lines, a price list with a mid-period price revision, `dim_calendar` with Cambodian public holidays.
- `fact_customer_month` snapshots (MRR, usage, payment status) — the actual month-end MIS backbone.
- Seasonality (Khmer New Year, Pchum Ben, payday, tourism), product-mix drift, two dated promo campaigns, rep skill heterogeneity.
- **12 deliberately planted defects** plus a separate `answer_key/` folder so the audit can be self-graded.
- A seeded `make_dataset.py` and a `validate_dataset.py` with 10 acceptance tests Claude must actually run.

**Open decision:** regenerate the dataset *before* writing T02, or the staging script will be written twice (9 tables instead of 2).

## 6. Cost position — everything is free

Python, pandas, DuckDB (MIT), openpyxl, matplotlib, Git, VS Code, LibreOffice Calc (instead of Excel), Obsidian for personal use — all $0.

**The trap:** Power BI Desktop is free to build in, but *sharing* needs Pro at ~$14/user/month. Free dashboard path: **Looker Studio** (free including sharing) or **Evidence.dev → GitHub Pages**, with **GitHub Actions** for monthly refresh (~2,000 min/month private, unlimited public). Details and tier limits in `docs/02-zero-cost-stack.md`.

## 7. Blocker: Obsidian writes are blocked

The agent environment can **read** `C:\Users\Admin\Documents` but **cannot write** to it — a plain `.txt` probe failed too, so it is not an Obsidian issue (likely Windows Defender Controlled Folder Access or a policy). The MCP vault tools fail identically.

**Workaround:** notes are authored here in `docs/obsidian/` and copied with:

```powershell
powershell -File tools/sync_obsidian.ps1
```

Target: `10-Projects/Cellcard-MIS-Engagement.md`. Verified working against a scratch vault; idempotent on repeat runs.

## 8. Where we stopped

**T01 complete. T02 assigned, not started.** `src/02_stage.py` is a TODO skeleton.

T02 asks for: read paths from config → load both sheets → cast Date → build `stg_sales` + `stg_customers` in `data/clean/cellcard.duckdb` with `CREATE OR REPLACE` → assert 200/150 rows → fail loudly → write `docs/01-data-contract.md`.

The two things that will bite: re-running must give 200 rows not 400, and pandas datetimes arrive in DuckDB as `TIMESTAMP`, not `DATE`.

## 9. How to resume in a fresh session

Paste this:

> Read `docs/obsidian/10-Projects/Cellcard-MIS-Engagement.md` and `docs/00-engagement-brief.md` in `C:\Users\Admin\Github_Projects\Pyhton_Data_Analytics`. Then review `src/02_stage.py` against `tickets/T02-staging.md`.

If instead the dataset was regenerated first, the line becomes:

> ...The dataset was replaced; re-run `python src/01_audit.py`, update `tickets/T01-data-audit.md` with the new verdict, then reassign T02 against the new schema.

## 10. Open questions for next session

- Regenerate the dataset first, or finish T02 against the current 2-table source?
- Do you want the Excel MIS pack to target LibreOffice-compatible formatting only, or assume real Excel?
- Should the dashboard be Evidence.dev (BI-as-code, nicer portfolio piece) or a hand-built static HTML page (fewer moving parts)?
