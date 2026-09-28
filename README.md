# SaaS Churn & Revenue Analytics Platform

## Project Overview

This project analyzes customer churn, recurring revenue, product usage, customer retention, support activity, and customer risk for a B2B SaaS company.

The objective is to understand the factors associated with customer churn, identify high-risk customers, analyze revenue exposure, and provide actionable insights for improving customer retention.

The project covers the complete analytics workflow from raw data loading and cleaning to statistical analysis, customer segmentation, churn-risk scoring, SQL analysis, Excel reporting, Power BI visualization, and executive recommendations.

## Business Problem

CloudMetrics is a B2B SaaS company operating across four subscription plan tiers.

Leadership has observed that revenue growth is flattening despite steady new customer signups and wants to understand the underlying churn problem.

The analysis focuses on:

- What factors are associated with customer churn?
- Which customer segments have higher churn?
- How does product usage differ between churned and retained customers?
- Which customers are at the highest churn risk?
- How much monthly recurring revenue is exposed to churn risk?
- Which customer groups should receive retention attention?

## Dataset

The project uses four datasets collected from different internal systems:

- `saas_customers.csv`
- `saas_subscriptions.csv`
- `saas_usage.csv`
- `saas_tickets.csv`

The datasets contain information related to:

- Customer details
- Subscription plans
- Monthly recurring revenue
- Product usage
- Customer tenure
- Support tickets
- Ticket satisfaction
- Churn status

The raw datasets are cleaned and validated before being used for analysis.

## Project Modules

### Module 1 — Python Foundations

- Data loading
- Exception handling
- File validation
- Shape validation
- Column validation
- Data type validation
- Reusable utility functions

### Module 2 — Data Audit & Cleaning

- Shape and data type analysis
- Missing-value analysis
- Duplicate detection
- Unique-value analysis
- Text standardization
- Referential mismatch resolution
- Post-cleaning validation
- Data Cleaning Log

### Module 3 — NumPy

- Conversion of MRR, seats, and usage metrics into NumPy arrays
- Mean calculation
- Standard deviation
- Minimum and maximum values
- Metric normalization
- High-value and at-risk customer flags using `np.where()`

### Module 4 — Pandas Wrangling & EDA

- Customer-level data integration
- GroupBy analysis
- Multiple aggregations
- Pivot tables
- Calculated columns
- Tenure analysis
- Revenue per seat
- Tickets per month
- Usage trend
- IQR-based outlier detection
- Correlation matrix
- Correlation interpretation

### Module 5 — Statistics

- Descriptive statistics
- Random sample vs population comparison
- Hypothesis testing
- Churn hypothesis analysis
- p-value calculation
- Statistical interpretation

### Module 6 — Cohort & Retention Analysis

- Signup-month cohort analysis
- Retention percentage calculation
- Retention curve
- Cohort comparison
- Retention trend analysis

### Module 7 — Visualisation

The project includes the following seven required visualizations:

1. Churn trend over time
2. Retention curve
3. Churn by segment
4. Usage distribution
5. Usage vs churn relationship
6. Ticket satisfaction impact
7. Correlation heatmap

Each visualization includes a business-focused insight.

### Module 8 — Customer Segmentation

- Customer-level feature engineering
- Feature scaling
- Elbow Method
- K-Means clustering
- Selection of optimal `k`
- Behaviour-based cluster naming
- Retention recommendations for each segment

### Module 9 — Churn Risk Scoring

- Customer risk scoring
- Combination of churn-related signals
- Customer risk ranking
- Identification of high-risk customers
- MRR exposure analysis

### Module 10 — SQL

The SQL analysis covers business questions using:

- JOIN
- GROUP BY
- HAVING
- CASE
- Subqueries
- CTEs
- Window functions
- Orphan-record handling

SQL outputs are provided as CSV files.

### Module 11 — Excel Reporting

The Excel report contains:

- Cleaned data
- Pivot summary
- KPI reporting
- Total MRR
- Churn Rate
- Average Revenue per Account
- Average Tenure

### Module 12 — Power BI Dashboard

The Power BI dashboard contains:

- KPI cards
- Business visuals
- Slicers
- Data model relationships
- DAX measures
- `DIVIDE` calculations
- Python cross-checking

### Module 13 — Executive Summary

The executive summary provides a leadership-level overview of:

- Revenue
- Customer churn
- Product usage
- Customer retention
- Customer segments
- Churn risk
- Revenue exposure
- Retention priorities

### Module 14 — Repository & Documentation

The project is organized into structured modules, datasets, outputs, reports, and documentation to support reproducibility and review.

## Technologies Used

- Python
- Pandas
- NumPy
- SciPy
- Scikit-learn
- Matplotlib
- SQL
- Microsoft Excel
- Power BI
- DAX
- Git & GitHub

## Python Libraries

- `pandas`
- `numpy`
- `scipy`
- `scikit-learn`
- `matplotlib`
- `openpyxl`

## Installation

Clone the repository:

    git clone <YOUR-GITHUB-REPOSITORY-URL>

Navigate to the project directory:

    cd SaaS-Churn-Revenue-Analytics

Install the required Python libraries:

    pip install -r requirements.txt

## How to Run

Run the Python modules in sequence.

    python modules/module_01/...
    python modules/module_02/...
    python modules/module_03/...
    python modules/module_04/...
    python modules/module_05/...
    python modules/module_06/...
    python modules/module_07/...
    python modules/module_08/...
    python modules/module_09/...

Later modules use outputs generated by earlier modules, so the recommended workflow is to execute the modules sequentially.

## SQL Analysis

The cleaned datasets are loaded into SQL for business analysis.

The SQL module contains queries covering:

- Customer analysis
- Revenue analysis
- Churn analysis
- Segment analysis
- Aggregations
- CTEs
- Window functions
- Subqueries
- Orphan-record handling

The resulting query outputs are stored as CSV files.

## Excel Reporting

The Excel report provides a business-oriented summary of the cleaned data.

It includes:

- KPI calculations
- Pivot analysis
- Revenue analysis
- Churn analysis
- Customer metrics

## Power BI Dashboard

The Power BI dashboard provides an interactive view of:

- Revenue
- Customer count
- Churn
- Retention
- Customer segments
- Usage behaviour
- Risk indicators

The dashboard includes slicers and DAX measures for interactive analysis.

## Key Analysis Areas

The project investigates the relationship between:

- Customer usage and churn
- Customer tenure and retention
- Subscription plans and churn
- Customer segments and churn
- Support ticket satisfaction and churn
- Customer risk and MRR exposure
- Signup cohorts and retention

## Deliverables

| Module | Deliverable |
|---|---|
| Module 1 | Python Foundations |
| Module 2 | Data Audit & Cleaning |
| Module 3 | NumPy Analysis |
| Module 4 | Pandas & EDA |
| Module 5 | Statistical Analysis |
| Module 6 | Cohort & Retention Analysis |
| Module 7 | Visualisations |
| Module 8 | Customer Segmentation |
| Module 9 | Churn Risk Scoring |
| Module 10 | SQL Analysis |
| Module 11 | Excel Reporting |
| Module 12 | Power BI Dashboard |
| Module 13 | Executive Summary |
| Module 14 | Repository & Documentation |

## Conclusion

This project demonstrates an end-to-end SaaS analytics workflow, transforming raw operational data into cleaned datasets, analytical outputs, dashboards, customer segments, churn-risk insights, and business recommendations.

The final outputs are designed to support data-driven understanding of customer churn and recurring revenue exposure.

## Author

**Manjunath Kumbar**
