"""
Central configuration for the Cellcard June 2026 MIS engagement.

Rule of thumb: no script in this repo hard-codes a file path. Everything
imports from here. When a path changes, it changes in exactly one place.

    import sys, pathlib
    ROOT = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "src"))
    from config import SALES_SHEET, DB_PATH
"""

from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
OUTPUT = ROOT / "output"
FIGURES = OUTPUT / "figures"

SOURCE_XLSX = DATA_RAW / "Cellcard_Interview_Practice_Dataset.xlsx"   # v1 practice file, superseded
DB_PATH = DATA_CLEAN / "cellcard.duckdb"
EXCEL_PACK = OUTPUT / "Cellcard_MIS_June2026.xlsx"
DASHBOARD = OUTPUT / "dashboard.html"
AUDIT_REPORT = OUTPUT / "audit_report.txt"

# ------------------------------------------------- generated dataset (v2)
# Built by tools/make_dataset.py. This is the source of truth from T01 onward.
RAW = {
    "sales": DATA_RAW / "fact_sales.csv",
    "targets": DATA_RAW / "fact_targets.csv",
    "customer_month": DATA_RAW / "fact_customer_month.csv",
    "customers": DATA_RAW / "dim_customer.csv",
    "reps": DATA_RAW / "dim_rep.csv",
    "products": DATA_RAW / "dim_product.csv",
    "regions": DATA_RAW / "dim_region.csv",
    "calendar": DATA_RAW / "dim_calendar.csv",
    "customer_legacy": DATA_RAW / "dim_customer_legacy.xlsx",
}

# Row counts as delivered. stg_sales must deduplicate txn_id, so its expected
# count is SALES_UNIQUE, not SALES_ROWS.
SALES_ROWS = 152_604          # raw rows, incl. 210 planted duplicates
SALES_UNIQUE = 152_394        # unique txn_id
CUSTOMER_ROWS = 12_000
CUSTOMER_MONTH_ROWS = 145_434
TARGET_ROWS = 1_512
REP_ROWS = 14
PRODUCT_ROWS = 7              # 6 products; P05 has two price versions
REGION_ROWS = 5
CALENDAR_ROWS = 546
LEGACY_ROWS = 12_014          # 12,000 customers + 14 duplicate-phone rows


# ------------------------------------------------------------ reporting
# The reporting period this engagement covers. Everything downstream
# assumes one month of data; if the source changes to a quarter, this
# is the knob you turn.
PERIOD_LABEL = "June 2026"
PERIOD_START = "2026-06-01"
PERIOD_END = "2026-06-30"

# The extract itself spans 18 months; the reporting period is one month of it.
DATA_START = "2025-01-01"
DATA_END = "2026-06-30"

# ----------------------------------------------------------- domains
# Values the business says are valid. Anything outside these is a data
# quality exception, not a new category. Never let a typo silently
# create a new region in a chart.
VALID_REGIONS = ["Phnom Penh", "Siem Reap", "Sihanoukville", "Kampot", "Battambang"]
VALID_PRODUCTS = [
    "SIM Starter", "Top-up Bundle", "Data Pack 5GB",
    "Postpaid Plan M", "Home Internet 30Mbps", "Enterprise Leased Line",
]
VALID_PLANS = ["prepaid", "postpaid", "broadband"]
VALID_STATUSES = ["active", "churned"]
VALID_SEGMENTS = ["consumer", "sme", "enterprise"]
VALID_CHANNELS = ["retail_store", "dealer", "online", "outbound_tele", "referral"]
VALID_PAYMENT_METHODS = ["cash", "bank_transfer", "credit_card", "mobile_wallet"]
VALID_PAYMENT_STATUSES = ["paid", "late", "failed", "partial"]
VALID_OUTCOMES = ["closed_won", "follow_up", "no_answer", "rejected"]

# ------------------------------------------------------------ thresholds
# Used by the audit to decide pass/fail on each rule. Tune with the
# business, do not tune to make the report look green.
MAX_NULL_PCT = 0.0          # telecom billing data: zero tolerance
MIN_DAY_COVERAGE = 0.95     # at least 95% of calendar days present
MAX_OUTLIER_PCT = 0.05      # >5% outliers means the metric is misdefined

for _d in (DATA_RAW, DATA_CLEAN, OUTPUT, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)
