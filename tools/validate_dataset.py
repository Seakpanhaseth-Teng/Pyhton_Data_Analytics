"""
Acceptance tests for the generated Cellcard dataset.
Implements the 10 tests in docs/prompts/generate-richer-dataset.md §7.

Run:  python tools/validate_dataset.py
Exit code 0 = all pass, 1 = at least one fail.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import DATA_RAW  # noqa: E402

PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2026, 6, 30)
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {detail}")


def load(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / name, **kw)


def month_diff(a: str, b: str) -> int:
    ay, am = int(a[:4]), int(a[5:7])
    by, bm = int(b[:4]), int(b[5:7])
    return (ay - by) * 12 + (am - bm)


def main() -> int:
    sales = load("fact_sales.csv", dtype={"txn_id": str, "customer_id": str})
    cm = load("fact_customer_month.csv", dtype={"customer_id": str})
    cust = load("dim_customer.csv", dtype={"customer_id": str})
    prod = load("dim_product.csv", dtype={"product_id": str}, keep_default_na=False)
    rep = load("dim_rep.csv", dtype={"rep_id": str})
    tgt = load("fact_targets.csv", dtype={"rep_id": str})

    sales["txn_date"] = pd.to_datetime(sales["txn_date"])
    # dedupe the planted duplicates for every revenue-based test
    clean = sales.drop_duplicates(subset="txn_id")

    # ---------------------------------------------------------------- 1
    rev = clean[clean["net_revenue_usd"] >= 0]
    calc = (rev["units"] * rev["unit_price_usd"] - rev["discount_usd"]).round(2)
    bad = (calc - rev["net_revenue_usd"]).abs() > 0.011
    reversals = int((clean["net_revenue_usd"] < 0).sum())
    check("1  net_revenue = units*price - discount (2dp)",
          int(bad.sum()) == 0 and reversals == 18,
          f"{int(bad.sum())} mismatching rows; {reversals} planted reversals (expected 18)")

    # ---------------------------------------------------------------- 2
    hire = dict(zip(rep["rep_id"], pd.to_datetime(rep["hire_date"])))
    h = clean["rep_id"].map(hire)
    early = int((clean["txn_date"] < h).sum())
    outside = int(((clean["txn_date"].dt.date < PERIOD_START) |
                   (clean["txn_date"].dt.date > PERIOD_END)).sum())
    check("2  every txn_date inside rep hire window and period",
          early == 0 and outside == 0,
          f"{early} rows before hire date; {outside} rows outside the period")

    # ---------------------------------------------------------------- 3
    price_rows = prod.copy()
    price_rows["eff"] = price_rows["price_effective_from"].replace("", "1900-01-01")
    price_rows["eff"] = pd.to_datetime(price_rows["eff"])
    lookup = {}
    for pid, grp in price_rows.groupby("product_id"):
        lookup[pid] = list(zip(grp["eff"], grp["unit_price_usd"]))

    def valid_price(row):
        hist = sorted([x for x in lookup[row.product_id] if x[0] <= row.txn_date])
        return hist[-1][1] if hist else np.nan

    want = clean.apply(valid_price, axis=1)
    mism = int(((want - clean["unit_price_usd"]).abs() > 0.011).sum())
    check("3  unit_price matches the price valid on txn_date",
          mism == 0, f"{mism} rows priced off the price list")

    # ---------------------------------------------------------------- 4
    months_by_cust = cm.groupby("customer_id")["month"].apply(sorted).to_dict()
    churn = dict(zip(cust["customer_id"], cust["churn_date"]))
    signup = dict(zip(cust["customer_id"], cust["signup_date"]))
    after_churn = 0
    gaps = 0
    for cid, months in months_by_cust.items():
        cd = churn.get(cid)
        if isinstance(cd, str):
            if any(m > cd[:7] for m in months):
                after_churn += 1
        if len(months) > 1 and any(month_diff(months[i + 1], months[i]) != 1
                                   for i in range(len(months) - 1)):
            gaps += 1
    check("4  snapshots contiguous, none after churn month",
          after_churn == 0 and gaps == 0,
          f"{after_churn} customers with rows after churn; {gaps} customers with month gaps")

    # ---------------------------------------------------------------- 5
    june = clean[(clean["txn_date"].dt.strftime("%Y-%m") == "2026-06")
                 & (clean["net_revenue_usd"] >= 0)]
    june_rev = float(june["net_revenue_usd"].sum())
    check("5  June 2026 revenue between $4M and $9M",
          4_000_000 <= june_rev <= 9_000_000,
          f"${june_rev:,.0f} across {len(june):,} unique lines")

    # ---------------------------------------------------------------- 6
    cust["signup_date"] = pd.to_datetime(cust["signup_date"])
    cust["churn_date"] = pd.to_datetime(cust["churn_date"])
    months = sorted(cm["month"].unique())
    rates = []
    for m in months:
        ms = pd.Timestamp(m + "-01")
        me = ms + pd.offsets.MonthEnd(0)
        active = ((cust["signup_date"] <= me) &
                  (cust["churn_date"].isna() | (cust["churn_date"] >= ms))).sum()
        left = (cust["churn_date"].dt.strftime("%Y-%m") == m).sum()
        rates.append(left / active if active else 0.0)
    rates = np.array(rates)
    share = float(((rates >= 0.02) & (rates <= 0.04)).mean())
    check("6  monthly churn 2-4% in >=80% of months",
          share >= 0.80,
          f"{share:.0%} of months in band; range {rates.min():.2%}-{rates.max():.2%}")

    # ---------------------------------------------------------------- 7
    daily = clean[clean["net_revenue_usd"] >= 0].groupby(
        clean["txn_date"].dt.date)["net_revenue_usd"].sum()
    kny = date(2026, 4, 14)
    trail = [daily.get(kny - pd.Timedelta(days=i).to_pytimedelta(), 0) for i in range(1, 8)]
    drop = 1 - daily.get(kny, 0) / (sum(trail) / 7)
    check("7  Khmer New Year day >=50% below trailing 7-day average",
          drop >= 0.50, f"2026-04-14 is {drop:.0%} below the trailing average")

    # ---------------------------------------------------------------- 8
    disc_rate = clean.groupby(clean["txn_date"].dt.strftime("%Y-%m")).apply(
        lambda g: (g["discount_usd"] > 0).mean(), include_groups=False)
    blitz = disc_rate.get("2025-11", 0)
    kny_promo = disc_rate.get("2026-04", 0)
    other = disc_rate.drop(["2025-11", "2026-04"]).mean()
    check("8  campaign months discount more than normal months",
          blitz > other * 1.5 and kny_promo > other * 1.5,
          f"Nov-25 {blitz:.1%}, Apr-26 {kny_promo:.1%}, other months {other:.1%}")

    # ---------------------------------------------------------------- 9
    last = tgt[tgt["month"] == "2026-06"].groupby("rep_id")[
        ["target_revenue_usd"]].sum().join(
        clean[clean["txn_date"].dt.strftime("%Y-%m") == "2026-06"]
        .groupby("rep_id")["net_revenue_usd"].sum())
    last["att"] = last["net_revenue_usd"] / last["target_revenue_usd"].replace(0, np.nan)
    check("9  final month has a rep <80% and a rep >115%",
          bool((last["att"] < 0.80).any() and (last["att"] > 1.15).any()),
          f"attainment range {last['att'].min():.0%}-{last['att'].max():.0%} "
          f"across {last['att'].notna().sum()} reps")

    # ---------------------------------------------------------------- 10
    cm["month_dt"] = pd.to_datetime(cm["month"] + "-01")
    usable = 0
    ok = 0
    for cid, g in cm.groupby("customer_id"):
        cd = churn.get(cid)
        if not isinstance(cd, str) or len(g) < 6:
            continue
        usable += 1
        g = g.sort_values("month")
        baseline = g["data_usage_gb"].iloc[:-2].median()
        pre = g["data_usage_gb"].iloc[-2:].mean()
        if baseline > 0 and pre <= baseline * 0.80:
            ok += 1
    share = ok / usable if usable else 0
    check("10 pre-churn usage >=20% below the customer's own baseline",
          share >= 0.80,
          f"{share:.0%} of {usable:,} churners with >=6 months show the decline")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
