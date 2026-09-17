from MODULE_1_Python_Foundations import *

# ============================================================
# MODULE 2 — INITIAL DATA AUDIT
# ============================================================

initial_audits = {
    name: audit_table(df, name) for name, df in raw.items()
}

print("\n\n******** INITIAL DATA AUDIT ********")
for audit in initial_audits.values():
    print_audit(audit)


# Work on copies only after the initial audit.
customers = raw["customers"].copy()
subscriptions = raw["subscriptions"].copy()
usage = raw["usage"].copy()
tickets = raw["tickets"].copy()

cleaning_log = []


def log_issue(table, issue, rows_affected, action, why):
    cleaning_log.append({
        "Table": table,
        "Issue": issue,
        "Rows affected": rows_affected,
        "Action": action,
        "Why": why,
    })


# ============================================================
# 2A — CUSTOMERS
# ============================================================

# Standardize text.
customers = standardize_text(
    customers,
    title_case_columns=["Industry", "Country", "City", "AcquisitionChannel"]
)

# Missing Industry: no reliable value can be inferred.
n = int(customers["Industry"].isna().sum())
customers["Industry"] = customers["Industry"].fillna("Unknown")
log_issue(
    "customers", "Missing Industry", n, 'Fill with "Unknown"',
    "Industry cannot be reliably inferred from the available fields; "
    "Unknown preserves the customer record without inventing a category."
)

# Missing EmployeeCount: use industry-level median after normalization,
# then overall median only if Industry itself is Unknown.
n = int(customers["EmployeeCount"].isna().sum())
industry_median = customers.groupby("Industry", dropna=False)["EmployeeCount"].transform("median")
overall_median = customers["EmployeeCount"].median()
customers["EmployeeCount"] = customers["EmployeeCount"].fillna(industry_median)
customers["EmployeeCount"] = customers["EmployeeCount"].fillna(overall_median)
log_issue(
    "customers", "Missing EmployeeCount", n,
    "Fill using Industry median; fallback to overall median when no "
    "industry-level value exists",
    "Employee count is numeric and industry is a meaningful grouping; "
    "median is less sensitive to skew than mean."
)

# Missing AcquisitionChannel.
n = int(customers["AcquisitionChannel"].isna().sum())
customers["AcquisitionChannel"] = customers["AcquisitionChannel"].fillna("Unknown")
log_issue(
    "customers", "Missing AcquisitionChannel", n, 'Fill with "Unknown"',
    "The source does not provide enough evidence to reconstruct the channel."
)

# Date conversion + validation.
customers["SignupDate"] = pd.to_datetime(customers["SignupDate"], errors="coerce")
if customers["SignupDate"].isna().any():
    raise ValueError("customers.SignupDate contains invalid/unparseable dates.")

# Exact duplicate rows.
n = int(customers.duplicated().sum())
customers = customers.drop_duplicates().copy()
log_issue(
    "customers", "Exact duplicate rows", n, "Remove exact duplicates",
    "Identical customer records add no information and can duplicate downstream joins."
)

# CustomerID must be unique after exact-duplicate removal.
if customers["CustomerID"].duplicated().any():
    raise ValueError("customers.CustomerID is still duplicated after cleaning.")


# ============================================================
# 2B — SUBSCRIPTIONS
# ============================================================

subscriptions = standardize_text(
    subscriptions,
    title_case_columns=["PlanName", "BillingTerm", "Status"]
)

subscriptions["StartDate"] = pd.to_datetime(subscriptions["StartDate"], errors="coerce")
subscriptions["EndDate"] = pd.to_datetime(subscriptions["EndDate"], errors="coerce")

if subscriptions["StartDate"].isna().any():
    raise ValueError("subscriptions.StartDate contains invalid/unparseable dates.")

bad_end = subscriptions["EndDate"].notna() & (subscriptions["EndDate"] < subscriptions["StartDate"])
if bad_end.any():
    raise ValueError("subscriptions contains EndDate earlier than StartDate.")

