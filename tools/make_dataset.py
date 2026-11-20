"""
Synthetic Cellcard dataset generator  (18 months, 2025-01-01 .. 2026-06-30)
==========================================================================
Implements docs/prompts/generate-richer-dataset.md.

Deterministic: one seed, one script, byte-identical CSVs on every run.
Deliberately imperfect: 12 defects are planted and listed only in
answer_key/data_quality_answer_key.md.

Run:  python tools/make_dataset.py

Layout (deviations from the prompt are listed in answer_key/):
  data/raw/   fact_sales.csv, fact_targets.csv, fact_customer_month.csv,
              dim_customer.csv, dim_region.csv, dim_product.csv,
              dim_rep.csv, dim_calendar.csv, dim_customer_legacy.xlsx
  docs/       data_dictionary.md, README_source.md
  answer_key/ data_quality_answer_key.md

This is a DEV tool, not part of the monthly pipeline. The monthly pipeline
starts at src/01_audit.py and never re-generates data.
"""

from __future__ import annotations

import calendar
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import DATA_RAW  # noqa: E402  (path rule: never hard-code)

ANSWER_KEY = ROOT / "answer_key"
DOCS = ROOT / "docs"

SEED = 20260630
START = date(2025, 1, 1)
END = date(2026, 6, 30)
N_CUSTOMERS = 12_000
TARGET_LINES = 150_000

# Scale knob. `units` on subscription products is the number of subscriptions
# in one order (dealer / SME / enterprise bulk). Setting this to (1, 1) gives
# a pure consumer reading and June revenue lands near $0.1M; the prompt's
# acceptance test wants $4M-$9M, so bulk ordering is the coherent reading.
SUBSCRIPTION_UNITS = {"P04": (10, 120), "P05": (10, 120)}
ONE_OFF_UNITS = (1, 20)

# --------------------------------------------------------------- dimensions
REGIONS = [
    # id, name, province, manager, population_weight
    ("R1", "Phnom Penh", "Phnom Penh", "Chea Sophal", 0.45),
    ("R2", "Siem Reap", "Siem Reap", "Lim Sreyneang", 0.15),
    ("R3", "Sihanoukville", "Preah Sihanouk", "Heng Vuthy", 0.15),
    ("R4", "Kampot", "Kampot", "Nou Chanda", 0.15),
    ("R5", "Battambang", "Battambang", "Sok Pisey", 0.10),
]

PRODUCTS = [
    # id, name, category, billing_type, price
    ("P01", "SIM Starter", "Voice", "one_off", 1.50),
    ("P02", "Top-up Bundle", "Voice", "one_off", 0.75),
    ("P03", "Data Pack 5GB", "Data", "one_off", 2.50),
    ("P04", "Postpaid Plan M", "Voice+Data", "monthly", 12.00),
    ("P05", "Home Internet 30Mbps", "Broadband", "monthly", 22.00),
    ("P06", "Enterprise Leased Line", "Broadband", "monthly", 180.00),
]
# price revision: P05 22.00 -> 19.90 on 2026-01-01 (kept as history, not flattened)
PRICE_HISTORY = {
    "P05": [(date(2025, 1, 1), 22.00), (date(2026, 1, 1), 19.90)],
}

REPS = [
    # id, name, region, hire_date, seniority
    ("REP01", "Sokha Chan", "R1", date(2019, 3, 4), "senior"),
    ("REP02", "Dara Kim", "R1", date(2020, 7, 20), "senior"),
    ("REP03", "Sophea Meas", "R1", date(2021, 1, 11), "mid"),
    ("REP04", "Vibol Long", "R1", date(2021, 9, 6), "mid"),
    ("REP05", "Chanthou Pen", "R1", date(2022, 4, 18), "junior"),
    ("REP06", "Bopha Ngin", "R2", date(2020, 11, 2), "senior"),
    ("REP07", "Samnang Chea", "R2", date(2022, 8, 15), "mid"),
    ("REP08", "Theary Ouk", "R3", date(2021, 6, 7), "mid"),
    ("REP09", "Kosal Ly", "R3", date(2023, 5, 22), "junior"),
    ("REP10", "Nita Heng", "R4", date(2020, 2, 10), "senior"),
    ("REP11", "Pheakdey Sun", "R4", date(2025, 7, 1), "junior"),   # mid-period hire
    ("REP12", "Sreyleak Mao", "R5", date(2022, 10, 3), "mid"),
    ("REP13", "Visal Nou", "R5", date(2025, 10, 1), "mid"),        # mid-period hire
    ("REP14", "Chenda Rin", "R2", date(2026, 1, 15), "junior"),    # mid-period hire
]

