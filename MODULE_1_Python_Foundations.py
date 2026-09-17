
# ============================================================
#  MODULE 1 - Python Foundations
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent

FILES = {
    "customers": BASE_DIR / "saas_customers.csv",
    "subscriptions": BASE_DIR / "saas_subscriptions.csv",
    "usage": BASE_DIR / "saas_usage.csv",
    "tickets": BASE_DIR / "saas_tickets.csv",
}

EXPECTED_COLUMNS = {
    "customers": [
        "CustomerID", "CompanyName", "Industry", "Country", "City",
        "EmployeeCount", "SignupDate", "AcquisitionChannel"
    ],
    "subscriptions": [
        "SubscriptionID", "CustomerID", "PlanName", "BillingTerm",
        "Seats", "MRR", "StartDate", "EndDate", "Status"
    ],
    "usage": [
        "CustomerID", "SubscriptionID", "Month", "Logins", "ActiveUsers",
        "FeatureUsed", "APICalls", "SessionMinutes"
    ],
    "tickets": [
        "TicketID", "CustomerID", "OpenedDate", "Category", "Priority",
        "ResolutionHours", "SatisfactionScore"
    ],
}


# ============================================================
# MODULE 1 — REUSABLE UTILITY FUNCTIONS
# ============================================================

def load_csv(path: Path, table_name: str) -> pd.DataFrame:
    """Load one CSV and give clear errors for missing/malformed files."""
    if not path.exists():
        raise FileNotFoundError(
            f"{table_name}: file not found -> {path.name}"
        )

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{table_name}: CSV is empty -> {path.name}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            f"{table_name}: malformed CSV / parsing error -> {path.name}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{table_name}: encoding could not be decoded -> {path.name}"
        ) from exc
    except OSError as exc:
        raise OSError(
            f"{table_name}: could not read file -> {path.name}"
        ) from exc

    if df.empty:
        raise ValueError(f"{table_name}: file loaded but contains no rows.")

    return df


def validate_schema(df: pd.DataFrame, table_name: str) -> None:
    """Validate required columns before any processing."""
    expected = EXPECTED_COLUMNS[table_name]
    missing = [c for c in expected if c not in df.columns]
    extra = [c for c in df.columns if c not in expected]

    if missing:
        raise ValueError(
            f"{table_name}: missing required columns: {missing}"
        )

    if extra:
        print(f"WARNING — {table_name}: unexpected columns found: {extra}")

    print(f"\n{table_name.upper()} validation")
    print(f"Shape   : {df.shape}")
    print(f"Columns : {list(df.columns)}")
    print("Dtypes  :")
    print(df.dtypes)


def audit_table(df: pd.DataFrame, table_name: str) -> dict:
    """Return shape, dtypes, missing counts, duplicate count and text uniques."""
    text_uniques = {}
    for col in df.select_dtypes(include=["object", "string"]).columns:
        text_uniques[col] = df[col].dropna().astype(str).unique().tolist()

    return {
        "table": table_name,
        "rows": len(df),
        "columns": len(df.columns),
        "shape": str(df.shape),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "text_uniques": text_uniques,
    }


def standardize_text(df: pd.DataFrame, title_case_columns=None) -> pd.DataFrame:
    """Strip whitespace from every text field and normalize selected categories."""
    df = df.copy()
    title_case_columns = title_case_columns or []

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()

    for col in title_case_columns:
        if col in df.columns:
            df[col] = df[col].str.title()

    return df


def print_audit(audit: dict, show_uniques: bool = True) -> None:
    print("\n" + "=" * 80)
    print(f"AUDIT — {audit['table'].upper()}")
    print("=" * 80)
    print("Shape:", audit["shape"])
    print("Dtypes:", audit["dtypes"])
    print("Missing:", audit["missing"])
    print("Duplicate rows:", audit["duplicate_rows"])

    if show_uniques:
        print("\nUnique values in every text column:")
        for col, values in audit["text_uniques"].items():
            print(f"  {col}: {values}")


# ============================================================
# MODULE 1 — LOAD + VALIDATE BEFORE PROCESSING
# ============================================================

raw = {}

for table_name, path in FILES.items():
    raw[table_name] = load_csv(path, table_name)
    validate_schema(raw[table_name], table_name)

print("\nAll four files loaded and schema-validated before processing.")


