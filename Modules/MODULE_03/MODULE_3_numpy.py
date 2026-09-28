"""
 MODULE 3 — NumPy solution for the CloudMetrics SaaS dataset.

"""

from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_3_output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Z-SCORE FUNCTION
# ============================================================

def z_score(values):
    values = np.asarray(values, dtype=float)

    std = values.std()

    if std != 0:
        return (values - values.mean()) / std

    return np.zeros_like(values)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load cleaned Module 2 data
    # --------------------------------------------------------

    subscriptions = pd.read_csv(
        BASE / "cleaned_output" / "cleaned_subscriptions.csv"
    )

    usage = pd.read_csv(
        BASE / "cleaned_output" / "cleaned_usage.csv"
    )


    # --------------------------------------------------------
    # Convert required metrics to NumPy arrays
    # --------------------------------------------------------

    mrr = subscriptions["MRR"].fillna(0).to_numpy(dtype=float)

    seats = subscriptions["Seats"].fillna(0).to_numpy(dtype=float)

    logins = usage["Logins"].fillna(0).to_numpy(dtype=float)

    active_users = usage["ActiveUsers"].fillna(0).to_numpy(dtype=float)

    api_calls = usage["APICalls"].fillna(0).to_numpy(dtype=float)

    session_minutes = usage["SessionMinutes"].fillna(0).to_numpy(dtype=float)


    # --------------------------------------------------------
    # Metric summary
    # --------------------------------------------------------

    metrics = {
        "MRR": mrr,
        "Seats": seats,
        "Logins": logins,
        "ActiveUsers": active_users,
        "APICalls": api_calls,
        "SessionMinutes": session_minutes,
    }

    summary = []

    for name, values in metrics.items():

        summary.append({
            "Metric": name,
            "Mean": np.mean(values),
            "Std": np.std(values),
            "Min": np.min(values),
            "Max": np.max(values),
        })


    # --------------------------------------------------------
    # MRR Z-score
    # --------------------------------------------------------

    subscriptions["MRR_ZScore"] = z_score(mrr)


    # --------------------------------------------------------
    # High-value subscription flag
    # --------------------------------------------------------

    high_value_cutoff = np.percentile(mrr, 75)

    subscriptions["HighValueFlag"] = np.where(
        subscriptions["MRR"] >= high_value_cutoff,
        "High Value",
        "Standard"
    )


    # --------------------------------------------------------
    # Customer-level usage aggregation
    # --------------------------------------------------------

    usage_customer = usage.groupby(
        "CustomerID",
        as_index=False
    ).agg(
        TotalLogins=("Logins", "sum"),
        TotalActiveUsers=("ActiveUsers", "sum"),
        TotalAPICalls=("APICalls", "sum"),
    )


    # --------------------------------------------------------
    # Customer-level subscription aggregation
    # --------------------------------------------------------

    customer = subscriptions.groupby(
        "CustomerID",
        as_index=False
    ).agg(
        TotalMRR=("MRR", "sum"),
        SubscriptionCount=("SubscriptionID", "nunique"),
        AnyChurned=(
            "Status",
            lambda s: (
                s.astype(str).str.lower() == "churned"
            ).any()
        ),
    ).merge(
        usage_customer,
        on="CustomerID",
        how="left"
    ).fillna(0)


    # --------------------------------------------------------
    # At-risk flag
    # --------------------------------------------------------

    customer["AtRiskFlag"] = np.where(
        (customer["AnyChurned"] == True)
        |
        (
            (customer["TotalLogins"] <= customer["TotalLogins"].median())
            &
            (
                customer["TotalActiveUsers"]
                <= customer["TotalActiveUsers"].median()
            )
        ),
        "At Risk",
        "Not At Risk"
    )


    # --------------------------------------------------------
    # Save Module 3 outputs
    # --------------------------------------------------------

    pd.DataFrame(summary).to_csv(
        OUTPUT_DIR / "module3_numpy_results.csv",
        index=False
    )

    subscriptions.to_csv(
        OUTPUT_DIR / "module3_subscription_flags.csv",
        index=False
    )

    customer.to_csv(
        OUTPUT_DIR / "module3_customer_risk_flags.csv",
        index=False
    )


    # --------------------------------------------------------
    # Completion message
    # --------------------------------------------------------

    print("Module 3 complete.")

    print(
        pd.DataFrame(summary)
        .round(2)
        .to_string(index=False)
    )

    print(
        f"High-value cutoff (75th percentile MRR): "
        f"{high_value_cutoff:.2f}"
    )

    print("Files written to module_3_output folder.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
