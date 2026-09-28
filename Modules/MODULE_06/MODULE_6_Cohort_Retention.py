"""
 MODULE 6 — Cohort & Retention Analysis

"""

from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_6_output"
OUTPUT_DIR.mkdir(exist_ok=True)

ANALYSIS_MONTH=pd.Timestamp("2024-12-01")

def main():
    c=pd.read_csv(DATA / "cleaned_customers.csv",parse_dates=["SignupDate"])
    s=pd.read_csv(DATA / "cleaned_subscriptions.csv",parse_dates=["StartDate","EndDate"])
    c["CohortMonth"]=c["SignupDate"].dt.to_period("M").dt.to_timestamp()

    records=[]
    for _,r in c.iterrows():
        cid=r.CustomerID; cohort=r.CohortMonth
        subs=s[s.CustomerID==cid]
        age=0
        while True:
            m=cohort+pd.DateOffset(months=age)
            if m>ANALYSIS_MONTH: break
            month_end=m+pd.offsets.MonthEnd(0)
            retained=((subs.StartDate<=month_end) & (subs.EndDate.isna() | (subs.EndDate>=m))).any()
            records.append({"CustomerID":cid,"CohortMonth":cohort,"MonthAge":age,
                            "CalendarMonth":m,"Retained":int(retained)})
            age+=1

    detail=pd.DataFrame(records)
    detail.to_csv(BASE / "MODULE_6_output" / "module6_retention_detail.csv",index=False)

    cohort=detail.groupby(["CohortMonth","MonthAge"])["Retained"].mean().unstack()
    cohort_pct=cohort*100
    cohort_pct.to_csv(BASE / "MODULE_6_output" / "module6_cohort_retention_pct.csv", index=False)

    curve=detail.groupby("MonthAge").agg(
        CustomersObserved=("CustomerID","nunique"),
        RetainedCustomers=("Retained","sum"),
        RetentionRate=("Retained","mean")
    ).reset_index()
    curve["RetentionPct"]=curve.RetentionRate*100
    curve.to_csv(BASE / "MODULE_6_output" / "module6_retention_curve.csv",index=False)

    eligible=cohort_pct[12].dropna().sort_values()
    summary=eligible.rename("RetentionAtMonth12Pct").reset_index()
    summary["Half"]="H1 2023" if False else np.where(summary.CohortMonth.dt.month<=6,"H1 2023","H2 2023")
    summary.to_csv(BASE / "MODULE_6_output" / "module6_12_month_cohort_comparison.csv",index=False)

    half=(summary.groupby("Half")["RetentionAtMonth12Pct"].agg(["count","mean","min","max"]).reset_index())
    half.to_csv(BASE / "MODULE_6_output" / "module6_half_year_change.csv",index=False)

    print("12-month cohort retention:")
    print(summary.to_string(index=False))
    print("\nH1 vs H2 2023:")
    print(half.to_string(index=False))
    print("\nRetention definition: a customer is retained in a calendar month when at least one subscription overlaps that month; Active/Paused subscriptions without an end date remain retained through the analysis period.")
    print("Observation window ends 2024-12 because usage data ends in 2024-12.")

if __name__=="__main__":
    main()
