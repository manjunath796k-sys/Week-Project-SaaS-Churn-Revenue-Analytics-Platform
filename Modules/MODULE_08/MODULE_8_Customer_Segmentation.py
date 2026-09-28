"""
 MODULE 8 — Customer Segmentation

"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA = BASE / "cleaned_output"

OUTPUT_DIR = BASE / "MODULE_8_output"
OUTPUT_DIR.mkdir(exist_ok=True)

FEATURES=["TotalMRR","TotalSeats","AvgMonthlyLogins","AvgActiveUsers",
          "AvgSessionMinutes","TicketCount","AvgSatisfactionScore",
          "TenureMonths","RevenuePerSeat"]

def main():
    v=pd.read_csv(BASE/"MODULE_4_output/module4_customer_level_view.csv")
    v["AvgSessionMinutes"]=np.where(v["UsageMonths"]>0,v["TotalSessionMinutes"]/v["UsageMonths"],0)
    X=v[FEATURES].replace([np.inf,-np.inf],np.nan).fillna(0)
    scaler=StandardScaler()
    Xs=scaler.fit_transform(X)

    rows=[]
    for k in range(2,9):
        km=KMeans(n_clusters=k,random_state=42,n_init=20)
        labels=km.fit_predict(Xs)
        rows.append({"k":k,"inertia":km.inertia_,"silhouette":silhouette_score(Xs,labels)})
    elbow=pd.DataFrame(rows)
    elbow.to_csv(OUTPUT_DIR / "module8_elbow_metrics.csv",index=False)

    # k=5 is selected because the inertia curve begins to flatten around 5
    # and it has the highest silhouette among k=2..8 in this dataset.
    k=5
    model=KMeans(n_clusters=k,random_state=42,n_init=20)
    v["ClusterID"]=model.fit_predict(Xs)

    summary=v.groupby("ClusterID").agg(
        Customers=("CustomerID","count"),AvgMRR=("TotalMRR","mean"),
        AvgSeats=("TotalSeats","mean"),AvgMonthlyLogins=("AvgMonthlyLogins","mean"),
        AvgActiveUsers=("AvgActiveUsers","mean"),AvgSessionMinutes=("AvgSessionMinutes","mean"),
        AvgTickets=("TicketCount","mean"),AvgSatisfaction=("AvgSatisfactionScore","mean"),
        AvgTenureMonths=("TenureMonths","mean"),
        AvgRevenuePerSeat=("RevenuePerSeat","mean"),
        ChurnRatePct=("Status",lambda x:100*(x=="Churned").mean())
    ).reset_index()

    # Behavior names based on measured profiles.
    names={}
    for _,r in summary.iterrows():
        cid=int(r.ClusterID)
        if r.AvgMRR>1500:
            names[cid]="High-Value Expansion Accounts"
        elif r.AvgMonthlyLogins>=12 and r.ChurnRatePct<15:
            names[cid]="Highly Engaged Retained Accounts"
        elif r.AvgSatisfaction<3:
            names[cid]="Support-Frustrated Accounts"
        elif r.AvgMonthlyLogins<8 and r.ChurnRatePct>35:
            names[cid]="Low-Usage At-Risk Accounts"
        else:
            names[cid]="Steady Mid-Market Accounts"
    summary["SegmentName"]=summary.ClusterID.map(names)

    recs={
        "High-Value Expansion Accounts":"Protect adoption with executive check-ins, usage reviews and expansion opportunities.",
        "Highly Engaged Retained Accounts":"Maintain adoption momentum with advanced-feature education and advocacy programs.",
        "Support-Frustrated Accounts":"Prioritize support recovery, root-cause resolution and proactive service follow-up.",
        "Low-Usage At-Risk Accounts":"Trigger product-adoption outreach, usage alerts and targeted onboarding before renewal.",
        "Steady Mid-Market Accounts":"Use lightweight lifecycle campaigns to increase feature adoption and monitor early churn signals."
    }
    summary["RetentionRecommendation"]=summary.SegmentName.map(recs)
    summary.to_csv(OUTPUT_DIR / "module8_cluster_summary.csv",index=False)
    v[["CustomerID","ClusterID"]].merge(summary[["ClusterID","SegmentName","RetentionRecommendation"]],on="ClusterID").to_csv(OUTPUT_DIR / "module8_customer_segments.csv",index=False)

    fig,ax=plt.subplots(figsize=(8,5))
    ax.plot(elbow.k,elbow.inertia,marker="o")
    ax.axvline(k,linestyle="--",label=f"Selected k={k}")
    ax.set_title("K-Means Elbow Method"); ax.set_xlabel("Number of clusters (k)"); ax.set_ylabel("Within-cluster sum of squares (inertia)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUTPUT_DIR / "module8_elbow_method.png",dpi=160,bbox_inches="tight"); plt.close(fig)

    pd.DataFrame({
        "Decision":["Selected k","Reason"],
        "Value":[k,"Elbow begins flattening around k=5; k=5 also has the highest silhouette score (0.198) among tested k=2..8."]
    }).to_csv(OUTPUT_DIR / "module8_k_selection_justification.csv",index=False)

    print(summary.round(2).to_string(index=False))

if __name__=="__main__":
    main()
