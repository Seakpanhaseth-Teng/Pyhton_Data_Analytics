# T01 — Data Audit & Fitness-for-Purpose Verdict

**Status:** ✅ Complete (demo ticket — I built this one, you study it)
**Deliverable:** `src/01_audit.py` → `output/audit_report.txt`
**Effort:** ~1 hour

---

## Business ask

> *"Before we build June's pack on this extract, confirm it's fit to report on.
> I don't want to present a number and get challenged on it."*
> — Head of Commercial Analytics

## Why this ticket exists

A pack built on unverified data is a liability. The audit is not busywork —
it produces the **ground rules** that constrain every later ticket. Three of
the four rules in `docs/00-engagement-brief.md §7` came out of this file.

## What the audit covers

| # | Check | What it catches |
|---|-------|-----------------|
| 0 | Structure | Wrong sheet, wrong dtype, text dates |
| 1 | Completeness | Nulls, missing calendar days |
| 2 | Uniqueness & grain | Fake "duplicates", missing natural key |
| 3 | Validity | Illegal region/product/status, negatives, zero denominators |
| 4 | Consistency | Revenue vs units x price |
| 5 | Referential integrity | Can the two tables be joined at all? |
| 6 | Outliers | Values that would move an average |
| 7 | Coverage bias | Unequal opportunity before ranking anyone |

## Result: 16 PASS / 3 WARN / 3 FAIL

**Fit for purpose: conditionally.** Report at rep × region × product level only.

### The three fails, and what each one *forces* you to do

1. **No price list.** Revenue per unit is a random draw from $8–$20 for *every*
   product — a SIM and a Home Internet line bill identically. Revenue is
   synthetic.
   → *Do not derive Revenue from units × price. Sum Revenue only.*

2. **No join key.** `Sales_Data` has no `CustomerID`. The two tables cannot be
   joined.
   → *Never promise revenue-by-customer. Log it as a data gap and request it.*

3. **Unequal rep coverage.** Busiest rep has 50 transactions, quietest has 18
   (2.8x). Nita has zero rows in Sihanoukville.
   → *Never rank reps on raw revenue. Use attainment % and revenue-per-call.*

### The warns

- `Sales_Data` has **no business key** — rows are transaction-grained and
  unique across all 10 columns. Dedupe is unnecessary; sum, don't count.
- Revenue is *usable as an amount* but not reconstructable.
- One rep/region pair (Nita × Sihanoukville) has no activity.

### The trap I nearly fell into

My first pass reported "32 duplicate keys" and I almost wrote it up as a defect.
Adding `Region` to the key changed the count to 9; the rows inside each group
still had **different Revenue**, which means they are separate transactions.

**Lesson:** a duplicated key is a question about grain, not a verdict about
quality. Read the actual colliding rows before you call anything dirty.

## Second trap: numpy booleans

`check()` originally used `passed is True`. pandas returns `numpy.bool_`, and
`numpy.True_ is True` evaluates to `False`, so six passing checks printed as
FAIL. Fixed with `bool(passed)`.

**Lesson:** never identity-compare a value that came out of pandas. Coerce at
the boundary. This exact bug ships to production constantly.

## Evidence

```
output/audit_report.txt     # full rule-by-rule log, attach to the ticket
```
