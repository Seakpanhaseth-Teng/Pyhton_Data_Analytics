# T02 — SQL Staging Layer & Data Contract

**Status:** 🔲 **Assigned to you**
**Owner:** you
**Effort:** ~2 hours (8 tables, not 2)
**Builds on:** T01 (audit, already done)

---

## Business ask

> *"Everything downstream — the pack, the dashboard, the KPI numbers — should
> read from one place, not from re-reading nine CSV files three times. Put the
> data in a database, tell me exactly what's in it, and make it rebuildable."*
> — Head of Commercial Analytics

## Why this ticket exists

Right now every future script would open the same raw files and apply its own
version of the cleaning. That is how two reports end up disagreeing. A staging
layer fixes it: **load once, clean once, document once.** Everything else
queries `data/clean/cellcard.duckdb`.

It is also the ticket where the audit findings become code. Seven defects were
found in T01. Six of them are resolved here, in one place, with a test that
proves it.

## Deliverables

1. `src/02_stage.py` — rebuilds the database from `data/raw/`
2. `data/clean/cellcard.duckdb` — created by that script (never committed)
3. `docs/01-data-contract.md` — the written contract (template below)

## Target tables

| Staging table | Source | Grain | Expected rows |
|---|---|---|---|
| `stg_sales` | `fact_sales.csv` | one transaction line | **152,394** (after dedupe) |
| `stg_customer_month` | `fact_customer_month.csv` | customer × month | **145,434** |
| `stg_targets` | `fact_targets.csv` | month × rep × product | **1,512** |
| `stg_customers` | `dim_customer.csv` | customer | **12,000** |
| `stg_reps` | `dim_rep.csv` | rep | **14** |
| `stg_products` | `dim_product.csv` | product × price version | **7** |
| `stg_regions` | `dim_region.csv` | region | **5** |
| `stg_calendar` | `dim_calendar.csv` | day | **546** |
| `stg_customer_legacy` | `dim_customer_legacy.xlsx` | customer (5 sheets) | **12,014** *(stretch)* |

The 12,014 is not a typo: 12,000 customers plus 14 rows that reuse an existing
phone number. Five `TOTAL:` footer rows must be dropped, and the header is on
row 4, not row 1.

## Cleaning rules the staging layer must apply

These are the T01 fails. Apply each one **once**, here, and assert the result.

| # | Defect | Rule |
|---|---|---|
| 1 | 210 duplicate `txn_id` | Drop duplicates on `txn_id`. Keep the first. Assert 152,394. |
| 2 | 2,288 whitespace region names | `TRIM(region_name)` on `stg_sales`; assert 5 distinct values. |
| 3 | 240 case-variant plan types | `LOWER(TRIM(plan_type))`; assert 3 distinct values. |
| 4 | 9 future signups, 4 churn < signup | **Do not delete.** Add a boolean `is_valid_lifecycle` flag so downstream can exclude them explicitly. |
| 5 | 306 orphan sales lines | **Do not delete.** Keep them; the LEFT JOIN happens downstream. Report the count in the contract. |
| 6 | 14 duplicate legacy phones | Keep both rows; flag with `is_duplicate_phone`. |
| 7 | Mixed date formats in legacy | Parse with `dayfirst=True` only if you can prove the majority format; otherwise parse explicitly and count the failures. |

**Rule of thumb:** staging normalises and flags. It does not decide what the
business is allowed to see. Deleting rows here hides the defect instead of
documenting it — and the duplicate `txn_id` is the only exception, because
those rows are literally the same transaction.

## The script must do this, in order

| Step | Requirement |
|---|---|
| 1 | Read every path from `config.RAW` and `config.DB_PATH`. No string paths. |
| 2 | Load CSVs with explicit `dtype` for ID columns (do not let pandas guess). |
| 3 | Cast every date column to a real datetime in pandas. |
| 4 | Clean per the table above, in pandas or SQL — your choice, but one place. |
| 5 | `CREATE OR REPLACE TABLE` for every staging table (idempotent rebuild). |
| 6 | Assert each row count **and** the normalisation results. Fail non-zero. |
| 7 | Print table name, row count, and `DESCRIBE` output for `stg_sales`. |

## Acceptance criteria (paste these into your submission)