# Seats missing — plan-level median.
n = int(subscriptions["Seats"].isna().sum())
plan_seat_median = subscriptions.groupby("PlanName")["Seats"].transform("median")
subscriptions["Seats"] = subscriptions["Seats"].fillna(plan_seat_median)
subscriptions["Seats"] = subscriptions["Seats"].fillna(subscriptions["Seats"].median())
log_issue(
    "subscriptions", "Missing Seats", n,
    "Fill using PlanName median; fallback to overall median",
    "Seat counts differ by plan, so plan-level median preserves the plan's "
    "typical size better than a blanket zero or mean."
)

# MRR missing — plan + billing-term median.
n = int(subscriptions["MRR"].isna().sum())
plan_term_median = subscriptions.groupby(
    ["PlanName", "BillingTerm"]
)["MRR"].transform("median")
subscriptions["MRR"] = subscriptions["MRR"].fillna(plan_term_median)
subscriptions["MRR"] = subscriptions["MRR"].fillna(
    subscriptions.groupby("PlanName")["MRR"].transform("median")
)
subscriptions["MRR"] = subscriptions["MRR"].fillna(subscriptions["MRR"].median())
log_issue(
    "subscriptions", "Missing MRR", n,
    "Fill using PlanName + BillingTerm median; fallback to PlanName median "
    "and then overall median",
    "MRR is strongly tied to plan and billing structure; grouped medians "
    "avoid assuming one value fits every plan."
)

# EndDate is intentionally retained as null for Active/Paused subscriptions.
expected_enddate_nulls = subscriptions["EndDate"].isna() & subscriptions["Status"].isin(["Active", "Paused"])
unexpected_enddate_nulls = subscriptions["EndDate"].isna() & ~subscriptions["Status"].isin(["Active", "Paused"])
if unexpected_enddate_nulls.any():
    raise ValueError("Unexpected missing EndDate found for a non-Active/non-Paused subscription.")

log_issue(
    "subscriptions", "Missing EndDate (expected lifecycle state)", int(expected_enddate_nulls.sum()),
    "Retain as NULL for Active/Paused subscriptions",
    "An active or paused subscription has no completed end date; replacing it "
    "would create false churn/end dates."
)

n = int(subscriptions.duplicated().sum())
subscriptions = subscriptions.drop_duplicates().copy()
log_issue(
    "subscriptions", "Exact duplicate rows", n, "Remove exact duplicates",
    "Duplicate subscription records can double-count recurring revenue."
)

if subscriptions["SubscriptionID"].duplicated().any():
    raise ValueError("subscriptions.SubscriptionID is still duplicated after cleaning.")


# ============================================================
# 2C — USAGE
# ============================================================

usage = standardize_text(usage, title_case_columns=["FeatureUsed"])
usage["Month"] = pd.to_datetime(usage["Month"], errors="coerce")
if usage["Month"].isna().any():
    raise ValueError("usage.Month contains invalid/unparseable dates.")

# ActiveUsers missing — customer-level median, fallback overall median.
n = int(usage["ActiveUsers"].isna().sum())
cust_active_median = usage.groupby("CustomerID")["ActiveUsers"].transform("median")
usage["ActiveUsers"] = usage["ActiveUsers"].fillna(cust_active_median)
usage["ActiveUsers"] = usage["ActiveUsers"].fillna(usage["ActiveUsers"].median())
log_issue(
    "usage", "Missing ActiveUsers", n,
    "Fill using CustomerID median; fallback to overall median",
    "Usage is customer-specific, so the customer's historical median is a "
    "more defensible estimate than a global value."
)

# SessionMinutes missing — customer-level median.
n = int(usage["SessionMinutes"].isna().sum())
cust_session_median = usage.groupby("CustomerID")["SessionMinutes"].transform("median")
usage["SessionMinutes"] = usage["SessionMinutes"].fillna(cust_session_median)
usage["SessionMinutes"] = usage["SessionMinutes"].fillna(usage["SessionMinutes"].median())
log_issue(
    "usage", "Missing SessionMinutes", n,
    "Fill using CustomerID median; fallback to overall median",
    "Session duration is behavior-specific; customer-level history is the "
    "most relevant available reference."
)

