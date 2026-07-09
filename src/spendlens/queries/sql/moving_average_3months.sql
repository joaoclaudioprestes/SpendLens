-- 3-month moving average of expenses per category
WITH monthly_totals AS (
    SELECT
        strftime('%Y-%m', t.date) AS month,
        c.name AS category,
        SUM(t.value) AS total
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    WHERE t.type = 'expense'
    GROUP BY strftime('%Y-%m', t.date), c.name
)
SELECT
    month,
    category,
    total,
    ROUND(AVG(total) OVER (
        PARTITION BY category
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3m
FROM monthly_totals
ORDER BY month DESC, category;
