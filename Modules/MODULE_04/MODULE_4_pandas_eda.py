"""
MODULE 4 — Pandas wrangling and EDA solution for CloudMetrics.

"""
from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_4_output"
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_data():

    customers = pd.read_csv(
        DATA / "cleaned_customers.csv"
    )

    subscriptions = pd.read_csv(
        DATA / "cleaned_subscriptions.csv"
    )

    usage = pd.read_csv(
        DATA / "cleaned_usage.csv"
    )

    tickets = pd.read_csv(
        DATA / "cleaned_tickets.csv"
    )

    # Remove duplicates
    customers = customers.drop_duplicates("CustomerID")

    subscriptions = subscriptions.drop_duplicates(
        "SubscriptionID"
    )

    usage = usage.drop_duplicates(
        ["CustomerID", "SubscriptionID", "Month"]
    )

    tickets = tickets.drop_duplicates("TicketID")

    # Convert date columns to datetime
    customers["SignupDate"] = pd.to_datetime(
        customers["SignupDate"],
        errors="coerce"
    )

    subscriptions["StartDate"] = pd.to_datetime(
        subscriptions["StartDate"],
        errors="coerce"
    )

    subscriptions["EndDate"] = pd.to_datetime(
        subscriptions["EndDate"],
        errors="coerce"
    )

    usage["Month"] = pd.to_datetime(
        usage["Month"],
        errors="coerce"
    )

    tickets["OpenedDate"] = pd.to_datetime(
        tickets["OpenedDate"],
        errors="coerce"
    )

    # Convert numeric columns
    for df, cols in [
        (
            subscriptions,
            ["Seats", "MRR"]
        ),
        (
            usage,
            [
                "Logins",
                "ActiveUsers",
                "APICalls",
                "SessionMinutes"
            ]
        ),
        (
            tickets,
            [
                "ResolutionHours",
                "SatisfactionScore"
            ]
        )
    ]:

        for col in cols:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    return customers, subscriptions, usage, tickets

def iqr_outlier_flags(df, column):
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return pd.Series(np.where((df[column] < lower) | (df[column] > upper), "Outlier", "Normal"),
                     index=df.index), lower, upper

