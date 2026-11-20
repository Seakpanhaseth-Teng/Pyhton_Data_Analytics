# T02 — SQL Staging Layer & Data Contract

**Status:** 🔲 **Assigned to you**
**Owner:** you
**Effort:** ~90 minutes
**Builds on:** T01 (audit, already done)

---

## Business ask

> *"Everything downstream — the pack, the dashboard, the KPI numbers — should
> read from one place, not from re-reading the Excel file three times. Put the
> data in a database, tell me exactly what's in it, and make it rebuildable."*
> — Head of Commercial Analytics

## Why this ticket exists

Right now three future scripts would each open the same Excel file and each
could apply a slightly different cleaning step. That is how two reports end up
disagreeing. A staging layer fixes it: **load once, clean once, document once.**
Everything else queries the database.

It also gives you the SQL practice that 90% of analyst job descriptions list.

## Deliverables

1. `src/02_stage.py` — rebuilds the database from the Excel source
2. `data/clean/cellcard.duckdb` — created by that script (never committed)
3. `docs/01-data-contract.md` — the written contract (template below)

## The script must do this, in order

| Step | Requirement |
|---|---|
| 1 | Read `SOURCE_XLSX` and `DB_PATH` from `config.py`. No string paths. |
| 2 | Load both sheets with `pd.read_excel`. |
| 3 | Cast `Date` to a real datetime in pandas. |
| 4 | Connect to DuckDB and **drop-then-create** `stg_sales` and `stg_customers`. |
| 5 | Re-running must leave exactly 200 / 150 rows — never 400 / 300. |
| 6 | Assert row counts and fail loudly (non-zero exit) if they don't match. |
| 7 | Print a short confirmation with table names, row counts, and DB path. |

## Acceptance criteria (paste these into your submission)

- [ ] `python src/02_stage.py` runs clean from the repo root
- [ ] `SELECT COUNT(*) FROM stg_sales` → **200**
- [ ] `SELECT COUNT(*) FROM stg_customers` → **150**
- [ ] `DESCRIBE stg_sales` shows `Date` as `DATE` (not `VARCHAR`)
- [ ] Running the script **twice** still gives 200 / 150
- [ ] A deliberate bad source (wrong sheet name) makes the script exit non-zero
- [ ] `docs/01-data-contract.md` is filled in
- [ ] No file paths hard-coded anywhere

## Hints (read only if stuck ~15 min)

<details>
<summary>Hint 1 — getting a DataFrame into DuckDB</summary>

```python
import duckdb
con = duckdb.connect(str(DB_PATH))
con.register("sales_df", sales)         # makes the DF queryable as a table name
con.execute("CREATE OR REPLACE TABLE stg_sales AS SELECT * FROM sales_df")
con.unregister("sales_df")
```

`register` is a zero-copy view of the pandas object. `CREATE OR REPLACE TABLE
... AS SELECT` is what makes the rebuild idempotent — no manual `DROP` needed.
</details>

<details>
<summary>Hint 2 — the DATE problem</summary>

You converted `Date` to datetime **in pandas** (`pd.to_datetime`). Pandas
datetime columns arrive in DuckDB as `TIMESTAMP`, not `DATE`. If the criteria
demand `DATE`, cast inside the SQL:

```sql
CREATE OR REPLACE TABLE stg_sales AS
SELECT CAST("Date" AS DATE) AS sale_date, Region, ...
FROM sales_df
```

Decide whether you want to rename columns to `snake_case` at staging. **I would.**
SQL is far easier when columns have no spaces — otherwise every reference needs
`"double quotes"` and someone will forget one.
</details>

<details>
<summary>Hint 3 — failing loudly</summary>

Silent failure is worse than a crash. A `raise ValueError` at the end of a
script exits with code 1 and stops a pipeline. Prefer:

```python
assert n_sales == 200, f"expected 200 sales rows, got {n_sales}"
```

but note `assert` disappears under `python -O`, so for anything that matters:

```python
if n_sales != 200:
    raise ValueError(f"row count check failed: {n_sales} != 200")
```
</details>

<details>
<summary>Hint 4 — reading it back to prove it works</summary>

```python
print(con.execute("DESCRIBE stg_sales").fetchdf())
print(con.execute("SELECT COUNT(*) AS n FROM stg_sales").fetchone())
```
</details>

## Data contract template (`docs/01-data-contract.md`)

```markdown
# Data Contract — Cellcard Sales & Customer Extract (June 2026)

| Table | Grain | Rows | Primary key | Owner | Refresh |
|---|---|---|---|---|---|
| stg_sales | one transaction line | 200 | none (surrogate) | ... | monthly |
| stg_customers | one customer | 150 | CustomerID | ... | monthly |

## Known limitations
- (list the three audit fails here, in business language)

## Columns
| Table | Column | Type | Definition | Valid values |
...
```

Write the "known limitations" section **in business language** — the CFO reads
it, not a data engineer. "We cannot report revenue per customer" beats
"referential integrity violation between fact and dimension tables."

## Review checklist I will apply

1. Does re-running double the data? (most common bug)
2. Are types correct, or is everything a string?
3. Is the failure path real, or cosmetic?
4. Does the contract state gaps honestly, or hide them?
5. Is any logic duplicated from `01_audit.py` that should be shared?