- [ ] `python src/02_stage.py` runs clean from the repo root
- [ ] All eight core table counts match the table above exactly
- [ ] `SELECT COUNT(*) FROM stg_sales` → **152,394**
- [ ] `SELECT COUNT(DISTINCT txn_id) FROM stg_sales` → **152,394** (no dupes left)
- [ ] `DESCRIBE stg_sales` shows `txn_date` as `DATE` (not `VARCHAR`/`TIMESTAMP`)
- [ ] `SELECT COUNT(DISTINCT region_name) FROM stg_sales` → **5**
- [ ] `SELECT COUNT(DISTINCT plan_type) FROM stg_customers` → **3**
- [ ] Running the script **twice** still gives the same counts
- [ ] A deliberate bad source (rename a file, or point at a missing sheet) exits non-zero
- [ ] `docs/01-data-contract.md` is filled in
- [ ] No file paths hard-coded anywhere

## Hints (read only if stuck ~15 min)

<details>
<summary>Hint 1 — getting a DataFrame into DuckDB</summary>

```python
import duckdb
con = duckdb.connect(str(DB_PATH))
con.register("sales_df", sales)          # zero-copy view of the pandas object
con.execute("""
    CREATE OR REPLACE TABLE stg_sales AS
    SELECT txn_id, CAST(txn_date AS DATE) AS txn_date, ...
    FROM sales_df
""")
con.unregister("sales_df")
```

`CREATE OR REPLACE TABLE ... AS SELECT` is what makes the rebuild idempotent —
no manual `DROP`, and re-running cannot append.
</details>

<details>
<summary>Hint 2 — the DATE problem</summary>

Pandas `datetime64` arrives in DuckDB as `TIMESTAMP`. If the criteria demand
`DATE`, cast inside the SQL: `CAST(txn_date AS DATE) AS txn_date`.

Same story for `month`: it is `YYYY-MM` text. Either keep it as `VARCHAR` (and
document that choice) or build a real date with `strptime(month || '-01',
'%Y-%m-%d')::DATE`. Pick one and be consistent across all three tables that
carry it.
</details>

<details>
<summary>Hint 3 — dedupe without losing money</summary>

```python
before = len(sales)
sales = sales.drop_duplicates(subset="txn_id", keep="first")
print(f"dropped {before - len(sales):,} duplicate lines")
```

Print the number dropped. A silent dedupe is indistinguishable from a silent
data loss bug. The audit said 210; if your script drops 211, stop and find out
why.
</details>

<details>
<summary>Hint 4 — reading the legacy workbook</summary>

```python
sheets = pd.read_excel(RAW["customer_legacy"], sheet_name=None, skiprows=3)
legacy = pd.concat(
    [df.assign(source_sheet=name) for name, df in sheets.items()],
    ignore_index=True,
)
legacy = legacy[~legacy["Customer ID"].astype(str).str.startswith("TOTAL")]
```

`sheet_name=None` returns a dict of DataFrames — one per sheet. You need the
sheet name as a column, otherwise you cannot tell Phnom Penh from Kampot after
the concat.
</details>

<details>
<summary>Hint 5 — failing loudly</summary>

```python
if n_sales != 152_394:
    raise ValueError(f"row count check failed: {n_sales:,} != 152,394")
```

`assert` disappears under `python -O`. For a pipeline gate, raise.
</details>

## Data contract template (`docs/01-data-contract.md`)

```markdown
# Data Contract — Cellcard Commercial Extract (June 2026)

| Table | Grain | Rows | Primary key | Owner | Refresh |
|---|---|---|---|---|---|
| stg_sales | one transaction line | 152,394 | txn_id | Commercial Analytics | monthly |
| stg_customer_month | customer x month | 145,434 | customer_id + month | ... | monthly |
| stg_targets | month x rep x product | 1,512 | month + rep_id + product_id | ... | monthly |
| stg_customers | one customer | 12,000 | customer_id | ... | monthly |
| stg_reps | one rep | 14 | rep_id | ... | ad hoc |
| stg_products | product x price version | 7 | product_id + price_effective_from | ... | ad hoc |
| stg_regions | one region | 5 | region_id | ... | ad hoc |
| stg_calendar | one day | 546 | date | ... | annual |

## Cleaning applied at staging
- (list each rule and the count it changed)

## Known limitations (business language)
- (the seven T01 fails, each with what it means for the pack)
- (state the bulk-order units caveat: sales revenue and MRR answer
  different questions and must never be reconciled)

## Columns
| Table | Column | Type | Definition | Valid values |
...
```

Write "known limitations" so the Sales Director can read it. "We cannot
attribute $176k of June revenue to a customer because 306 lines carry an
unknown customer ID" beats "referential integrity violation".

## Review checklist I will apply

1. Does re-running double the data? (most common bug)
2. Are types correct, or is everything a string?
3. Is the dedupe count printed and equal to 210?
4. Do the normalisation assertions actually run, or are they comments?
5. Is the failure path real, or cosmetic?
6. Does the contract state the seven gaps honestly, or hide them?
7. Is any logic duplicated from `01_audit.py` that should be shared?
