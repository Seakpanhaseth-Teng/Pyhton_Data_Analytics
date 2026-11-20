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

SOURCE_XLSX = DATA_RAW / "Cellcard_Interview_Practice_Dataset.xlsx"
DB_PATH = DATA_CLEAN / "cellcard.duckdb"
EXCEL_PACK = OUTPUT / "Cellcard_MIS_June2026.xlsx"
DASHBOARD = OUTPUT / "dashboard.html"
AUDIT_REPORT = OUTPUT / "audit_report.txt"

# ------------------------------------------------------------ reporting
# The reporting period this engagement covers. Everything downstream
# assumes one month of data; if the source changes to a quarter, this
# is the knob you turn.
PERIOD_LABEL = "June 2026"
PERIOD_START = "2026-06-01"
PERIOD_END = "2026-06-30"

# ----------------------------------------------------------- domains
# Values the business says are valid. Anything outside these is a data
# quality exception, not a new category. Never let a typo silently
# create a new region in a chart.
VALID_REGIONS = ["Phnom Penh", "Siem Reap", "Sihanoukville", "Kampot", "Battambang"]
VALID_PRODUCTS = ["SIM", "Data Pack", "Home Internet", "Postpaid"]
VALID_PLANS = ["Prepaid", "Postpaid"]
VALID_STATUSES = ["Active", "Inactive"]

# ------------------------------------------------------------ thresholds
# Used by the audit to decide pass/fail on each rule. Tune with the
# business, do not tune to make the report look green.
MAX_NULL_PCT = 0.0          # telecom billing data: zero tolerance
MIN_DAY_COVERAGE = 0.95     # at least 95% of calendar days present
MAX_OUTLIER_PCT = 0.05      # >5% outliers means the metric is misdefined

for _d in (DATA_RAW, DATA_CLEAN, OUTPUT, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)
