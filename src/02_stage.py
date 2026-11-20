"""
TICKET T02 — SQL Staging Layer   [ASSIGNED TO YOU]
==================================================
Read tickets/T02-staging.md first. This file is a skeleton: fill every
TODO, then run it.

Goal: eight CSV/XLSX sources in, eight clean DuckDB tables out. Correct
types, normalised labels, idempotent rebuild, loud failure when a count
or a domain check is wrong.

Run:  python src/02_stage.py
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd
from config import (
    RAW, DB_PATH,
    SALES_UNIQUE, CUSTOMER_MONTH_ROWS, TARGET_ROWS, CUSTOMER_ROWS,
    REP_ROWS, PRODUCT_ROWS, REGION_ROWS, CALENDAR_ROWS, LEGACY_ROWS,
    VALID_REGIONS, VALID_PLANS,
)

# ---------------------------------------------------------------------
# 1. EXTRACT
# ---------------------------------------------------------------------
# TODO: read each RAW[...] path into a DataFrame.
#       Pass dtype=str for every *_id column so pandas does not guess.
#
# TODO: parse the date columns to datetime:
#         sales.txn_date, customers.signup_date, customers.churn_date,
#         reps.hire_date, products.price_effective_from, calendar.date
#       Leave `month` (YYYY-MM text) alone unless you decide to make it a date.
#
# TODO: for the legacy workbook, read all 5 sheets (skiprows=3), keep the
#       sheet name as a column, and drop the "TOTAL:" footer rows.

sales = None          # <- replace
customer_month = None
targets = None
customers = None
reps = None
products = None
regions = None
calendar = None
legacy = None


# ---------------------------------------------------------------------
# 2. CLEAN  (the T01 findings, applied once)
# ---------------------------------------------------------------------
# TODO: dedupe sales on txn_id. PRINT how many rows you dropped; it
#       should be 210.
#
# TODO: TRIM sales.region_name and assert 5 distinct values.
#
# TODO: lower/trim customers.plan_type and assert 3 distinct values.
#
# TODO: add is_valid_lifecycle to customers:
#         signup_date <= 2026-06-30 AND
#         (churn_date IS NULL OR churn_date >= signup_date)
#       Do NOT delete the offending rows.
#
# TODO: flag duplicate phones in the legacy sheet. Do NOT delete them.


# ---------------------------------------------------------------------
# 3. LOAD INTO DUCKDB
# ---------------------------------------------------------------------
# TODO: open a connection to DB_PATH.
#
# TODO: CREATE OR REPLACE TABLE for every staging table, so re-running
#       REPLACES instead of appending. Hint 1 in the ticket.
#
# TODO: cast date columns to DATE in SQL and rename to snake_case where
#       the source uses spaces (the legacy sheet).
#
# TODO: unregister every temporary view when done.

con = None  # <- replace


# ---------------------------------------------------------------------
# 4. VALIDATE  (this is the part people skip, and then trust a broken pack)
# ---------------------------------------------------------------------
# TODO: query the real row counts back out of the database and compare
#       them to the constants imported above.
#
# TODO: raise ValueError with a helpful message on the first mismatch.
#       Do not use bare assert for a pipeline gate.
#
# TODO: re-check the domains inside DuckDB: 5 regions, 3 plans,
#       0 duplicate txn_id.

counts = {}   # <- replace with real counts read back from DuckDB


# ---------------------------------------------------------------------
# 5. REPORT
# ---------------------------------------------------------------------
# TODO: print the DB path, every table name with its row count, and the
#       result of DESCRIBE stg_sales so you can eyeball the types.

print("TODO: not implemented yet")
