# T01 — Data Audit & Fitness-for-Purpose Verdict

**Status:** ✅ Complete (demo ticket — I built this one, you study it)
**Deliverable:** `src/01_audit.py` → `output/audit_report.txt`
**Effort:** ~2 hours (9 tables, 47 rules)

---

## Business ask

> *"Before we build June's pack on this extract, confirm it's fit to report on.
> I don't want to present a number and get challenged on it."*
> — Head of Commercial Analytics

## Why this ticket exists

A pack built on unverified data is a liability. The audit is not busywork —
it produces the **ground rules** that constrain every later ticket. Every
cleaning decision in T02 traces back to a line in this report.

## The extract

Nine objects from three systems, landed in `data/raw/`:

| Object | Grain | Rows | Source |
|---|---|---|---|
| `fact_sales.csv` | one sales transaction | 152,604 | billing_core |
| `fact_customer_month.csv` | customer × month | 145,434 | billing_core |
| `fact_targets.csv` | month × rep × product | 1,512 | crm |
| `dim_customer.csv` | customer | 12,000 | crm |
| `dim_rep.csv` | rep | 14 | master_data |
| `dim_product.csv` | product × price version | 7 | master_data |
| `dim_region.csv` | region | 5 | master_data |
| `dim_calendar.csv` | day | 546 | master_data |
| `dim_customer_legacy.xlsx` | customer (manual export) | 5 sheets | crm, manual |

## What the audit covers

| # | Section | Rules | What it catches |
|---|---------|-------|-----------------|
| 0 | Structure | 8 | File present, expected columns, parseable dates |
| 1 | Completeness | 6 | Nulls in required fields, missing calendar days |
| 2 | Uniqueness & grain | 6 | Duplicate keys, wrong grain, repeated snapshots |
| 3 | Validity | 11 | Illegal labels, negatives, impossible dates |
| 4 | Consistency | 6 | gross = units × price, net = gross − discount, churn vs status |
| 5 | Referential integrity | 6 | Orphan foreign keys, price-version coverage |
| 6 | Coverage bias | 3 | Rep volume spread, month gaps, empty region × product cells |
| 7 | Outliers | 4 | Values that would move an average |

## Result: 39 PASS / 1 WARN / 7 FAIL (47 checks)

**Fit for purpose: conditionally.** Report at **rep × region × product ×
month** only, after the staging layer resolves the seven defects below.

### The seven fails, and what each one *forces* you to do

1. **210 duplicate `txn_id` rows** (152,604 rows, 152,394 unique).
   Summing revenue without deduplicating overstates June by roughly the
   duplicate share.
   → *Dedupe on `txn_id` in staging. Assert 152,394 rows.*

2. **306 orphan sales lines ($176,058)** reference customer IDs that are not
   in `dim_customer`.
   → *Do not INNER JOIN sales to customers — you would silently delete
   $176k. LEFT JOIN, count the misses, and report them as unattributed.*

3. **2,288 `region_name` values carry stray whitespace**, producing 20
   distinct labels for 5 regions.
   → *`TRIM()` before any GROUP BY. This is the classic "Phnom Penh" vs
   "Phnom Penh " double-count.*

4. **240 `plan_type` values are outside the approved list** (`Postpaid`,
   `POSTPAID`, `Prepaid`, …).
   → *Normalise case before every plan-level split, or postpaid splits into
   three rows.*

5. **4 customers churn before they sign up.** They have zero snapshot rows.
   → *Exclude from cohort and retention work; flag to CRM.*

6. **9 customers sign up after 2026-06-30** and never appear in snapshots.
   → *Exclude from the June base. They are future-dated records, not
   customers.*

7. **14 phone numbers in the legacy export belong to more than one customer
   ID.**
   → *The legacy sheet is not a safe join key. Use `customer_id` from the
   CSV extract, and treat the xlsx as reference only.*

### The warn

**3 reps were hired mid-period** (REP11 Jul-25, REP13 Oct-25, REP14 Jan-26).
Their lower totals reflect tenure, not performance.

→ *Never rank reps on raw revenue. Compare attainment %, or lines per
selling day, and exclude partial-history reps from any "who is best" cut.*

## Three checks I got wrong before I got them right

These are worth more than the passing checks. Each is a rule that *looked*
right and produced a false alarm.

### 1. A rep-month gap that wasn't there

`"Every active rep has sales in every month since hire"` reported **473
missing rep-months** — more than the 252 rep-months that exist.

Cause: `pd.period_range(hire_date.to_period("M"), Period("2026-06"))` starts
at the hire year. REP01 was hired in 2019, so the rule demanded 88 months of
sales from an 18-month extract.

Fix: clamp the start to the data window —
`max(hire.to_period("M"), Period("2025-01"))`. Result: 0 gaps.

**Lesson:** when a count exceeds the population, the denominator is wrong,
not the data.

### 2. "Reps have comparable volume" — 3.4x, and it was fine

Raw transaction totals ranged 3.4x, but the three smallest were exactly the
three mid-period hires. The check was measuring tenure, not effort.

Fix: divide by distinct selling days, compare only full-period reps, and
report the spread as a percentage of the team median (73%–113%). Partial
hires became an explicit WARN instead of a hidden FAIL.

**Lesson:** before you call a distribution uneven, normalise by exposure.
Hire date, territory age, and opening hours all move volume without moving
skill.

### 3. 18% "outliers" in data usage

The IQR rule flagged 18% of `data_usage_gb` as outliers. The metric is
bimodal by plan: a prepaid SIM draws ~4 GB, a leased line draws ~280 GB.
Pooled, the entire broadband tail is "extreme".

Fix: compute the IQR **within `plan_type`**. Worst plan is now broadband at
2.9%.

**Lesson:** an outlier rule is only valid inside a homogeneous group. Segment
first, then judge. (Also: `plan_type` lives on `dim_customer`, not on the
monthly fact — the join is part of the check.)

## Second trap: numpy booleans

`check()` originally used `passed is True`. pandas returns `numpy.bool_`, and
`numpy.True_ is True` evaluates to `False`, so six passing checks printed as
FAIL. Fixed with `bool(passed)`.

**Lesson:** never identity-compare a value that came out of pandas. Coerce at
the boundary. This exact bug ships to production constantly.

## Second trap: a duplicated key is a question, not a verdict

My first pass on the old practice file reported "32 duplicate keys". Adding
`Region` to the key changed the count to 9, and the rows inside each group
still had different revenue — they were separate transactions.

**Lesson:** read the actual colliding rows before you call anything dirty.
Here the duplicates are genuine (identical `txn_id`, identical amounts), which
is why dedupe is the right fix and not a grain redefinition.

## What this means for the pack

| Rule | Consequence |
|---|---|
| Dedupe `txn_id` | June revenue = $6,157,228 across 152,394 unique lines |
| LEFT JOIN customers | $176,058 stays in the total, flagged unattributed |
| TRIM region, normalise plan | 5 regions, 3 plans, no phantom splits |
| Exclude future signups, fix churn < signup | 12,000 customers, 11,996 usable |
| Attainment, not raw revenue | Rep ranking survives the mid-period hires |
| Within-plan outlier tests | Usage is comparable only inside a plan |

## Evidence

```
output/audit_report.txt     # full rule-by-rule log, attach to the ticket
```
