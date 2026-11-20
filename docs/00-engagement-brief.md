# Engagement Brief — Cellcard Commercial Analytics

**Simulation notice:** Cellcard is a real Cambodian telecom, but this dataset is
synthetic and this engagement is fictional. Everything else — the roles, the
process, the deliverables, the review loop — is how the work actually runs.

---

## 1. The setup

| | |
|---|---|
| **Company** | Cellcard (mobile + home broadband), Cambodia |
| **Your role** | MIS Analyst, Commercial Analytics (dual-hatted: analyst + reporting owner) |
| **You report to** | Head of Commercial Analytics |
| **Your stakeholders** | Sales Director (5 regional managers), Marketing lead, CFO's office |
| **Reporting period** | June 2026 (month-end close) |
| **Data source** | `data/raw/Cellcard_Interview_Practice_Dataset.xlsx` |
| **Deadline** | Performance pack to Sales Director by 5 July |
| **Cadence** | This is a **recurring monthly pack**, not a one-off study |

## 2. Why the role matters

Cellcard's sales org runs on targets. Five regions, four products, six reps.
Every month the Sales Director asks the same three questions, in this order:

1. **Are we going to hit the number?** (target vs actual, and by how much)
2. **Where is the gap coming from?** (which region, product, rep)
3. **What do we do about it?** (a decision, not a chart)

An MIS analyst's job is to answer those three questions *on time, with numbers
that reconcile, in a format a busy director can read in ninety seconds.* The
analysis is the easy part. The hard parts are:

- **Data quality.** If the extract is broken, the pack is wrong, and you find
  out in the meeting.
- **Definitions.** "Active customer" means something specific. If you and the
  CFO disagree, both your numbers are wrong.
- **Reproducibility.** Next month someone else (or future-you) runs the pack.
  If it lives in a notebook with manual copy-paste, it is already broken.

## 3. The delivery pipeline you are building

```
 Excel source  ->  audit  ->  SQL staging (DuckDB)  ->  KPI layer
                                                          |
                    +-------------------------------------+
                    |                  |                  |
              Excel MIS pack     HTML dashboard     Insight memo
              (for Finance)      (for Sales)        (for the Director)
```

Each arrow is a script that runs unattended. One command refreshes the whole
pack. That is the difference between a report and an analysis.

## 4. The ticket queue

Work arrives as tickets with a business ask and acceptance criteria — never as
"make me a chart". A ticket is only done when its criteria are met and reviewed.

| # | Ticket | Owner | Status |
|---|--------|-------|--------|
| T01 | Data audit & fitness-for-purpose verdict | *built as your demo* | ✅ done |
| T02 | SQL staging layer + data contract | **you** | 🔲 assigned |
| T03 | KPI dictionary & metric layer | you | 🔲 |
| T04 | Sales performance analysis (attainment, efficiency) | you | 🔲 |
| T05 | Customer base & churn diagnostics | you | 🔲 |
| T06 | Automated Excel MIS pack | you | 🔲 |
| T07 | Dashboard + insight memo | you | 🔲 |

## 5. How we work together (pair programming)

For every ticket I do exactly one of these:

- **Demo** — I build it, narrating each decision, and you run it.
- **Build** — you build it from scratch using the ticket's hints. I review like
  a senior analyst: I look for wrong logic, fragile code, and missed business
  meaning, and I send it back if it is not right.

The rule that makes this work: **you write the code, not me.** Reading code
teaches recognition. Writing code teaches recall. Interviews test recall.

When you get stuck for more than ~15 minutes, say so and I will give you the
next hint, not the answer.

## 6. Definition of done (applies to every ticket)

1. Runs end-to-end with one command from a clean checkout.
2. No hard-coded paths (all via `src/config.py`).
3. Outputs land in `output/`.
4. Numbers reconcile: totals in the detail sheet equal totals in the summary.
5. Reviewed and signed off in this file's ticket list.

## 7. Ground rules for the numbers

These come straight out of the audit (T01) and they are non-negotiable:

- **Never rank reps on raw revenue.** Transaction volume varies 2.8x between
  reps, so totals reflect territory, not talent. Use attainment % and
  revenue-per-call.
- **Never derive Revenue from units x price.** The source has no price list;
  Revenue is the source of truth as an amount.
- **Never join sales to customers.** There is no shared key. Asking for that
  join is a data request to the source owner, not an analysis you can fake.
- **State the period on every page.** "June 2026", not "this month".
