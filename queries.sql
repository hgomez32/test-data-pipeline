-- 1. Engine lifetimes
SELECT unit, MAX(cycle) AS cycles_to_failure
FROM readings
GROUP BY unit
ORDER BY cycles_to_failure DESC;

-- 2. CTE: engines that failed earlier than average
WITH life AS (
    SELECT unit, MAX(cycle) AS cycles FROM readings GROUP BY unit
)
SELECT unit, cycles
FROM life
WHERE cycles < (SELECT AVG(cycles) FROM life);

-- 3. Window function: 5-cycle rolling average of sensor 11
SELECT unit, cycle, s11,
       AVG(s11) OVER (
           PARTITION BY unit ORDER BY cycle
           ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
       ) AS s11_rolling_avg
FROM readings;

-- 4. LAG: cycle-over-cycle change in sensor 11
SELECT unit, cycle, s11,
       s11 - LAG(s11) OVER (PARTITION BY unit ORDER BY cycle) AS change_from_prev
FROM readings;

-- 5. Engines with the most flagged readings
SELECT unit, SUM(outlier_flag) AS flagged
FROM readings
GROUP BY unit
HAVING flagged > 0
ORDER BY flagged DESC;