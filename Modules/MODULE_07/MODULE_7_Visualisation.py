"""
 MODULE 7 — Visualisation

"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_7_output"
OUTPUT_DIR.mkdir(exist_ok=True)

def save(fig,name):
    fig.tight_layout(rect=[0,0.06,1,1])
    fig.savefig(OUTPUT_DIR / name,dpi=160,bbox_inches="tight")
    plt.close(fig)

def main():
    c=pd.read_csv(BASE/"cleaned_output/cleaned_customers.csv",parse_dates=["SignupDate"])
    s=pd.read_csv(BASE/"cleaned_output/cleaned_subscriptions.csv",parse_dates=["StartDate","EndDate"])
    u=pd.read_csv(BASE/"cleaned_output/cleaned_usage.csv",parse_dates=["Month"])
    t=pd.read_csv(BASE/"cleaned_output/cleaned_tickets.csv",parse_dates=["OpenedDate"])
    v=pd.read_csv(BASE/"MODULE_4_output/module4_customer_level_view.csv")

    insights=[]

    # 1 Churn trend
    churn=s[s.Status=="Churned"].copy()
    churn["Month"]=churn["EndDate"].dt.to_period("M").dt.to_timestamp()
    trend=churn.groupby("Month").size().rename("ChurnedSubscriptions").reset_index()
    fig,ax=plt.subplots(figsize=(10,5))
    ax.plot(trend.Month,trend.ChurnedSubscriptions,marker="o")
    ax.set_title("Churn Trend Over Time"); ax.set_xlabel("Churn month"); ax.set_ylabel("Churned subscriptions")
    if len(trend):
        peak=trend.loc[trend.ChurnedSubscriptions.idxmax()]
        ax.annotate(f"Peak: {int(peak.ChurnedSubscriptions)} in {peak.Month:%b %Y}",
                    (peak.Month,peak.ChurnedSubscriptions),xytext=(10,10),textcoords="offset points")
        insight=f"Peak monthly churn was {int(peak.ChurnedSubscriptions)} subscriptions in {peak.Month:%B %Y}."
    else: insight="No churn events were recorded."
    save(fig,"01_churn_trend.png"); insights.append(("Churn trend over time",insight))

    # 2 Retention curve
    r=pd.read_csv(BASE/"MODULE_6_output/module6_retention_curve.csv")
    fig,ax=plt.subplots(figsize=(9,5))
    ax.plot(r.MonthAge,r.RetentionPct,marker="o")
    ax.set_title("Customer Retention Curve"); ax.set_xlabel("Months since cohort signup"); ax.set_ylabel("Retention (%)")
    m12=r.loc[r.MonthAge==12,"RetentionPct"].iloc[0]
    ax.annotate(f"Month 12: {m12:.1f}%",(12,m12),xytext=(10,10),textcoords="offset points")
    insight=f"Overall cohort retention is {m12:.1f}% at month 12."
    save(fig,"02_retention_curve.png"); insights.append(("Retention curve",insight))

    # 3 Churn by segment (plan)
    seg=v.groupby("PlanName").agg(Customers=("CustomerID","count"),Churned=("Status",lambda x:(x=="Churned").sum())).reset_index()
    seg["ChurnRatePct"]=100*seg.Churned/seg.Customers
    fig,ax=plt.subplots(figsize=(8,5))
    ax.bar(seg.PlanName,seg.ChurnRatePct)
    ax.set_title("Churn Rate by Plan"); ax.set_xlabel("Plan"); ax.set_ylabel("Churn rate (%)")
    peak=seg.loc[seg.ChurnRatePct.idxmax()]
    ax.annotate(f"{peak.ChurnRatePct:.1f}%",(peak.PlanName,peak.ChurnRatePct),xytext=(0,6),textcoords="offset points",ha="center")
    insight=f"The {peak.PlanName} plan has a {peak.ChurnRatePct:.1f}% customer churn rate ({int(peak.Churned)} of {int(peak.Customers)})."
    save(fig,"03_churn_by_segment.png"); insights.append(("Churn by segment",insight))

    # 4 Usage distribution
    fig,ax=plt.subplots(figsize=(8,5))
    ax.hist(v["AvgMonthlyLogins"].dropna(),bins=20)
    ax.set_title("Distribution of Average Monthly Logins"); ax.set_xlabel("Average monthly logins"); ax.set_ylabel("Customers")
    med=v.AvgMonthlyLogins.median()
    ax.axvline(med,linestyle="--",label=f"Median = {med:.1f}")
    ax.legend()
    insight=f"The median customer records {med:.1f} average monthly logins."
    save(fig,"04_usage_distribution.png"); insights.append(("Usage distribution",insight))

    # 5 Usage vs churn
    plot=v.copy()
    plot["ChurnFlag"]=(plot.Status=="Churned").astype(int)
    means=plot.groupby("ChurnFlag")["AvgMonthlyLogins"].mean()
    fig,ax=plt.subplots(figsize=(8,5))
    ax.boxplot([plot.loc[plot.ChurnFlag==0,"AvgMonthlyLogins"],plot.loc[plot.ChurnFlag==1,"AvgMonthlyLogins"]],
               labels=["Retained","Churned"])
    ax.set_title("Usage vs Churn"); ax.set_xlabel("Customer status"); ax.set_ylabel("Average monthly logins")
    diff=means[0]-means[1]
    insight=f"Retained customers average {means[0]:.1f} logins/month versus {means[1]:.1f} for churned customers, a {diff:.1f}-login gap."
    save(fig,"05_usage_vs_churn.png"); insights.append(("Usage vs churn relationship",insight))

    # 6 Ticket satisfaction impact
    sat=plot.groupby("ChurnFlag")["AvgSatisfactionScore"].mean()
    fig,ax=plt.subplots(figsize=(8,5))
    ax.bar(["Retained","Churned"],[sat[0],sat[1]])
    ax.set_title("Average Ticket Satisfaction by Churn Status"); ax.set_xlabel("Customer status"); ax.set_ylabel("Average satisfaction score")
    gap=sat[0]-sat[1]
    insight=f"Retained customers average satisfaction {sat[0]:.2f} versus {sat[1]:.2f} among churned customers, a {gap:.2f}-point gap."
    save(fig,"06_ticket_satisfaction_impact.png"); insights.append(("Ticket satisfaction impact",insight))

    # 7 Correlation heatmap
    corr=pd.read_csv(BASE/"MODULE_4_output/module4_correlation_matrix.csv",index_col=0)
    fig,ax=plt.subplots(figsize=(10,8))
    im=ax.imshow(corr.values,aspect="auto")
    ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels(corr.columns,rotation=60,ha="right")
    ax.set_yticks(range(len(corr.index))); ax.set_yticklabels(corr.index)
    ax.set_title("Correlation Heatmap")
    fig.colorbar(im,ax=ax,fraction=.046,pad=.04,label="Pearson correlation")
    insight_pair=corr.where(~np.eye(len(corr),dtype=bool)).stack().sort_values(key=lambda x:x.abs(),ascending=False).iloc[0]
    # Use upper triangle to avoid duplicate pair.
    pairs=[]
    for i,a in enumerate(corr.columns):
        for j,b in enumerate(corr.columns):
            if j>i: pairs.append((abs(corr.loc[a,b]),a,b,corr.loc[a,b]))
    _,a,b,r=max(pairs)
    insight=f"The strongest linear relationship is between {a} and {b}, with Pearson r={r:.2f}."
    save(fig,"07_correlation_heatmap.png"); insights.append(("Correlation heatmap",insight))

    pd.DataFrame(insights,columns=["Chart","OneLineInsight"]).to_csv(BASE/"MODULE_7_output/module7_chart_insights.csv",index=False)
    print(pd.DataFrame(insights).to_string(index=False))

if __name__=="__main__":
    main()
