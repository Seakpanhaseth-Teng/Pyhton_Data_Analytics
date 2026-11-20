# Source Notes — Cellcard Commercial Data Mart

These files are extracts from three systems. They are what the billing and CRM
teams actually send at month-end, not a curated demo.

| File | Source system | Extract mode | Last extract |
|---|---|---|---|
| `fact_sales.csv` | `billing_core` | automated | 2026-07-02 03:10 |
| `fact_targets.csv` | `billing_core` (finance feed) | automated | 2026-07-02 03:12 |
| `fact_customer_month.csv` | `crm` | automated | 2026-07-02 04:05 |
| `dim_customer.csv` | `crm` | automated | 2026-07-02 04:05 |
| `dim_customer_legacy.xlsx` | `crm` | **manual export** | 2026-07-02 08:14 |
| `dim_region.csv` | `master_data` | manual, quarterly | 2026-01-08 |
| `dim_product.csv` | `master_data` | manual, on change | 2026-01-08 |
| `dim_rep.csv` | `master_data` | manual, on change | 2026-06-30 |
| `dim_calendar.csv` | `master_data` | generated | 2026-01-02 |

## Automated vs manually maintained

The automated exports have stable headers and machine-written dates. The manual
ones do not: master data is edited in spreadsheets by Commercial Ops, and the
legacy CRM export is produced by hand from the CRM UI (one sheet per region).

Treat every difference in formatting between automated and manual files as a
process signal, not a bug report.

## Period

2025-01-01 → 2026-06-30. The monthly reporting cycle closes on the second
working day of the following month; this extract was taken on 2026-07-02.

## Privacy

All names, phone numbers and customer identifiers are fabricated. No real
Cellcard subscriber data is present.

## Reproduction

`tools/make_dataset.py` regenerates every file in this folder from seed
`20260630`. Two consecutive runs produce byte-identical CSVs. The generator is a
development tool and is not part of the monthly pipeline.

## Do not open

`answer_key/` at the repository root lists the intentionally planted defects.
It exists so the audit can be graded after the fact, not so the audit can be
shortcut.