SENIORITY_MULT = {"junior": 0.70, "mid": 1.00, "senior": 1.35}

# product weights at the start of the period, by region
BASE_MIX = {
    "R1": [0.18, 0.14, 0.16, 0.22, 0.24, 0.06],
    "R2": [0.24, 0.18, 0.18, 0.14, 0.22, 0.04],
    "R3": [0.22, 0.17, 0.17, 0.15, 0.24, 0.05],
    "R4": [0.26, 0.20, 0.18, 0.14, 0.19, 0.03],
    "R5": [0.28, 0.22, 0.18, 0.13, 0.16, 0.03],
}
# relative drift applied linearly over 18 months (t = 0 .. 1)
MIX_DRIFT = [1.00 - 0.30, 1.00 - 0.15, 1.00 + 0.05, 1.00 + 0.10, 1.00 + 0.60, 1.00 + 0.25]

HOLIDAYS: dict[date, str] = {}


def _hol(y, m, d, name):
    HOLIDAYS[date(y, m, d)] = name


for y in (2025, 2026):
    _hol(y, 1, 1, "International New Year")
    _hol(y, 1, 7, "Victory over Genocide Day")
    _hol(y, 3, 8, "International Women's Day")
    _hol(y, 5, 1, "International Labour Day")
    _hol(y, 5, 14, "King's Birthday")
    _hol(y, 6, 18, "Queen Mother's Birthday")
    _hol(y, 9, 24, "Constitution Day")
    _hol(y, 10, 15, "Commemoration of King Father")
    _hol(y, 10, 29, "King's Coronation Day")
    _hol(y, 11, 9, "Independence Day")
    _hol(y, 12, 10, "International Human Rights Day")

for d, n in [(13, "Khmer New Year"), (14, "Khmer New Year"),
             (15, "Khmer New Year"), (16, "Khmer New Year")]:
    _hol(2025, 4, d, n)
    _hol(2026, 4, d, n)
for d in (21, 22, 23):
    _hol(2025, 9, d, "Pchum Ben")
for d in (10, 11, 12):
    _hol(2026, 10, d, "Pchum Ben")
for d in (4, 5, 6):
    _hol(2025, 11, d, "Water Festival")
_hol(2025, 2, 12, "Meak Bochea")
_hol(2026, 3, 3, "Meak Bochea")
_hol(2025, 5, 11, "Visak Bochea")
_hol(2026, 5, 31, "Visak Bochea")

KNY = {(2025, 4, d) for d in range(13, 17)} | {(2026, 4, d) for d in range(13, 17)}
PCHUM = {(2025, 9, d) for d in (21, 22, 23)} | {(2026, 10, d) for d in (10, 11, 12)}
WATER = {(2025, 11, d) for d in (4, 5, 6)}

rng = np.random.default_rng(SEED)
P = len(PRODUCTS)


