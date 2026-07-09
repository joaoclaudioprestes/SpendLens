-- Total expenses grouped by category and month
SELECT
    strftime('%Y-%m', t.date) AS month,
    c.name AS category,
    COUNT(*) AS count,
    SUM(t.value) AS total
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.type = 'expense'
GROUP BY strftime('%Y-%m', t.date), c.name
ORDER BY month DESC, total DESC;
