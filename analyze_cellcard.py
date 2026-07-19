"""
Cellcard Interview Practice Dataset — Analysis
================================================
Run this top to bottom. Each section is a self-contained question.
Read the comments BEFORE the code — they explain the "why", not just the "what".

Requires: pandas, matplotlib (pip install pandas matplotlib openpyxl --break-system-packages)
"""

import pandas as pd
import matplotlib.pyplot as plt

FILE = "Cellcard_Interview_Practice_Dataset.xlsx"  # put this script next to the file, or use full path

# -----------------------------------------------------------------
# 0. LOAD THE DATA
# -----------------------------------------------------------------
# An Excel file can have multiple sheets. pd.ExcelFile lets us see
# what sheets exist before loading them.
xls = pd.ExcelFile(FILE)
print("Sheets found:", xls.sheet_names)

sales = pd.read_excel(xls, "Sales_Data")
customers = pd.read_excel(xls, "Customer_Data")

# Always a good habit: peek at shape + dtypes before analysing anything.
print("\nSales_Data shape:", sales.shape)
print(sales.dtypes)
print("\nCustomer_Data shape:", customers.shape)
print(customers.dtypes)

# Date column comes in as a string here — convert it to a real datetime
# so we can sort/group by week, month, etc.
sales["Date"] = pd.to_datetime(sales["Date"])


# -----------------------------------------------------------------
# 1. TARGET vs ACTUAL SALES — who/what is over- or under-performing?
# -----------------------------------------------------------------
# "Attainment %" = actual / target. This is a classic sales KPI.
sales["Attainment %"] = (sales["Actual Sales"] / sales["Target Sales"] * 100).round(1)

print("\n--- Attainment % by Sales Rep ---")
rep_perf = (
    sales.groupby("Sales Rep")
    .agg(
        Target=("Target Sales", "sum"),
        Actual=("Actual Sales", "sum"),
        Revenue=("Revenue", "sum"),
    )
)
rep_perf["Attainment %"] = (rep_perf["Actual"] / rep_perf["Target"] * 100).round(1)
rep_perf = rep_perf.sort_values("Attainment %", ascending=False)
print(rep_perf)

print("\n--- Attainment % by Region ---")
region_perf = (
    sales.groupby("Region")
    .agg(Target=("Target Sales", "sum"), Actual=("Actual Sales", "sum"))
)
region_perf["Attainment %"] = (region_perf["Actual"] / region_perf["Target"] * 100).round(1)
print(region_perf.sort_values("Attainment %", ascending=False))

print("\n--- Attainment % by Product ---")
product_perf = (
    sales.groupby("Product")
    .agg(Target=("Target Sales", "sum"), Actual=("Actual Sales", "sum"))
)
product_perf["Attainment %"] = (product_perf["Actual"] / product_perf["Target"] * 100).round(1)
print(product_perf.sort_values("Attainment %", ascending=False))


# -----------------------------------------------------------------
# 2. REVENUE TRENDS OVER TIME
# -----------------------------------------------------------------
# Group by week to smooth out daily noise. dt.to_period("W") buckets
# dates into weekly periods.
weekly_revenue = sales.groupby(sales["Date"].dt.to_period("W"))["Revenue"].sum()
print("\n--- Weekly Revenue ---")
print(weekly_revenue)

plt.figure(figsize=(9, 4))
weekly_revenue.plot(kind="line", marker="o")
plt.title("Weekly Revenue Trend")
plt.ylabel("Revenue")
plt.xlabel("Week")
plt.tight_layout()
plt.savefig("weekly_revenue_trend.png")
plt.close()
print("Saved chart: weekly_revenue_trend.png")


# -----------------------------------------------------------------
# 3. SALES EFFICIENCY — revenue generated per call made
# -----------------------------------------------------------------
# More calls doesn't always mean more revenue. This ratio shows who
# converts effort into money most efficiently.
sales["Revenue per Call"] = (sales["Revenue"] / sales["Calls Made"]).round(2)

efficiency = (
    sales.groupby("Sales Rep")
    .agg(Total_Revenue=("Revenue", "sum"), Total_Calls=("Calls Made", "sum"))
)
efficiency["Revenue per Call"] = (efficiency["Total_Revenue"] / efficiency["Total_Calls"]).round(2)
print("\n--- Revenue per Call by Sales Rep (efficiency ranking) ---")
print(efficiency.sort_values("Revenue per Call", ascending=False))


# -----------------------------------------------------------------
# 4. NEW vs EXISTING CUSTOMER MIX
# -----------------------------------------------------------------
# Are reps mostly farming existing accounts, or hunting new ones?
sales["New Customer %"] = (
    sales["New Customers"] / (sales["New Customers"] + sales["Existing Customers"]) * 100
).round(1)

mix = sales.groupby("Region")[["New Customers", "Existing Customers"]].sum()
mix["New %"] = (mix["New Customers"] / (mix["New Customers"] + mix["Existing Customers"]) * 100).round(1)
print("\n--- New vs Existing Customer Mix by Region ---")
print(mix)


# -----------------------------------------------------------------
# 5. CHURN — Active vs Inactive customers
# -----------------------------------------------------------------
churn_overall = customers["Status"].value_counts(normalize=True).mul(100).round(1)
print("\n--- Overall Status Split (%) ---")
print(churn_overall)

churn_by_province = (
    customers.groupby("Province")["Status"]
    .value_counts(normalize=True)
    .mul(100)
    .round(1)
    .unstack()
)
print("\n--- Active/Inactive % by Province ---")
print(churn_by_province)

churn_by_plan = (
    customers.groupby("Plan")["Status"]
    .value_counts(normalize=True)
    .mul(100)
    .round(1)
    .unstack()
)
print("\n--- Active/Inactive % by Plan ---")
print(churn_by_plan)


# -----------------------------------------------------------------
# 6. PREPAID vs POSTPAID — billing & usage comparison
# -----------------------------------------------------------------
plan_summary = customers.groupby("Plan").agg(
    Avg_Monthly_Bill=("Monthly Bill", "mean"),
    Avg_Data_Usage_GB=("Data Usage GB", "mean"),
    Avg_Voice_Minutes=("Voice Minutes", "mean"),
    Customers=("CustomerID", "count"),
).round(1)
print("\n--- Prepaid vs Postpaid Summary ---")
print(plan_summary)


# -----------------------------------------------------------------
# 7. DOES USAGE RELATE TO CHURN?
# -----------------------------------------------------------------
# Compare average usage for Active vs Inactive customers. If Inactive
# customers show much lower usage before leaving, that's an early
# warning signal a business could act on.
usage_vs_status = customers.groupby("Status").agg(
    Avg_Data_Usage_GB=("Data Usage GB", "mean"),
    Avg_Voice_Minutes=("Voice Minutes", "mean"),
    Avg_Monthly_Bill=("Monthly Bill", "mean"),
).round(1)
print("\n--- Usage & Billing: Active vs Inactive ---")
print(usage_vs_status)


# -----------------------------------------------------------------
# 8. QUICK VISUAL SUMMARY (bar charts)
# -----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

rep_perf["Attainment %"].plot(kind="bar", ax=axes[0], color="steelblue")
axes[0].set_title("Sales Attainment % by Rep")
axes[0].axhline(100, color="red", linestyle="--", linewidth=1)

churn_overall.plot(kind="bar", ax=axes[1], color="darkorange")
axes[1].set_title("Customer Status Split (%)")

plt.tight_layout()
plt.savefig("summary_charts.png")
plt.close()
print("\nSaved chart: summary_charts.png")

print("\nDone. Check the printed tables above and the two PNG charts saved alongside this script.")
