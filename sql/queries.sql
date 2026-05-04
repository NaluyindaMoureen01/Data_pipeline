-- queries.sql

-- Q1: TOP INVENTORS (most patents)

SELECT
    i.name,
    i.country,
    COUNT(DISTINCT r.patent_id) AS patent_count
FROM relationships r
JOIN inventors i ON r.inventor_id = i.inventor_id
WHERE r.inventor_id != ''
GROUP BY i.inventor_id
ORDER BY patent_count DESC
LIMIT 20;

-- Q2: TOP COMPANIES (most patents owned)

SELECT
    c.name,
    COUNT(DISTINCT r.patent_id) AS patent_count
FROM relationships r
JOIN companies c ON r.company_id = c.company_id
WHERE r.company_id != ''
GROUP BY c.company_id
ORDER BY patent_count DESC
LIMIT 20;

-- Q3: TOP COUNTRIES (by inventor country)

SELECT
    i.country,
    COUNT(DISTINCT r.patent_id) AS patent_count,
    ROUND(
        100.0 * COUNT(DISTINCT r.patent_id) /
        (SELECT COUNT(DISTINCT patent_id) FROM relationships WHERE inventor_id != ''),
        2
    ) AS share_pct
FROM relationships r
JOIN inventors i ON r.inventor_id = i.inventor_id
WHERE r.inventor_id != ''
  AND i.country != 'Unknown'
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 20;

-- Q4: TRENDS OVER TIME (patents per year)

SELECT
    year,
    COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
  AND year BETWEEN 1976 AND 2025
GROUP BY year
ORDER BY year;

-- Q5: JOIN QUERY
-- Patents with their inventors AND companies

SELECT
    p.patent_id,
    p.title,
    p.year,
    i.name   AS inventor_name,
    i.country AS inventor_country,
    c.name   AS company_name
FROM patents p
JOIN relationships r ON p.patent_id = r.patent_id
JOIN inventors i     ON r.inventor_id = i.inventor_id
JOIN companies c     ON r.company_id  = c.company_id
WHERE r.inventor_id != ''
  AND r.company_id  != ''
ORDER BY p.year DESC
LIMIT 100;

-- Q6: CTE QUERY
-- Average patents per inventor, then show
-- inventors above that average

WITH inventor_counts AS (
    -- Step 1: count patents per inventor
    SELECT
        r.inventor_id,
        i.name,
        i.country,
        COUNT(DISTINCT r.patent_id) AS patent_count
    FROM relationships r
    JOIN inventors i ON r.inventor_id = i.inventor_id
    WHERE r.inventor_id != ''
    GROUP BY r.inventor_id
),
avg_count AS (
    -- Step 2: calculate the overall average
    SELECT AVG(patent_count) AS avg_patents
    FROM inventor_counts
)
-- Step 3: filter to above-average inventors
SELECT
    ic.name,
    ic.country,
    ic.patent_count,
    ROUND(ac.avg_patents, 2) AS avg_all_inventors
FROM inventor_counts ic
CROSS JOIN avg_count ac
WHERE ic.patent_count > ac.avg_patents
ORDER BY ic.patent_count DESC
LIMIT 50;

-- Q7: RANKING QUERY (window function)
-- Rank inventors within each country

WITH inventor_counts AS (
    SELECT
        i.inventor_id,
        i.name,
        i.country,
        COUNT(DISTINCT r.patent_id) AS patent_count
    FROM relationships r
    JOIN inventors i ON r.inventor_id = i.inventor_id
    WHERE r.inventor_id != ''
      AND i.country != 'Unknown'
    GROUP BY i.inventor_id
)
SELECT
    country,
    name,
    patent_count,
    RANK()       OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
    DENSE_RANK() OVER (ORDER BY patent_count DESC)                      AS global_rank,
    NTILE(4)     OVER (ORDER BY patent_count DESC)                      AS quartile
FROM inventor_counts
ORDER BY country, country_rank
LIMIT 200;