def month_iter(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield (y, m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def month_start(y, m):
    return date(y, m, 1)


def month_end(y, m):
    return date(y, m, calendar.monthrange(y, m)[1])


def price_on(pid: str, day: date) -> float:
    hist = PRICE_HISTORY.get(pid)
    if not hist:
        return next(p[4] for p in PRODUCTS if p[0] == pid)
    valid = [pr for eff, pr in hist if eff <= day]
    return valid[-1]


# ============================================================ dim_calendar
def build_calendar() -> pd.DataFrame:
    rows = []
    day = START
    while day <= END:
        rows.append({
            "date": day.isoformat(),
            "fiscal_month": day.strftime("%Y-%m"),
            "fiscal_quarter": f"{day.year}-Q{(day.month - 1) // 3 + 1}",
            "fiscal_year": day.year,
            "day_of_week": day.strftime("%A"),
            "is_weekend": int(day.weekday() >= 5),
            "is_public_holiday": int(day in HOLIDAYS),
            "holiday_name": HOLIDAYS.get(day, ""),
        })
        day += timedelta(days=1)
    return pd.DataFrame(rows)


# ============================================================== dim tables
def build_dims():
    region_df = pd.DataFrame(REGIONS, columns=[
        "region_id", "region_name", "province", "region_manager_name", "population_weight"])

    prod_rows = []
    for pid, name, cat, billing, price in PRODUCTS:
        hist = PRICE_HISTORY.get(pid, [(date(2025, 1, 1), price)])
        for eff, pr in hist:
            prod_rows.append({
                "product_id": pid, "product_name": name, "category": cat,
                "billing_type": billing, "unit_price_usd": pr,
                "price_effective_from": eff.isoformat(),
            })
    product_df = pd.DataFrame(prod_rows)
    # DEFECT 11: one price row is missing its effective date (single-price
    # product, so validity is unambiguous for everything except history joins).
    product_df.loc[product_df["product_id"] == "P01", "price_effective_from"] = ""

    rep_rows = []
    for rid, name, region, hire, sen in REPS:
        rep_rows.append({
            "rep_id": rid, "rep_name": name, "region_id": region,
            "hire_date": hire.isoformat(), "seniority": sen,
            "target_multiplier": SENIORITY_MULT[sen],
        })
    rep_df = pd.DataFrame(rep_rows)
    return region_df, product_df, rep_df


# ================================================================ customers
def build_customers(region_df: pd.DataFrame):
    ids = [f"C{i:06d}" for i in range(1, N_CUSTOMERS + 1)]
    region_ids = region_df["region_id"].to_numpy()
    rw = region_df["population_weight"].to_numpy()
    reg = rng.choice(region_ids, size=N_CUSTOMERS, p=rw / rw.sum())

    plan = rng.choice(["prepaid", "postpaid", "broadband"], size=N_CUSTOMERS,
                      p=[0.70, 0.20, 0.10])
    # broadband is an urban product: tilt Phnom Penh / Sihanoukville
    urban = np.isin(reg, ["R1", "R3"])
    flip = urban & (plan == "prepaid") & (rng.random(N_CUSTOMERS) < 0.12)
    plan[flip] = "broadband"

    segment = rng.choice(["consumer", "sme", "enterprise"], size=N_CUSTOMERS,
                         p=[0.85, 0.12, 0.03])
    channel = rng.choice(["retail_store", "dealer", "online", "outbound_tele", "referral"],
                         size=N_CUSTOMERS, p=[0.34, 0.26, 0.16, 0.14, 0.10])

    # 65% pre-existing base, 35% acquired during the period
    signup = []
    span_pre = (date(2024, 12, 31) - date(2022, 1, 1)).days
    span_in = (END - START).days
    for i in range(N_CUSTOMERS):
        if rng.random() < 0.65:
            signup.append(date(2022, 1, 1) + timedelta(days=int(rng.integers(0, span_pre + 1))))
        else:
            signup.append(START + timedelta(days=int(rng.integers(0, span_in + 1))))

    cust = pd.DataFrame({
        "customer_id": ids, "signup_date": signup, "region_id": reg,
        "plan_type": plan, "segment": segment, "acquisition_channel": channel,
    })
    prov = dict(zip(region_df["region_id"], region_df["province"]))
    cust["province"] = cust["region_id"].map(prov)

    # ---- churn simulation (monthly hazard with drivers) -------------------
    churn_date: dict[str, date] = {}
    active = set(ids)
    signup_by_id = dict(zip(ids, signup))
    plan_by_id = dict(zip(ids, plan))
    seg_by_id = dict(zip(ids, segment))
    chan_by_id = dict(zip(ids, channel))

    base_h = {"prepaid": 0.034, "postpaid": 0.018, "broadband": 0.010}
    seg_f = {"consumer": 1.0, "sme": 0.70, "enterprise": 0.30}
    chan_f = {"retail_store": 1.0, "dealer": 0.95, "online": 1.05,
              "outbound_tele": 1.15, "referral": 0.70}

    for y, m in month_iter(START, END):
        ms, me = month_start(y, m), month_end(y, m)
        leaving = []
        for cid in sorted(active):   # sorted: set order is not stable across processes
            sd = signup_by_id[cid]
            if sd > me:
                continue
            tenure_m = (y - sd.year) * 12 + (m - sd.month)
            h = base_h[plan_by_id[cid]] * seg_f[seg_by_id[cid]] * chan_f[chan_by_id[cid]]
            if tenure_m < 12:
                h *= 1.5
            if rng.random() < h:
                leaving.append(cid)
        for cid in leaving:
            sd = signup_by_id[cid]
            first_day = max(ms, sd)      # never churn before signing up
            churn_date[cid] = first_day + timedelta(
                days=int(rng.integers(0, (me - first_day).days + 1)))
            active.discard(cid)

    cust["churn_date"] = [churn_date.get(c, None) for c in cust["customer_id"]]
    cust["status"] = np.where(cust["churn_date"].isna(), "active", "churned")

    # DEFECT 12: 4 customers churn before they signed up.
    # DEFECT 5: 9 customers sign up after the last snapshot date.
    # DEFECT 3: ~2% inconsistent case in plan_type.
    return cust


def inject_customer_defects(cust: pd.DataFrame) -> pd.DataFrame:
    cust = cust.copy()
    bad_churn = rng.choice(len(cust), size=4, replace=False)
    for i in bad_churn:
        sd = cust.at[i, "signup_date"]
        cust.at[i, "churn_date"] = sd - timedelta(days=int(rng.integers(20, 200)))
        cust.at[i, "status"] = "churned"

    future = rng.choice(np.where(cust["churn_date"].isna())[0], size=9, replace=False)
    for i in future:
        cust.at[i, "signup_date"] = date(2026, 8, int(rng.integers(1, 28)))

    n_bad_case = int(round(len(cust) * 0.02))
    bad_case = rng.choice(len(cust), size=n_bad_case, replace=False)
    upper = rng.random(n_bad_case) < 0.5
    vals = cust["plan_type"].astype(str).copy()
    vals.iloc[bad_case[upper]] = vals.iloc[bad_case[upper]].str.upper()
    vals.iloc[bad_case[~upper]] = vals.iloc[bad_case[~upper]].str.title()
    cust["plan_type"] = vals
    return cust


# ===================================================== fact_customer_month
def build_customer_month(cust: pd.DataFrame) -> pd.DataFrame:
    months = list(month_iter(START, END))
    midx = {m: i for i, m in enumerate(months)}

    cid = cust["customer_id"].to_numpy()
    plan = cust["plan_type"].str.lower().to_numpy()
    seg = cust["segment"].to_numpy()
    signup = cust["signup_date"].to_numpy()
    churn = cust["churn_date"].to_numpy()

    recs = []
    for i in range(len(cust)):
        sd, cd = signup[i], churn[i]
        if sd > END:
            continue                       # defect 5 customers: no snapshots
        first = (sd.year, sd.month)
        if first < (START.year, START.month):
            first = (START.year, START.month)
        if cd is not None and cd < sd:
            continue                       # defect 12 customers: no snapshots
        last = (cd.year, cd.month) if cd is not None else (END.year, END.month)
        if last > (END.year, END.month):
            last = (END.year, END.month)
        if (first > last):
            continue
        for y, m in month_iter(month_start(*first), month_end(*last)):
            recs.append((i, y, m, cd is not None and (y, m) == (cd.year, cd.month)))

    idx = np.array([r[0] for r in recs])
    mi = np.array([midx[(r[1], r[2])] for r in recs])
    is_churn_month = np.array([r[3] for r in recs], dtype=int)
    n = len(recs)

    pl = plan[idx]
    sg = seg[idx]

    # Customer-level propensity, drawn once: without it, month-to-month noise
    # swamps the pre-churn decline and the signal is undetectable.
    propensity = rng.lognormal(0.0, 0.35, N_CUSTOMERS)[idx]
    monthly_noise = rng.lognormal(0.0, 0.15, n)

    median_data = np.where(pl == "broadband", 280.0,
                           np.where(pl == "postpaid", 18.0, 4.0))
    median_voice = np.where(pl == "broadband", 25.0,
                            np.where(pl == "postpaid", 280.0, 110.0))
    median_sms = np.where(pl == "broadband", 8.0,
                          np.where(pl == "postpaid", 65.0, 45.0))

    base_data = median_data * propensity * monthly_noise
    base_voice = median_voice * propensity * monthly_noise
    base_sms = median_sms * propensity * monthly_noise

    tenure = mi - np.array([midx[(signup[i].year, signup[i].month)]
                            if signup[i] >= START else 0 for i in idx])
    ramp = np.where(tenure == 0, 0.70, np.where(tenure == 1, 0.85, 1.0))

    # months remaining until churn, for churners
    months_to_churn = np.full(n, 99)
    for k, i in enumerate(idx):
        cd = churn[i]
        if cd is not None:
            months_to_churn[k] = (cd.year - months[mi[k]][0]) * 12 + (cd.month - months[mi[k]][1])

    declining = (months_to_churn <= 1) & (tenure >= 5)
    decay = np.where(months_to_churn == 0, 0.58, np.where(months_to_churn == 1, 0.66, 1.0))

    data_gb = base_data * ramp * np.where(declining, decay, 1.0)
    voice = base_voice * ramp * np.where(declining, decay, 1.0)
    sms = rng.poisson(np.clip(base_sms * ramp * np.where(declining, decay, 1.0), 0, None))

    mrr = np.where(pl == "broadband",
                   rng.uniform(19.9, 38.0, n),
                   np.where(pl == "postpaid", rng.uniform(12.0, 28.0, n),
                            rng.uniform(2.0, 6.5, n)))
    mrr = np.where(sg == "enterprise", mrr * rng.uniform(3.0, 6.0, n), mrr)

    method = np.where(pl == "prepaid",
                      rng.choice(["mobile_wallet", "cash"], n, p=[0.72, 0.28]),
                      np.where(pl == "postpaid",
                               rng.choice(["bank_transfer", "credit_card", "cash"], n,
                                          p=[0.55, 0.30, 0.15]),
                               rng.choice(["bank_transfer", "credit_card"], n,
                                          p=[0.62, 0.38])))

    nps = np.clip(np.round(rng.normal(7.4, 1.6, n)), 1, 10)
    nps = np.where(declining, np.clip(nps - rng.integers(2, 4, n), 1, 10), nps)

    risk = (0.55 * (pl == "prepaid") + 0.25 * (method == "cash")
            + 0.20 * (nps < 5) + 0.15 * declining)
    status = np.empty(n, dtype=object)
    u = rng.random(n)
    status[:] = "paid"
    status[u > 0.82] = "late"
    status[(u > 0.92) & (rng.random(n) < 0.6 + 0.4 * risk)] = "failed"
    status[(u > 0.96)] = "partial"
    status[np.where(declining)[0]] = np.where(
        rng.random(declining.sum()) < 0.35, "late", status[np.where(declining)[0]])

    tickets = rng.poisson(0.35 + 0.9 * risk)

    df = pd.DataFrame({
        "month": [f"{months[i][0]}-{months[i][1]:02d}" for i in mi],
        "customer_id": cid[idx],
        "mrr_usd": np.round(mrr, 2),
        "data_usage_gb": np.round(data_gb, 3),
        "voice_minutes": np.round(voice, 1),
        "sms_count": sms,
        "payment_method": method,
        "payment_status": status,
        "support_tickets_opened": tickets,
        "nps_score": nps.astype(int),
        "is_churned_this_month": is_churn_month,
    })

    # DEFECT 4: 340 null payment methods
    null_idx = rng.choice(len(df), size=340, replace=False)
    df.loc[null_idx, "payment_method"] = None
    return df


# ============================================================== fact_sales
def build_sales(region_df: pd.DataFrame, cust: pd.DataFrame):
    days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    nd = len(days)

    rep_ids = [r[0] for r in REPS]
    rep_region = {r[0]: r[2] for r in REPS}
    rep_hire = {r[0]: r[3] for r in REPS}
    rep_sen = {r[0]: r[4] for r in REPS}
    nr = len(rep_ids)

    # rep skill: drawn once, applied to every month
    skill = rng.normal(1.0, 0.12, nr)
    for i, rid in enumerate(rep_ids):
        if rep_hire[rid] >= date(2025, 7, 1):
            skill[i] *= 0.85           # learning curve, grows in below

    # AR(1) daily noise per rep: correlated activity, not i.i.d.
    noise = np.empty((nr, nd))
    for i in range(nr):
        x = 0.0
        for d in range(nd):
            x = 0.4 * x + rng.normal(0, 0.15)
            noise[i, d] = max(0.35, 1.0 + x)

    region_factor = {r[0]: r[4] for r in REGIONS}
    ridx = {r[0]: i for i, r in enumerate(REGIONS)}

    # customer pool per month (customers with snapshots that month)
    months = list(month_iter(START, END))
    midx = {m: i for i, m in enumerate(months)}
    signup = cust["signup_date"].to_numpy()
    churn = cust["churn_date"].to_numpy()
    cid = cust["customer_id"].to_numpy()
    pool = []
    for y, m in months:
        ms, me = month_start(y, m), month_end(y, m)
        ok = (signup <= me) & np.array([c is None or c >= ms for c in churn])
        pool.append(cid[ok])

    base_rate = 25.0
    total_rep_days = sum(1 for d in days for r in REPS if r[3] <= d)
    base_rate = TARGET_LINES / total_rep_days * 1.04

    # price per product per day
    price = np.array([[price_on(p[0], d) for d in days] for p in PRODUCTS])

    frames = []
    for di, day in enumerate(days):
        t = di / (nd - 1)
        dow = day.weekday()
        key = (day.year, day.month, day.day)

        # ---- day-level seasonality ------------------------------------
        gfac = 1.0
        if key in KNY:
            gfac *= 0.35
        elif day in (date(2025, 4, 11), date(2025, 4, 12), date(2026, 4, 11), date(2026, 4, 12)):
            gfac *= 1.25                # pre-holiday stocking
        if key in PCHUM:
            gfac *= 0.75
        if day.day >= (month_end(day.year, day.month).day - 4):
            gfac *= 1.50 if dow < 5 else 1.20   # payday window

        prod_season = np.ones(P)
        if dow >= 5:
            prod_season *= np.array([0.80, 0.85, 0.82, 0.85, 0.95, 0.15])
        if key in WATER:
            prod_season[0:5] *= 0.85

        # ---- product mix at t -----------------------------------------
        drift = 1.0 + (np.array(MIX_DRIFT) - 1.0) * t
        mix = {r: np.array(BASE_MIX[r]) * drift for r in BASE_MIX}
        for r in mix:
            mix[r] = mix[r] / mix[r].sum()

        month_i = midx[(day.year, day.month)]
        cust_pool = pool[month_i]
        if cust_pool.size == 0:
            continue

        for pi, prod in enumerate(PRODUCTS):
            pid = prod[0]
            act = [i for i, r in enumerate(REPS) if r[3] <= day]
            if not act:
                continue
            act = np.array(act)

            # tourism season for Siem Reap / Sihanoukville
            reg_mult = np.array([
                (1.20 if (day.month in (11, 12, 1, 2) and rep_region[rep_ids[i]] in ("R2", "R3"))
                 else 1.0) for i in act
            ])
            w = np.array([mix[rep_region[rep_ids[i]]][pi] for i in act])

            rates = (base_rate * skill[act] * noise[act, di] * gfac
                     * prod_season[pi] * reg_mult * w)
            rates = np.clip(rates, 0, None)
            n = rng.poisson(rates)
            if n.sum() == 0:
                continue
            rep_pos = np.repeat(act, n)
            cnt = int(n.sum())

            if pid in SUBSCRIPTION_UNITS:
                lo, hi = SUBSCRIPTION_UNITS[pid]
            else:
                lo, hi = ONE_OFF_UNITS
            units = rng.integers(lo, hi + 1, cnt)

            customers = rng.choice(cust_pool, size=cnt, replace=True)
            unit_price = price[pi, di]

            # campaigns: dated windows, no discounting outside them
            disc = np.zeros(cnt)
            if date(2025, 11, 1) <= day <= date(2025, 11, 30) and pid == "P03":
                hit = rng.random(cnt) < 0.25
                disc[hit] = np.round(units[hit] * unit_price
                                     * rng.uniform(0.20, 0.35, hit.sum()), 2)
            if date(2026, 4, 1) <= day <= date(2026, 4, 30) and pid == "P05":
                hit = rng.random(cnt) < 0.40
                disc[hit] = np.round(units[hit] * unit_price * 0.15, 2)

            outcome = rng.choice(["closed_won", "follow_up", "no_answer", "rejected"],
                                 size=cnt, p=[0.55, 0.20, 0.15, 0.10])
            calls = rng.integers(1, 9, cnt)
            calls = np.where(outcome == "closed_won", np.clip(calls, 1, 3),
                             np.where(outcome == "follow_up", np.clip(calls, 2, 4),
                                      np.where(outcome == "no_answer", np.clip(calls, 3, 6),
                                               np.clip(calls, 2, 8))))

            frames.append(pd.DataFrame({
                "txn_date": day.isoformat(),
                "rep_id": [rep_ids[i] for i in rep_pos],
                "region_id": [rep_region[rep_ids[i]] for i in rep_pos],
                "region_name": [REGIONS[ridx[rep_region[rep_ids[i]]]][1] for i in rep_pos],
                "product_id": pid,
                "customer_id": customers,
                "units": units,
                "unit_price_usd": np.round(unit_price, 2),
                "gross_amount_usd": np.round(units * unit_price, 2),
                "discount_usd": disc,
                "net_revenue_usd": np.round(units * unit_price - disc, 2),
                "calls_attempted": calls,
                "call_outcome": outcome,
            }))

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["txn_date", "rep_id", "product_id"], kind="stable").reset_index(drop=True)
    df.insert(0, "txn_id", [f"T{i:08d}" for i in range(1, len(df) + 1)])

    # ---- DEFECT 2: whitespace in region_name (~1.5% of rows) -----------
    n_ws = int(round(len(df) * 0.015))
    ws_idx = rng.choice(len(df), size=n_ws, replace=False)
    pad = rng.choice([" ", "  ", "\t"], size=n_ws)
    df.loc[ws_idx, "region_name"] = df.loc[ws_idx, "region_name"] + pad

    # ---- DEFECT 6: 18 negative net revenue (refund / reversal) ---------
    rev_idx = rng.choice(len(df), size=18, replace=False)
    refund = rng.uniform(25, 150, 18).round(2)
    df.loc[rev_idx, "discount_usd"] = np.round(
        df.loc[rev_idx, "gross_amount_usd"].to_numpy() + refund, 2)
    df.loc[rev_idx, "net_revenue_usd"] = -refund

    # ---- DEFECT 7: ~0.2% orphan customer ids ---------------------------
    n_orph = int(round(len(df) * 0.002))
    orph_idx = rng.choice(len(df), size=n_orph, replace=False)
    df.loc[orph_idx, "customer_id"] = [f"C9{rng.integers(10000, 99999)}" for _ in range(n_orph)]

    # ---- DEFECT 1: 210 exact duplicate rows (same txn_id) --------------
    dup_idx = rng.choice(len(df), size=210, replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)
    df = df.sort_values(["txn_date", "txn_id"], kind="stable").reset_index(drop=True)

    return df


# ============================================================ fact_targets
def build_targets(sales: pd.DataFrame):
    months = list(month_iter(START, END))
    clean = sales.drop_duplicates(subset="txn_id")
    clean = clean[clean["net_revenue_usd"] >= 0]
    realised = (clean.groupby([clean["txn_date"].str[:7], "rep_id", "product_id"])
                ["net_revenue_usd"].sum().rename("rev").reset_index()
                .rename(columns={"txn_date": "month"}))

    rep_ids = [r[0] for r in REPS]
    rep_hire = {r[0]: r[3] for r in REPS}
    avg_price = {p[0]: p[4] for p in PRODUCTS}

    rows = []
    for y, m in months:
        mkey = f"{y}-{m:02d}"
        att = {r: float(np.clip(rng.normal(0.96, 0.12), 0.55, 1.45)) for r in rep_ids}
        if mkey == "2026-06":
            # guarantee a visible spread in the final month
            order = sorted(rep_ids, key=lambda r: att[r])
            att[order[0]] = 0.72
            att[order[-1]] = 1.22
        for r in rep_ids:
            hire = rep_hire[r]
            if hire > month_end(y, m):
                for p in PRODUCTS:
                    rows.append({"month": mkey, "rep_id": r, "product_id": p[0],
                                 "target_revenue_usd": 0.0, "target_units": 0})
                continue
            share = 1.0
            if hire > month_start(y, m):
                days = (month_end(y, m) - hire).days + 1
                share = days / month_end(y, m).day
            sub = realised[(realised["month"] == mkey) & (realised["rep_id"] == r)]
            total = float(sub["rev"].sum())
            if total <= 0:
                for p in PRODUCTS:
                    rows.append({"month": mkey, "rep_id": r, "product_id": p[0],
                                 "target_revenue_usd": 0.0, "target_units": 0})
                continue
            goal = total / att[r]
            raw = {p[0]: float(sub.loc[sub["product_id"] == p[0], "rev"].sum())
                   * float(np.clip(rng.normal(1.0, 0.05), 0.85, 1.15)) for p in PRODUCTS}
            s = sum(raw.values()) or 1.0
            for p in PRODUCTS:
                trev = goal * raw[p[0]] / s
                rows.append({
                    "month": mkey, "rep_id": r, "product_id": p[0],
                    "target_revenue_usd": round(trev, 2),
                    "target_units": int(round(trev / avg_price[p[0]])),
                })
    return pd.DataFrame(rows)


# =========================================================== legacy export
def build_legacy_xlsx(cust: pd.DataFrame, region_df: pd.DataFrame):
    """A genuinely painful manual export: title block, one sheet per province,
    mixed date formats, footer totals, duplicate customers on the same phone."""
    df = cust.copy()
    df["full_name"] = [f"Customer {i:05d}" for i in range(len(df))]
    # unique phone numbers: 09x / 01x + 7 digits
    df["phone"] = [f"0{9 if i % 2 else 1}{i:07d}" for i in range(len(df))]

    # DEFECT 8: 14 duplicate customers, same phone, different customer_id
    dups = df.sample(14, random_state=7).copy()
    dups["customer_id"] = [f"C8{i:05d}" for i in range(14)]
    df = pd.concat([df, dups], ignore_index=True)

    # DEFECT 9: mixed date formats in the same column
    def mixed(d):
        if d is None or (isinstance(d, float) and math.isnan(d)):
            return ""
        d = pd.Timestamp(d).date()
        return d.strftime("%d/%m/%Y") if rng.random() < 0.5 else d.isoformat()

    out = DATA_RAW / "dim_customer_legacy.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        for _, reg in region_df.iterrows():
            part = df[df["province"] == reg["province"]]
            body = pd.DataFrame({
                "Customer ID": part["customer_id"].to_numpy(),
                "Name": part["full_name"].to_numpy(),
                "Phone": part["phone"].to_numpy(),
                "Signup Date": [mixed(d) for d in part["signup_date"]],
                "Plan": part["plan_type"].to_numpy(),
                "Status": part["status"].to_numpy(),
            })
            sheet = reg["region_name"][:31]
            # DEFECT 10: title block rows 1-3, header row 4, footer total
            body.to_excel(xw, sheet_name=sheet, startrow=3, index=False)
            ws = xw.sheets[sheet]
            ws["A1"] = f"CELLCARD CRM - CUSTOMER MASTER ({reg['region_name'].upper()})"
            ws["A2"] = "Extract run: 2026-07-02 08:14  |  Prepared by: CRM Ops"
            ws["A3"] = "CONFIDENTIAL - internal use only"
            footer = body.shape[0] + 5
            ws.cell(row=footer, column=1, value=f"TOTAL: {body.shape[0]} customers")
    return out


# ================================================================ writers
def main():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    ANSWER_KEY.mkdir(exist_ok=True)

    region_df, product_df, rep_df = build_dims()
    cal = build_calendar()

    print("generating customers ...")
    cust = inject_customer_defects(build_customers(region_df))
    cust = cust[["customer_id", "signup_date", "province", "region_id", "plan_type",
                 "segment", "acquisition_channel", "status", "churn_date"]]

    print("generating customer-month snapshots ...")
    cm = build_customer_month(cust)

    print("generating sales ...")
    sales = build_sales(region_df, cust)

    print("generating targets ...")
    targets = build_targets(sales)

    def w(df, name, floats=2):
        path = DATA_RAW / name
        out = df.copy()
        for c in out.columns:
            if out[c].dtype == object:
                out[c] = out[c].map(lambda v: v.isoformat() if hasattr(v, "isoformat") else v)
        out.to_csv(path, index=False, float_format=f"%.{floats}f",
                   date_format="%Y-%m-%d")
        print(f"  {name:28s} {len(out):>8,} rows  {path.stat().st_size/1e6:6.1f} MB")

    w(sales, "fact_sales.csv")
    w(targets, "fact_targets.csv")
    w(cm, "fact_customer_month.csv", floats=3)
    w(cust, "dim_customer.csv")
    w(region_df, "dim_region.csv", floats=2)
    w(product_df, "dim_product.csv")
    w(rep_df, "dim_rep.csv")
    w(cal, "dim_calendar.csv")

    print("generating legacy export ...")
    print("  ", build_legacy_xlsx(cust, region_df))

    june = sales[(sales["txn_date"].str[:7] == "2026-06") & (sales["net_revenue_usd"] >= 0)]
    june = june.drop_duplicates(subset="txn_id")
    print(f"\nJune 2026 revenue: ${june['net_revenue_usd'].sum():,.0f}  "
          f"({len(june):,} unique lines)")
    print(f"Total unique sales lines: {sales['txn_id'].nunique():,}")


if __name__ == "__main__":
    main()
