# Data Dictionary — Cellcard Commercial Data Mart

**Version:** 2.0
**Coverage:** 2025-01-01 → 2026-06-30 (18 fiscal months)
**Currency:** USD, all monetary columns
**Maintained by:** Commercial Analytics (master data: Commercial Ops)
**Status:** vendor extract, monthly refresh

Column types are the types as delivered in the CSV extracts. Nullable = `Y`
means the column can legitimately be empty; it does not mean the extract has
been cleaned.

---

## 1. Tables

| Table | Grain | Rows | Key | Owner | Refresh |
|---|---|---|---|---|---|
| `fact_sales` | one transaction line | 152,604 | `txn_id` | Billing Core | monthly |
| `fact_targets` | month × rep × product | 1,512 | `month, rep_id, product_id` | Commercial Finance | monthly |
| `fact_customer_month` | month × customer (while active) | 145,434 | `month, customer_id` | CRM | monthly |
| `dim_customer` | one customer | 12,000 | `customer_id` | CRM | monthly |
| `dim_rep` | one sales rep | 14 | `rep_id` | Commercial Ops | on change |
| `dim_product` | product × price version | 7 | `product_id, price_effective_from` | Product Marketing | on change |
| `dim_region` | one sales region | 5 | `region_id` | Commercial Ops | on change |
| `dim_calendar` | one calendar day | 546 | `date` | Commercial Analytics | annual |

`fact_targets` has 18 months × 14 reps × 6 products. Reps hired mid-period have
zero targets for months before their hire date.

---

## 2. `fact_sales`

One row per transaction line. `txn_id` is unique in a clean extract.

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `txn_id` | string | N | Transaction identifier assigned by Billing Core | `T` + 8 digits |
| `txn_date` | date | N | Date the transaction posted | 2025-01-01 … 2026-06-30 |
| `rep_id` | string | N | Rep credited with the sale | `dim_rep.rep_id` |
| `region_id` | string | N | Region of the credited rep | `dim_region.region_id` |
| `region_name` | string | N | Region label as printed on the billing extract | `dim_region.region_name` |
| `product_id` | string | N | Product sold | `dim_product.product_id` |
| `customer_id` | string | N | Customer on the order | `dim_customer.customer_id` |
| `units` | integer | N | Subscriptions or units in the order line | ≥ 1 |
| `unit_price_usd` | decimal(10,2) | N | List price per unit valid on `txn_date` | `dim_product` price history |
| `gross_amount_usd` | decimal(12,2) | N | `units × unit_price_usd` | ≥ 0 |
| `discount_usd` | decimal(12,2) | N | Campaign or negotiated discount | ≥ 0 |
| `net_revenue_usd` | decimal(12,2) | N | `gross_amount_usd − discount_usd` | may be negative on reversal |
| `calls_attempted` | integer | N | Outbound call attempts booked against the line | 1–8 |
| `call_outcome` | string | N | Outcome of the last attempt | `closed_won`, `follow_up`, `no_answer`, `rejected` |

**`units` is an order quantity, not a subscriber count.** For `P04` and `P05`
one line can carry a bulk order (dealer, SME, enterprise site). Do not compute
revenue per customer from `fact_sales`; use `fact_customer_month.mrr_usd` for
per-customer economics.

`region_name` is denormalised for the benefit of downstream Excel consumers and
is not guaranteed to be byte-identical to `dim_region.region_name` — join on
`region_id`.

---

## 3. `fact_targets`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `month` | string | N | Fiscal month | `YYYY-MM` |
| `rep_id` | string | N | Rep the target belongs to | `dim_rep.rep_id` |
| `product_id` | string | N | Product the target belongs to | `dim_product.product_id` |
| `target_revenue_usd` | decimal(12,2) | N | Revenue target for the month | ≥ 0; 0 before hire |
| `target_units` | integer | N | Unit target, derived at list price | ≥ 0 |

Attainment = `net revenue ÷ target_revenue_usd`. Targets are owned by
Commercial Finance; analysts do not restate them.

---

## 4. `fact_customer_month`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `month` | string | N | Snapshot month | `YYYY-MM` |
| `customer_id` | string | N | Customer | `dim_customer.customer_id` |
| `mrr_usd` | decimal(10,2) | N | Monthly recurring revenue billed | ≥ 0 |
| `data_usage_gb` | decimal(12,3) | N | Data consumed in the month | ≥ 0 |
| `voice_minutes` | decimal(10,1) | N | Billable voice minutes | ≥ 0 |
| `sms_count` | integer | N | SMS sent | ≥ 0 |
| `payment_method` | string | Y | Method used for the month's bill | `cash`, `bank_transfer`, `credit_card`, `mobile_wallet` |
| `payment_status` | string | N | Settlement state of the bill | `paid`, `late`, `failed`, `partial` |
| `support_tickets_opened` | integer | N | Tickets opened by the customer in the month | ≥ 0 |
| `nps_score` | integer | N | Relationship survey score | 1–10 |
| `is_churned_this_month` | integer | N | 1 if `dim_customer.churn_date` falls in this month | 0, 1 |

