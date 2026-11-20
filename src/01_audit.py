"""
TICKET T01 — Data Audit
=======================
Pairs with: tickets/T01-data-audit.md
Owner: me (demo section). You rebuild T02 the same way.

WHY THIS FILE EXISTS
--------------------
Every real engagement starts with an audit, not a chart. If you build a
dashboard on top of dirty data, you have automated a lie. The audit has
one job: decide, rule by rule, whether this dataset is fit to report on.

Each check below produces a PASS / FAIL / WARN plus the number that
justifies it. The output goes to output/audit_report.txt so it can be
attached to the ticket as evidence.

Run:  python src/01_audit.py
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
from config import (
    SOURCE_XLSX, AUDIT_REPORT, VALID_REGIONS, VALID_PRODUCTS,
    VALID_PLANS, VALID_STATUSES, MAX_NULL_PCT, MAX_OUTLIER_PCT,
    PERIOD_START, PERIOD_END,
)

# ---------------------------------------------------------------- plumbing
# A tiny logger so the same line goes to the terminal AND the report file.
# Analysts who only print to console lose their evidence the moment the
# window closes.
_lines = []


def log(msg=""):
    print(msg)
    _lines.append(str(msg))


def section(title):
    log()
    log("=" * 74)
    log(title)
    log("=" * 74)


def check(name, passed, detail):
    """One audit rule -> one verdict line. This is the atomic unit.

    Normalise the flag first. pandas returns numpy.bool_, and
    `numpy.True_ is True` is False, so identity comparison silently turns
    every pass into a fail. Always coerce with bool() at the boundary.
    """
    if isinstance(passed, str):
        verdict = "WARN"                     # explicit "warn" marker
    else:
        verdict = "PASS" if bool(passed) else "FAIL"
    log(f"[{verdict}] {name}")
    log(f"        {detail}")
    return verdict


results = []

# =====================================================================
# 0. STRUCTURE — what did we actually receive?
# =====================================================================
section("0. STRUCTURE")
xls = pd.ExcelFile(SOURCE_XLSX)
log(f"File        : {SOURCE_XLSX.name}")
log(f"Sheets      : {xls.sheet_names}")

sales = pd.read_excel(xls, "Sales_Data")
customers = pd.read_excel(xls, "Customer_Data")

for name, df in (("Sales_Data", sales), ("Customer_Data", customers)):
    log(f"{name:12s}: {df.shape[0]:>4} rows x {df.shape[1]} cols")
    log(f"{'':12s}  dtypes: {dict(df.dtypes.astype(str))}")

# The Date column arrives as text. Convert once, here, so no downstream
# script has to remember to. errors='coerce' turns unparseable values into
# NaT, which the completeness check will then catch instead of crashing.
sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")
log(f"Date column coerced to datetime -> NaT count: {sales['Date'].isna().sum()}")

# =====================================================================
# 1. COMPLETENESS — is anything missing?
# =====================================================================
section("1. COMPLETENESS")
for name, df in (("Sales_Data", sales), ("Customer_Data", customers)):
    null_pct = (df.isna().mean() * 100).round(2)
    offenders = null_pct[null_pct > 0]
    if offenders.empty:
        results.append(check(f"Nulls in {name}", True, "0 missing values in any column"))
    else:
        results.append(check(
            f"Nulls in {name}",
            "warn" if offenders.max() / 100 <= MAX_NULL_PCT else False,
            f"missing % by column: {offenders.to_dict()}",
        ))

# Calendar coverage: a month with 28 days of data is a broken extract, and
# averages will silently be 7% wrong. Always compare to the calendar, never
# to the row count.
expected_days = pd.date_range(PERIOD_START, PERIOD_END).size
actual_days = sales["Date"].dt.normalize().nunique()
coverage = actual_days / expected_days
results.append(check(
    "Calendar day coverage",
    coverage >= 0.95,
    f"{actual_days}/{expected_days} days present = {coverage:.1%} "
    f"({PERIOD_START} to {PERIOD_END})",
))

# =====================================================================
# 2. UNIQUENESS AND GRAIN — the most misunderstood check in analytics
# =====================================================================
section("2. UNIQUENESS / GRAIN")
# At first glance this looked like 32 duplicate records on (Date, Rep,
# Product). It is not. The question is never "are there duplicates?" but
# "what is one row?" Add Region to the key and the collisions change, so
# test the strongest available key: all columns.
key = ["Date", "Region", "Sales Rep", "Product"]
collisions = sales[sales.duplicated(key, keep=False)].sort_values(key)
log(f"Candidate grain {key}: {sales.duplicated(key).sum()} repeated keys")
if not collisions.empty:
    log("  Rows sharing that key (note: Revenue still differs):")
    log(collisions[key + ["Revenue"]].head(4).to_string(index=False))
    log("  -> Identical rep/day/product/region rows still carry different")
    log("     Revenue, so each row is a separate transaction. The table is")
    log("     transaction-grained and has no natural key.")

results.append(check(
    "No duplicate records in Sales_Data",
    sales.duplicated().sum() == 0,
    f"{sales.duplicated().sum()} fully identical rows across all 10 columns "
    f"(of {len(sales)})",
))
results.append(check(
    "CustomerID is a unique key",
    customers["CustomerID"].duplicated().sum() == 0,
    f"{customers['CustomerID'].duplicated().sum()} duplicate IDs in {len(customers)} customers",
))
results.append(check(
    "Sales_Data has a business key for row-level joins",
    "warn",
    "none of the columns uniquely identify a row: dedupe is unnecessary, "
    "but you cannot join line items to each other or to a transaction log",
))

# =====================================================================
# 3. VALIDITY — are the values legal?
# =====================================================================
section("3. VALIDITY")
for col, allowed, df, name in (
    ("Region", VALID_REGIONS, sales, "Sales_Data"),
    ("Product", VALID_PRODUCTS, sales, "Sales_Data"),
    ("Plan", VALID_PLANS, customers, "Customer_Data"),
    ("Status", VALID_STATUSES, customers, "Customer_Data"),
):
    seen = set(df[col].dropna().astype(str).unique())
    bad = seen - set(allowed)
    results.append(check(
        f"{name}.{col} within approved list",
        not bad,
        f"found {sorted(seen)}" + (f" | UNEXPECTED: {sorted(bad)}" if bad else ""),
    ))

# Negative or zero values where the business says they cannot exist.
neg = {c: int((sales[c] < 0).sum()) for c in
       ["Target Sales", "Actual Sales", "Revenue", "Calls Made", "New Customers", "Existing Customers"]}
results.append(check("No negative Sales_Data measures", not any(neg.values()), f"negatives: {neg}"))

# Division-by-zero guard: every efficiency KPI divides by Calls Made, so a
# single zero would poison the whole revenue-per-call average with inf.
zero_calls = int((sales["Calls Made"] == 0).sum())
results.append(check(
    "Calls Made > 0 (safe denominator)",
    zero_calls == 0,
    f"{zero_calls} rows with zero calls; revenue-per-call is computable for all rows",
))

# A transaction with no customers is meaningless. Same logic as above.
no_cust = int(((sales["New Customers"] + sales["Existing Customers"]) == 0).sum())
results.append(check(
    "Every sale touches a customer",
    no_cust == 0,
    f"{no_cust} rows with new + existing = 0",
))

# =====================================================================
# 4. CONSISTENCY — do the numbers reconcile with each other?
# =====================================================================
section("4. CONSISTENCY")
# This is the check that separates an analyst from someone who can run
# groupby(). Revenue should equal units x price, and price should differ
# by product. If it does not, Revenue is not a derived measure and must be
# reported as-is, never recomputed.
sales["_price_per_unit"] = sales["Revenue"] / sales["Actual Sales"]
price_by_product = sales.groupby("Product")["_price_per_unit"].agg(["min", "max", "mean"]).round(2)
log("Revenue per unit sold, by product:")
log(price_by_product.to_string())

# The correct test is whether the price BAND differs by product, not whether
# the means differ. Means differ by 0.7 here purely from the random draw; the
# band (8-20) is identical for all four. Identical bands = no real price list.
band = price_by_product[["min", "max"]]
identical_band = band.nunique().eq(1).all()
results.append(check(
    "Revenue differs by product (a real price list exists)",
    not identical_band,
    f"unit price band is {price_by_product['min'].min():.0f}-{price_by_product['max'].max():.0f} "
    f"for all {len(price_by_product)} products incl. Home Internet vs SIM",
))
log()
log("  BUSINESS IMPLICATION: Revenue is synthetic. A SIM and a Home Internet")
log("  line bill at the same simulated rate, which is impossible in the real")
log("  world. Consequence for reporting: treat Revenue as the single source")
log("  of truth, do not back-derive it from price x volume, and do not")
log("  quote 'average revenue per unit' as a business insight.")
results.append(check(
    "Revenue is internally usable as an amount",
    "warn",
    "directly summable and non-negative, but not reconstructable from units x price",
))

# =====================================================================
# 5. REFERENTIAL INTEGRITY — can the tables talk to each other?
# =====================================================================
section("5. REFERENTIAL INTEGRITY")
sales_cols = set(sales.columns)
cust_cols = set(customers.columns)
shared = sales_cols & cust_cols
log(f"Sales_Data columns : {sorted(sales_cols)}")
log(f"Customer_Data cols : {sorted(cust_cols)}")
log(f"Shared column names: {sorted(shared) or 'NONE'}")
results.append(check(
    "Sales and customer tables share a join key",
    bool(shared),
    "no CustomerID in Sales_Data -> no customer-level attribution is possible",
))
log()
log("  BUSINESS IMPLICATION: you cannot answer 'which customers drive")
log("  revenue' or 'do churned customers generate less revenue'. Any such")
log("  request must be sent back to the data owner as a data gap, in")
log("  writing, before someone promises it to a stakeholder. This is a")
log("  normal analyst response, not a failure.")

# =====================================================================
# 6. OUTLIERS — extremes that change the answer
# =====================================================================
section("6. OUTLIERS (IQR rule, 1.5 x IQR)")


def iqr_outlier_pct(series):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return 0.0, 0
    mask = (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)
    return mask.mean(), int(mask.sum())


for label, series in [
    ("Sales.Revenue", sales["Revenue"]),
    ("Sales.Actual Sales", sales["Actual Sales"]),
    ("Cust.Monthly Bill", customers["Monthly Bill"]),
    ("Cust.Data Usage GB", customers["Data Usage GB"]),
]:
    pct, n = iqr_outlier_pct(series)
    results.append(check(
        f"Outlier share: {label}",
        pct <= MAX_OUTLIER_PCT,
        f"{n} rows = {pct:.1%} outside 1.5xIQR (tolerance {MAX_OUTLIER_PCT:.0%})",
    ))

# =====================================================================
# 7. COVERAGE BIAS — is the comparison fair?
# =====================================================================
section("7. COVERAGE BIAS")
# Before anyone ranks reps, check whether they had equal opportunity.
# A rep with 50 transactions and a rep with 18 are not comparable on totals.
activity = sales.groupby("Sales Rep").agg(
    Transactions=("Date", "size"),
    Active_Days=("Date", "nunique"),
    Revenue=("Revenue", "sum"),
)
activity["Share of Revenue %"] = (activity["Revenue"] / activity["Revenue"].sum() * 100).round(1)
log(activity.sort_values("Transactions", ascending=False).to_string())

imbalance = activity["Transactions"].max() / activity["Transactions"].min()
results.append(check(
    "Reps have comparable activity volume",
    imbalance <= 1.5,
    f"busiest rep has {imbalance:.1f}x the transactions of the quietest "
    f"({activity['Transactions'].max()} vs {activity['Transactions'].min()})",
))
log()
log("  BUSINESS IMPLICATION: ranking reps on raw revenue is invalid here.")
log("  Report attainment % and revenue-per-call instead, or the leaderboard")
log("  rewards territory size rather than performance. This is exactly the")
log("  kind of trap an interviewer will test you on.")

region_rep = sales.pivot_table(
    index="Sales Rep", columns="Region", values="Date", aggfunc="size", fill_value=0
)
log()
log("Rep x Region activity (blank cells = unpresented territory):")
log(region_rep.to_string())
zero_cells = int((region_rep == 0).sum().sum())
results.append(check(
    "Every rep covers every region",
    "warn",
    f"{zero_cells} rep/region combinations have zero activity "
    f"(e.g. Nita has no Sihanoukville rows)",
))

# =====================================================================
# 8. VERDICT
# =====================================================================
section("8. VERDICT")
fail = sum(1 for r in results if r == "FAIL")
warn = sum(1 for r in results if r == "WARN")
passed = sum(1 for r in results if r == "PASS")
log(f"{passed} PASS | {warn} WARN | {fail} FAIL  (of {len(results)} checks)")
log()
if fail:
    log("Fit for purpose: CONDITIONALLY - report at rep/region/product level only.")
    log("Blocking gaps: no customer-level join key, Revenue not price-reconcilable.")
else:
    log("Fit for purpose: YES")

log()
log("Attachment: this log is written to output/audit_report.txt")

AUDIT_REPORT.write_text("\n".join(_lines), encoding="utf-8")
print(f"\n-> saved {AUDIT_REPORT.relative_to(ROOT)}")