def main():
    customers, subscriptions, usage, tickets = clean_data()

    # Aggregate one-to-many tables before merging to avoid row multiplication.
    sub_customer = subscriptions.groupby("CustomerID", as_index=False).agg(
        TotalMRR=("MRR", "sum"),
        TotalSeats=("Seats", "sum"),
        SubscriptionCount=("SubscriptionID", "nunique"),
        PlanName=("PlanName", lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"),
        BillingTerm=("BillingTerm", lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"),
        Status=("Status", lambda s: "Churned" if (s == "Churned").any() else "Active"),
        StartDate=("StartDate", "min"),
        EndDate=("EndDate", "max"),
    )

    usage_customer = usage.groupby("CustomerID", as_index=False).agg(
        TotalLogins=("Logins", "sum"),
        AvgMonthlyLogins=("Logins", "mean"),
        TotalActiveUsers=("ActiveUsers", "sum"),
        AvgActiveUsers=("ActiveUsers", "mean"),
        TotalAPICalls=("APICalls", "sum"),
        TotalSessionMinutes=("SessionMinutes", "sum"),
        UsageMonths=("Month", "nunique"),
        FirstUsageMonth=("Month", "min"),
        LastUsageMonth=("Month", "max"),
    )

    tickets_customer = tickets.groupby("CustomerID", as_index=False).agg(
        TicketCount=("TicketID", "nunique"),
        AvgResolutionHours=("ResolutionHours", "mean"),
        AvgSatisfactionScore=("SatisfactionScore", "mean"),
        FirstTicketDate=("OpenedDate", "min"),
        LastTicketDate=("OpenedDate", "max"),
    )

    # LEFT JOIN justified: customers are the population of interest; retain even
    # customers without subscriptions, usage or tickets.
    customer_view = (
        customers
        .merge(sub_customer, on="CustomerID", how="left")
        .merge(usage_customer, on="CustomerID", how="left")
        .merge(tickets_customer, on="CustomerID", how="left")
    )

    numeric_fill = [
        "TotalMRR", "TotalSeats", "SubscriptionCount", "TotalLogins",
        "AvgMonthlyLogins", "TotalActiveUsers", "AvgActiveUsers", "TotalAPICalls",
        "TotalSessionMinutes", "UsageMonths", "TicketCount",
        "AvgResolutionHours", "AvgSatisfactionScore"
    ]
    for col in numeric_fill:
        customer_view[col] = customer_view[col].fillna(0)

    customer_view["PlanName"] = customer_view["PlanName"].fillna("No Subscription")
    customer_view["Status"] = customer_view["Status"].fillna("No Subscription")
    customer_view["BillingTerm"] = customer_view["BillingTerm"].fillna("Unknown")

    analysis_date = max(
        customers["SignupDate"].max(),
        subscriptions["StartDate"].max(),
        usage["Month"].max(),
        tickets["OpenedDate"].max()
    )
    customer_view["TenureMonths"] = (
        (analysis_date - customer_view["SignupDate"]).dt.days / 30.44
    ).clip(lower=0).round(1)
    customer_view["RevenuePerSeat"] = np.where(
        customer_view["TotalSeats"] > 0,
        customer_view["TotalMRR"] / customer_view["TotalSeats"],
        0
    )
    customer_view["TicketsPerMonth"] = np.where(
        customer_view["TenureMonths"] > 0,
        customer_view["TicketCount"] / customer_view["TenureMonths"],
        customer_view["TicketCount"]
    )
    customer_view["UsageTrend"] = np.where(
        customer_view["TotalLogins"] > customer_view["AvgMonthlyLogins"] * customer_view["UsageMonths"],
        "Increasing",
        np.where(customer_view["TotalLogins"] < customer_view["AvgMonthlyLogins"] * customer_view["UsageMonths"],
                 "Decreasing", "Stable")
    )

    # GroupBy with multiple aggregations.
    for dimension in ["PlanName", "Industry", "Country", "AcquisitionChannel"]:
        grouped = customer_view.groupby(dimension, dropna=False).agg(
            Customers=("CustomerID", "nunique"),
            TotalMRR=("TotalMRR", "sum"),
            AvgMRR=("TotalMRR", "mean"),
            AvgSeats=("TotalSeats", "mean"),
            AvgTickets=("TicketCount", "mean"),
            ChurnedCustomers=("Status", lambda s: (s == "Churned").sum()),
        ).reset_index()
        grouped["ChurnRatePct"] = np.where(
            grouped["Customers"] > 0,
            grouped["ChurnedCustomers"] / grouped["Customers"] * 100, 0
        )
        grouped.to_csv(BASE / "MODULE_4_output" / f"module4_groupby_{dimension.lower()}.csv", index=False)

    # Pivot tables.
    pd.pivot_table(customer_view, index="PlanName", columns="Industry",
                   values="TotalMRR", aggfunc="sum", fill_value=0).to_csv(BASE / "MODULE_4_output" / "module4_pivot_mrr_plan_industry.csv")
    pd.pivot_table(customer_view, index="Country", columns="AcquisitionChannel",
                   values="CustomerID", aggfunc="nunique", fill_value=0).to_csv(BASE / "MODULE_4_output" / "module4_pivot_customers_country_channel.csv")

    # IQR outliers.
    outlier_summary = []
    for col in ["TotalMRR", "TotalSeats", "TotalLogins", "TicketCount", "RevenuePerSeat"]:
        flags, lower, upper = iqr_outlier_flags(customer_view, col)
        customer_view[f"{col}_OutlierFlag"] = flags
        outlier_summary.append({"Metric": col, "LowerBound": lower, "UpperBound": upper,
                                "OutlierCount": int((flags == "Outlier").sum())})
    pd.DataFrame(outlier_summary).to_csv(BASE / "MODULE_4_output"/ "module4_iqr_outlier_summary.csv", index=False)

    # Correlation matrix and plain-English interpretation.
    corr_cols = ["TotalMRR", "TotalSeats", "TotalLogins", "TotalActiveUsers",
                 "TotalAPICalls", "TotalSessionMinutes", "TicketCount",
                 "AvgResolutionHours", "AvgSatisfactionScore", "TenureMonths"]
    corr = customer_view[corr_cols].corr()
    corr.to_csv(BASE / "MODULE_4_output" / "module4_correlation_matrix.csv")

    interpretations = []
    for i, col1 in enumerate(corr.columns):
        for j, col2 in enumerate(corr.columns):
            if j > i:
                value = corr.loc[col1, col2]
                strength = ("very strong" if abs(value) >= .8 else
                            "strong" if abs(value) >= .6 else
                            "moderate" if abs(value) >= .4 else
                            "weak" if abs(value) >= .2 else "very weak")
                direction = "positive" if value > 0 else "negative" if value < 0 else "no"
                interpretations.append({
                    "Variable1": col1, "Variable2": col2, "Correlation": value,
                    "PlainEnglish": f"There is a {strength} {direction} linear relationship between {col1} and {col2}; correlation is not proof of causation."
                })
    pd.DataFrame(interpretations).to_csv(BASE / "MODULE_4_output" / "module4_correlation_interpretations.csv", index=False)

    customer_view.to_csv(BASE / "MODULE_4_output" / "module4_customer_level_view.csv", index=False)
    print("Module 4 complete. Customer-level rows:", len(customer_view))
    print("Join type: LEFT JOIN from customers, after aggregating one-to-many tables.")
    print("Files written: customer view, groupbys, pivots, IQR summary, correlation matrix and interpretations.")

if __name__ == "__main__":
    main()
