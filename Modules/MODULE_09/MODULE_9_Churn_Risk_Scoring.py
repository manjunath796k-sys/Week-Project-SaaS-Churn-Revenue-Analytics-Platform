"""
MODULE 9 — Churn Risk Scoring

"""

from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_9_output"
OUTPUT_DIR.mkdir(exist_ok=True)

def inverse_percentile(s):
    return (1-s.rank(pct=True, method="average")).clip(0,1)

def main():
    v=pd.read_csv(BASE/"MODULE_4_output/module4_customer_level_view.csv")
    v["AvgSessionMinutes"]=np.where(v["UsageMonths"]>0,v["TotalSessionMinutes"]/v["UsageMonths"],0)
    active=v[v["Status"].isin(["Active","Paused"])].copy()

    sig=pd.DataFrame(index=active.index)
    sig["LowUsage"]=inverse_percentile(active["AvgMonthlyLogins"])
    sig["LowActiveUsers"]=inverse_percentile(active["AvgActiveUsers"])
    sig["LowSessionMinutes"]=inverse_percentile(active["AvgSessionMinutes"])
    sig["LowSatisfaction"]=inverse_percentile(active["AvgSatisfactionScore"].replace(0,np.nan)).fillna(1)
    sig["HighTicketsPerMonth"]=active["TicketsPerMonth"].rank(pct=True,method="average").fillna(0)
    sig["DecliningUsage"]=(active["UsageTrend"]=="Decreasing").astype(float)

    weights={"LowUsage":.30,"LowActiveUsers":.15,"LowSessionMinutes":.15,
             "LowSatisfaction":.15,"HighTicketsPerMonth":.10,"DecliningUsage":.15}
    score=sum(sig[k]*w for k,w in weights.items())*100

    risk=active[["CustomerID","CompanyName","PlanName","Status","TotalMRR","TotalSeats",
                 "AvgMonthlyLogins","AvgActiveUsers","AvgSatisfactionScore",
                 "TicketCount","TicketsPerMonth","UsageTrend"]].copy()
    risk["AvgSessionMinutes"]=active["AvgSessionMinutes"]
    risk["RiskScore"]=score.round(2)
    risk["RiskBand"]=pd.cut(risk["RiskScore"],[-.01,30,60,75,100],
                            labels=["Low","Moderate","High","Critical"])
    risk=risk.sort_values(["RiskScore","TotalMRR"],ascending=[False,False]).reset_index(drop=True)
    risk.insert(0,"RiskRank",range(1,len(risk)+1))
    risk.to_csv(OUTPUT_DIR / "module9_customer_risk_scores.csv",index=False)

    n=max(1,int(np.ceil(len(risk)*.20)))
    top=risk.head(n)
    summary=pd.DataFrame([{
        "ActiveCustomerCount":len(risk),
        "HighestRiskGroupDefinition":f"Top 20% of active/paused customers by heuristic risk score ({n} customers)",
        "HighestRiskCustomerCount":len(top),
        "HighestRiskMRR":round(top["TotalMRR"].sum(),2),
        "TotalActivePopulationMRR":round(risk["TotalMRR"].sum(),2),
        "HighestRiskMRRSharePct":round(100*top["TotalMRR"].sum()/risk["TotalMRR"].sum(),2),
        "ScoringMethod":"30% low monthly logins + 15% low active users + 15% low session minutes + 15% low satisfaction + 10% high tickets/month + 15% declining usage"
    }])
    summary.to_csv(OUTPUT_DIR / "module9_risk_summary.csv",index=False)
    print(summary.to_string(index=False))

if __name__=="__main__":
    main()