n = int(usage.duplicated().sum())
usage = usage.drop_duplicates().copy()
log_issue(
    "usage", "Exact duplicate rows", n, "Remove exact duplicates",
    "Duplicate usage events would inflate engagement metrics."
)


# ============================================================
# 2D — TICKETS
# ============================================================

tickets = standardize_text(tickets, title_case_columns=["Category", "Priority"])
tickets["OpenedDate"] = pd.to_datetime(tickets["OpenedDate"], errors="coerce")
if tickets["OpenedDate"].isna().any():
    raise ValueError("tickets.OpenedDate contains invalid/unparseable dates.")

# ResolutionHours — Category + Priority median.
n = int(tickets["ResolutionHours"].isna().sum())
cat_pri_median = tickets.groupby(
    ["Category", "Priority"]
)["ResolutionHours"].transform("median")
tickets["ResolutionHours"] = tickets["ResolutionHours"].fillna(cat_pri_median)
tickets["ResolutionHours"] = tickets["ResolutionHours"].fillna(
    tickets.groupby("Category")["ResolutionHours"].transform("median")
)
tickets["ResolutionHours"] = tickets["ResolutionHours"].fillna(
    tickets["ResolutionHours"].median()
)
log_issue(
    "tickets", "Missing ResolutionHours", n,
    "Fill using Category + Priority median; fallback to Category median "
    "and overall median",
    "Resolution time depends on ticket type and urgency, so grouped medians "
    "preserve those differences."
)

# SatisfactionScore — Category median.
n = int(tickets["SatisfactionScore"].isna().sum())
cat_sat_median = tickets.groupby("Category")["SatisfactionScore"].transform("median")
tickets["SatisfactionScore"] = tickets["SatisfactionScore"].fillna(cat_sat_median)
tickets["SatisfactionScore"] = tickets["SatisfactionScore"].fillna(
    tickets["SatisfactionScore"].median()
)
log_issue(
    "tickets", "Missing SatisfactionScore", n,
    "Fill using Category median; fallback to overall median",
    "Satisfaction can vary by ticket type; category-level median avoids "
    "assuming every support category has the same score."
)

n = int(tickets.duplicated().sum())
tickets = tickets.drop_duplicates().copy()
log_issue(
    "tickets", "Exact duplicate rows", n, "Remove exact duplicates",
    "Duplicate tickets would overstate ticket volume and support workload."
)

if tickets["TicketID"].duplicated().any():
    raise ValueError("tickets.TicketID is still duplicated after cleaning.")


# ============================================================
# 2E — REFERENTIAL INTEGRITY
# ============================================================

valid_customers = set(customers["CustomerID"])

# Subscriptions must point to an existing customer.
orphan_sub = ~subscriptions["CustomerID"].isin(valid_customers)
n = int(orphan_sub.sum())
if n:
    orphan_ids = sorted(subscriptions.loc[orphan_sub, "CustomerID"].unique())
    subscriptions = subscriptions.loc[~orphan_sub].copy()
    log_issue(
        "subscriptions", "CustomerID not present in customers", n,
        f"Remove orphan subscriptions for customer IDs: {orphan_ids}",
        "There is no customer master record to which these subscriptions can "
        "be reliably linked."
    )

valid_subscriptions = set(subscriptions["SubscriptionID"])

# Usage must point to an existing customer and subscription.
orphan_usage_cust = ~usage["CustomerID"].isin(valid_customers)
orphan_usage_sub = ~usage["SubscriptionID"].isin(valid_subscriptions)
orphan_usage = orphan_usage_cust | orphan_usage_sub
n = int(orphan_usage.sum())
if n:
    usage = usage.loc[~orphan_usage].copy()
    log_issue(
        "usage", "Referential mismatch (CustomerID or SubscriptionID)", n,
        "Remove orphan usage rows",
        "Usage without a valid customer/subscription cannot be safely attributed."
    )