A customer has a row for every month from signup (or 2025-01, whichever is
later) through the churn month inclusive, and no rows after it.

---

## 5. `dim_customer`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `customer_id` | string | N | Surrogate customer key | `C` + 6 digits |
| `signup_date` | date | N | Activation date | ≥ 2022-01-01 |
| `province` | string | N | Province of residence | 5 provinces |
| `region_id` | string | N | Sales region | `dim_region.region_id` |
| `plan_type` | string | N | Commercial plan family | `prepaid`, `postpaid`, `broadband` |
| `segment` | string | N | Customer segment | `consumer`, `sme`, `enterprise` |
| `acquisition_channel` | string | N | Channel that acquired the customer | `retail_store`, `dealer`, `online`, `outbound_tele`, `referral` |
| `status` | string | N | Current lifecycle state | `active`, `churned` |
| `churn_date` | date | Y | Date the customer left; null iff active | ≥ `signup_date` |

`churn_date` null ⇔ `status = 'active'`.

---

## 6. `dim_rep`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `rep_id` | string | N | Rep key | `REP` + 2 digits |
| `rep_name` | string | N | Display name | — |
| `region_id` | string | N | Home region | `dim_region.region_id` |
| `hire_date` | date | N | First day of employment | ≥ 2019-01-01 |
| `seniority` | string | N | Band | `junior`, `mid`, `senior` |
| `target_multiplier` | decimal(4,2) | N | Target load relative to band baseline | 0.70 / 1.00 / 1.35 |

No sales exist for a rep before `hire_date`; targets are zero for those months.

---

## 7. `dim_product`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `product_id` | string | N | Product key | `P01`–`P06` |
| `product_name` | string | N | Product name | 6 products |
| `category` | string | N | Category | `Voice`, `Data`, `Voice+Data`, `Broadband` |
| `billing_type` | string | N | Revenue recognition | `one_off`, `monthly` |
| `unit_price_usd` | decimal(10,2) | N | List price from `price_effective_from` | > 0 |
| `price_effective_from` | date | Y | First day the price applies | null only for never-revised products |

Price history is versioned, not flattened: `P05` has two rows (22.00 from
2025-01-01, 19.90 from 2026-01-01). Join `fact_sales.unit_price_usd` against the
row where `price_effective_from` is the latest date ≤ `txn_date`.

---

## 8. `dim_region`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `region_id` | string | N | Region key | `R1`–`R5` |
| `region_name` | string | N | Region label | 5 regions |
| `province` | string | N | Province covered | 5 provinces |
| `region_manager_name` | string | N | Regional sales manager | — |
| `population_weight` | decimal(4,2) | N | Share of national addressable base | sums to 1.00 |

---

## 9. `dim_calendar`

| Column | Type | Null | Definition | Valid values |
|---|---|---|---|---|
| `date` | date | N | Calendar day | 2025-01-01 … 2026-06-30 |
| `fiscal_month` | string | N | Fiscal month | `YYYY-MM` |
| `fiscal_quarter` | string | N | Fiscal quarter | `YYYY-Qn` |
| `fiscal_year` | integer | N | Fiscal year | 2025, 2026 |
| `day_of_week` | string | N | Weekday name | Monday … Sunday |
| `is_weekend` | integer | N | 1 for Saturday/Sunday | 0, 1 |
| `is_public_holiday` | integer | N | 1 for a Cambodian public holiday | 0, 1 |
| `holiday_name` | string | Y | Holiday name when `is_public_holiday = 1` | — |

---

## 10. `dim_customer_legacy.xlsx`

Manual CRM export retained for reconciliation only. One sheet per region.

- Rows 1–3 are a title block; **row 4 is the header**.
- The last row of each sheet is a `TOTAL: N customers` footer, not data.
- Columns: `Customer ID`, `Name`, `Phone`, `Signup Date`, `Plan`, `Status`.
- `Signup Date` mixes `DD/MM/YYYY` and `YYYY-MM-DD` in the same column.
- `Phone` is the only near-key; customer IDs in this file are not guaranteed to
  match `dim_customer.customer_id`.

Do not load this file with a default `read_excel`. Use `header=3` (0-based
`skiprows=3`) and drop the footer row.

---

## 11. Measures

| Measure | Formula | Owner |
|---|---|---|
| Net revenue | `Σ net_revenue_usd` on unique `txn_id` | Billing Core |
| Gross revenue | `Σ gross_amount_usd` | Billing Core |
| Discount rate | `Σ discount_usd ÷ Σ gross_amount_usd` | Commercial Finance |
| Attainment % | `net revenue ÷ target_revenue_usd` | Commercial Finance |
| Revenue per call | `net revenue ÷ Σ calls_attempted` | Commercial Analytics |
| MRR | `Σ mrr_usd` in `fact_customer_month` | CRM |
| Churn rate | churned in month ÷ active at month start | CRM |
| NPS | mean `nps_score` | CRM |
| ARPU | `MRR ÷ active customers` | Commercial Analytics |

Report revenue at **rep × region × product × month**. Any finer grain needs a
written data request.
