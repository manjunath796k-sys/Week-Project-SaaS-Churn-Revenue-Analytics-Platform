-- ============================================================
-- MODULE 10 - SQL ANALYSIS
-- ============================================================
--
-- RENAME TABLE
--     cleaned_customers TO saas_customers,
--     cleaned_subscriptions TO saas_subscriptions,
--     cleaned_tickets TO saas_tickets,
--     cleaned_usage TO saas_usage;
--
-- Expected table names:
--   saas_customers
--   saas_subscriptions
--   saas_tickets
--   saas_usage
-- ============================================================

CREATE DATABASE IF NOT EXISTS saas_churn;
USE saas_churn;

-- ============================================================
-- Q1 - CUSTOMER REVENUE SUMMARY
-- JOIN + GROUP BY
-- ============================================================

SELECT
    c.CustomerID,
    c.CompanyName,
    c.Industry,
    COALESCE(SUM(s.MRR), 0) AS TotalMRR
FROM saas_customers AS c
LEFT JOIN saas_subscriptions AS s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName,
    c.Industry
ORDER BY TotalMRR DESC;

-- ============================================================
-- Q2 - REVENUE BY PLAN
-- GROUP BY
-- ============================================================

SELECT
    PlanName,
    COUNT(*) AS SubscriptionCount,
    COALESCE(SUM(MRR), 0) AS TotalMRR,
    COALESCE(AVG(MRR), 0) AS AverageMRR
FROM saas_subscriptions
GROUP BY PlanName
ORDER BY TotalMRR DESC;

-- ============================================================
-- Q3 - INDUSTRIES WITH HIGH REVENUE
-- JOIN + GROUP BY + HAVING
-- ============================================================

SELECT
    c.Industry,
    COUNT(DISTINCT c.CustomerID) AS Customers,
    SUM(s.MRR) AS TotalMRR
FROM saas_customers AS c
INNER JOIN saas_subscriptions AS s
    ON c.CustomerID = s.CustomerID
GROUP BY c.Industry
HAVING SUM(s.MRR) > 5000
ORDER BY TotalMRR DESC;

-- ============================================================
-- Q4 - CUSTOMER VALUE CATEGORY
-- CASE
-- ============================================================

SELECT
    c.CustomerID,
    c.CompanyName,
    COALESCE(SUM(s.MRR), 0) AS TotalMRR,
    CASE
        WHEN COALESCE(SUM(s.MRR), 0) >= 1000 THEN 'High Value'
        WHEN COALESCE(SUM(s.MRR), 0) >= 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS CustomerValue
FROM saas_customers AS c
LEFT JOIN saas_subscriptions AS s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName
ORDER BY TotalMRR DESC;

-- ============================================================
-- Q5 - CUSTOMERS ABOVE AVERAGE CUSTOMER MRR
-- SUBQUERY + GROUP BY
--
-- Correction:
-- The average is calculated at CUSTOMER level, rather than
-- comparing customer totals with the average individual
-- subscription MRR.
-- ============================================================

SELECT
    c.CustomerID,
    c.CompanyName,
    SUM(s.MRR) AS TotalMRR
FROM saas_customers AS c
INNER JOIN saas_subscriptions AS s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName
HAVING SUM(s.MRR) > (
    SELECT AVG(CustomerMRR)
    FROM (
        SELECT
            CustomerID,
            SUM(MRR) AS CustomerMRR
        FROM saas_subscriptions
        GROUP BY CustomerID
    ) AS customer_totals
)
ORDER BY TotalMRR DESC;

-- ============================================================
-- Q6 - CUSTOMER USAGE SUMMARY
-- CTE + JOIN
-- ============================================================

WITH usage_summary AS (
    SELECT
        CustomerID,
        AVG(Logins) AS AverageLogins,
        AVG(ActiveUsers) AS AverageActiveUsers,
        AVG(SessionMinutes) AS AverageSessionMinutes
    FROM saas_usage
    GROUP BY CustomerID
)
SELECT
    c.CustomerID,
    c.CompanyName,
    ROUND(u.AverageLogins, 2) AS AverageLogins,
    ROUND(u.AverageActiveUsers, 2) AS AverageActiveUsers,
    ROUND(u.AverageSessionMinutes, 2) AS AverageSessionMinutes
FROM saas_customers AS c
INNER JOIN usage_summary AS u
    ON c.CustomerID = u.CustomerID
ORDER BY u.AverageLogins DESC;

-- ============================================================
-- Q7 - RANK CUSTOMERS BY MRR
-- WINDOW FUNCTION
-- ============================================================

WITH customer_revenue AS (
    SELECT
        c.CustomerID,
        c.CompanyName,
        SUM(s.MRR) AS TotalMRR
    FROM saas_customers AS c
    INNER JOIN saas_subscriptions AS s
        ON c.CustomerID = s.CustomerID
    GROUP BY
        c.CustomerID,
        c.CompanyName
)
SELECT
    CustomerID,
    CompanyName,
    TotalMRR,
    RANK() OVER (ORDER BY TotalMRR DESC) AS RevenueRank
FROM customer_revenue
ORDER BY RevenueRank, CustomerID;

-- ============================================================
-- Q8 - FIND ORPHAN SUBSCRIPTIONS
-- LEFT JOIN + ORPHAN RECORD HANDLING
-- ============================================================

SELECT
    s.SubscriptionID,
    s.CustomerID,
    s.PlanName,
    s.MRR
FROM saas_subscriptions AS s
LEFT JOIN saas_customers AS c
    ON s.CustomerID = c.CustomerID
WHERE c.CustomerID IS NULL;

-- ============================================================
-- Q9 - CHURN / SUBSCRIPTION STATUS SUMMARY
-- GROUP BY + CASE
-- ============================================================

SELECT
    CASE
        WHEN Status IS NULL OR TRIM(Status) = '' THEN 'Unknown'
        ELSE Status
    END AS SubscriptionStatus,
    COUNT(*) AS SubscriptionCount,
    SUM(MRR) AS TotalMRR,
    AVG(MRR) AS AverageMRR
FROM saas_subscriptions
GROUP BY
    CASE
        WHEN Status IS NULL OR TRIM(Status) = '' THEN 'Unknown'
        ELSE Status
    END
ORDER BY SubscriptionCount DESC;

-- ============================================================
-- Q10 - CUSTOMER SUPPORT TICKET SUMMARY
-- JOIN + GROUP BY
-- ============================================================

SELECT
    c.CustomerID,
    c.CompanyName,
    COUNT(t.TicketID) AS TicketCount,
    ROUND(AVG(t.ResolutionHours), 2) AS AvgResolutionHours,
    ROUND(AVG(t.SatisfactionScore), 2) AS AvgSatisfactionScore
FROM saas_customers AS c
LEFT JOIN saas_tickets AS t
    ON c.CustomerID = t.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName
ORDER BY TicketCount DESC;

-- ============================================================
-- END OF MODULE 10
-- ============================================================
