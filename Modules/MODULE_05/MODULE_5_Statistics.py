"""
  MODULE 5 - Statistics

"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_5_output"
OUTPUT_DIR.mkdir(exist_ok=True)

SEED = 42

def build_customer_metrics():

    c = pd.read_csv(
        DATA / "cleaned_customers.csv",
        parse_dates=["SignupDate"]
    )

    s = pd.read_csv(
        DATA / "cleaned_subscriptions.csv",
        parse_dates=["StartDate", "EndDate"]
    )

    u = pd.read_csv(
        DATA / "cleaned_usage.csv",
        parse_dates=["Month"]
    )

    t = pd.read_csv(
        DATA / "cleaned_tickets.csv",
        parse_dates=["OpenedDate"]
    )

    status = s.groupby("CustomerID")["Status"].apply(
        lambda x: "Churned"
        if (x == "Churned").any()
        else "Retained"
    ).rename("ChurnGroup")

    usage = u.groupby("CustomerID").agg(
        AvgMonthlyLogins=("Logins", "mean"),
        AvgActiveUsers=("ActiveUsers", "mean"),
        AvgSessionMinutes=("SessionMinutes", "mean"),
        AvgAPICalls=("APICalls", "mean")
    )

    tickets = t.groupby("CustomerID").agg(
        TicketCount=("TicketID", "nunique"),
        AvgResolutionHours=("ResolutionHours", "mean"),
        AvgSatisfactionScore=("SatisfactionScore", "mean")
    )

    m = (
        c[["CustomerID"]]
        .merge(status, on="CustomerID", how="left")
        .merge(usage, on="CustomerID", how="left")
        .merge(tickets, on="CustomerID", how="left")
    )

    return m

def main():
    m=build_customer_metrics()
    m["ChurnGroup"]=m["ChurnGroup"].fillna("No Subscription")

    # Population/sample comparison.
    sample_rows=[]
    for metric in ["AvgMonthlyLogins","AvgActiveUsers","AvgSessionMinutes","AvgAPICalls"]:
        pop=m[metric].dropna()
        for sample_id, seed in [("Sample_1",SEED),("Sample_2",SEED+1)]:
            sample=pop.sample(n=min(50,len(pop)),random_state=seed)
            sample_rows.append({
                "Metric":metric,"Sample":sample_id,"PopulationN":len(pop),
                "PopulationMean":pop.mean(),"SampleN":len(sample),"SampleMean":sample.mean(),
                "DifferenceFromPopulationMean":sample.mean()-pop.mean()
            })
    pd.DataFrame(sample_rows).to_csv(BASE / "MODULE_5_output" / "module5_sample_vs_population.csv",index=False)

    # Welch two-sample t-tests plus Mann-Whitney sensitivity check.
    rows=[]
    for metric in ["AvgMonthlyLogins","AvgActiveUsers","AvgSessionMinutes","AvgAPICalls"]:
        a=m.loc[m.ChurnGroup=="Churned",metric].dropna()
        b=m.loc[m.ChurnGroup=="Retained",metric].dropna()
        tt=stats.ttest_ind(a,b,equal_var=False)
        mw=stats.mannwhitneyu(a,b,alternative="two-sided")
        pooled_sd=np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
        cohen_d=(a.mean()-b.mean())/pooled_sd if pooled_sd else np.nan
        rows.append({
            "Metric":metric,"ChurnedN":len(a),"RetainedN":len(b),
            "ChurnedMean":a.mean(),"RetainedMean":b.mean(),
            "MeanDifference_ChurnedMinusRetained":a.mean()-b.mean(),
            "Welch_t":tt.statistic,"Welch_p_value":tt.pvalue,"Welch_df":tt.df,
            "MannWhitney_U":mw.statistic,"MannWhitney_p_value":mw.pvalue,
            "Cohens_d":cohen_d,
            "Interpretation":("Evidence of a difference in group means at alpha=0.05; this does not establish causation."
                              if tt.pvalue<0.05 else
                              "No statistically significant difference in group means at alpha=0.05; this does not prove the groups are identical.")
        })
    results=pd.DataFrame(rows)
    results.to_csv(BASE / "MODULE_5_output" / "module5_hypothesis_tests.csv",index=False)

    # A focused hypothesis requested in the brief.
    focused=results[results.Metric=="AvgMonthlyLogins"].copy()
    focused.to_csv(BASE / "MODULE_5_output" / "module5_primary_churn_hypothesis.csv",index=False)

    print(results[["Metric","Welch_p_value","Cohens_d"]].to_string(index=False))
    print("p-values are evidence against the null of equal means; they do not prove causation.")

if __name__=="__main__":
    main()
