"""
TICKET T02 — SQL Staging Layer   [ASSIGNED TO YOU]
==================================================
Read tickets/T02-staging.md first. This file is a skeleton: fill every
TODO, then run it.

Goal: Excel in, DuckDB out. Two clean tables, correct types, idempotent
rebuild, loud failure if the source is wrong.

Run:  python src/02_stage.py
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd
from config import SOURCE_XLSX, DB_PATH

EXPECTED_SALES_ROWS = 200
EXPECTED_CUSTOMER_ROWS = 150

# ---------------------------------------------------------------------
# 1. EXTRACT
# ---------------------------------------------------------------------
# TODO: read both sheets ("Sales_Data", "Customer_Data") from SOURCE_XLSX
#       into two DataFrames.
#
# TODO: cast the Date column to datetime.

sales = None       # <- replace
customers = None   # <- replace


# ---------------------------------------------------------------------
# 2. LOAD INTO DUCKDB
# ---------------------------------------------------------------------
# TODO: open a connection to DB_PATH.
#
# TODO: create stg_sales and stg_customers so that re-running this script
#       REPLACES them instead of appending. Hint 1 in the ticket.
#
# TODO: rename columns to snake_case and give Date the SQL type DATE.
#       Hint 2 in the ticket.
#
# TODO: unregister any temporary views when done.

con = None  # <- replace


# ---------------------------------------------------------------------
# 3. VALIDATE  (this is the part people skip, and then trust a broken pack)
# ---------------------------------------------------------------------
# TODO: query the real row counts back out of the database.
# TODO: raise ValueError with a helpful message if either count is wrong.

n_sales = 0
n_customers = 0


# ---------------------------------------------------------------------
# 4. REPORT
# ---------------------------------------------------------------------
# TODO: print the DB path, both table names, both row counts, and the
#       result of DESCRIBE stg_sales so you can eyeball the types.

print("TODO: not implemented yet")