# Tickets must point to an existing customer.
orphan_tickets = ~tickets["CustomerID"].isin(valid_customers)
n = int(orphan_tickets.sum())
if n:
    tickets = tickets.loc[~orphan_tickets].copy()
    log_issue(
        "tickets", "CustomerID not present in customers", n,
        "Remove orphan ticket rows",
        "Tickets without a valid customer cannot be reliably associated with an account."
    )


# ============================================================
# 2F — FINAL VALIDATION
# ============================================================

cleaned = {
    "customers": customers,
    "subscriptions": subscriptions,
    "usage": usage,
    "tickets": tickets,
}

final_audits = {
    name: audit_table(df, name) for name, df in cleaned.items()
}

print("\n\n******** FINAL DATA AUDIT ********")
for audit in final_audits.values():
    print_audit(audit, show_uniques=True)

# Hard validation checks.
assert all(v["duplicate_rows"] == 0 for v in final_audits.values())
assert customers["CustomerID"].is_unique
assert subscriptions["SubscriptionID"].is_unique
assert tickets["TicketID"].is_unique
assert subscriptions["CustomerID"].isin(customers["CustomerID"]).all()
assert usage["CustomerID"].isin(customers["CustomerID"]).all()
assert usage["SubscriptionID"].isin(subscriptions["SubscriptionID"]).all()
assert tickets["CustomerID"].isin(customers["CustomerID"]).all()

# Final validation: confirm all text columns have no leading/trailing whitespace
for table_name, df in {
    "Customers": customers,
    "Subscriptions": subscriptions,
    "Usage": usage,
    "Tickets": tickets
}.items():

    for col in df.select_dtypes(include=["object", "string"]).columns:
        values = df[col].dropna().astype(str)

        assert not values.str.startswith(" ").any(), \
            f"{table_name}.{col} contains leading whitespace"

        assert not values.str.endswith(" ").any(), \
            f"{table_name}.{col} contains trailing whitespace"

print("Text standardization validation passed.")


# All missing values except the intentionally-null EndDate lifecycle field.
for name, df in cleaned.items():
    allowed = {"EndDate": int(df["EndDate"].isna().sum())} if name == "subscriptions" else {}
    unexpected = {
        col: int(count)
        for col, count in df.isna().sum().items()
        if count > 0 and col not in allowed
    }
    if unexpected:
        raise AssertionError(f"Unexpected remaining missing values in {name}: {unexpected}")

print("\nVALIDATION PASSED")
print("- Exact duplicate rows: 0 in all tables")
print("- CustomerID / SubscriptionID / TicketID keys are unique")
print("- No orphan CustomerIDs remain")
print("- No orphan SubscriptionIDs remain in usage")
print("- No unexpected missing values remain")
print("- Active/Paused subscription EndDate NULLs are retained intentionally")


# ============================================================
# OUTPUTS
# ============================================================

OUTPUT_DIR = BASE_DIR / "cleaned_output"
OUTPUT_DIR.mkdir(exist_ok=True)

for name, df in cleaned.items():
    df.to_csv(OUTPUT_DIR / f"cleaned_{name}.csv", index=False)

pd.DataFrame(cleaning_log).to_csv(
    OUTPUT_DIR / "data_cleaning_log.csv", index=False
)

# Compact machine-readable audit summaries.
audit_rows = []
for stage, audits in [("Initial", initial_audits), ("Final", final_audits)]:
    for name, a in audits.items():
        for col, count in a["missing"].items():
            audit_rows.append({
                "Stage": stage,
                "Table": name,
                "Metric": "Missing",
                "Column": col,
                "Value": count,
            })
        audit_rows.append({
            "Stage": stage, "Table": name, "Metric": "Rows",
            "Column": "", "Value": a["rows"]
        })
        audit_rows.append({
            "Stage": stage, "Table": name, "Metric": "DuplicateRows",
            "Column": "", "Value": a["duplicate_rows"]
        })

pd.DataFrame(audit_rows).to_csv(
    OUTPUT_DIR / "audit_summary.csv", index=False
)

print(f"\nOutputs written to: {OUTPUT_DIR}")