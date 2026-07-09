-- Top 5 largest expenses in the period
SELECT
    t.date,
    t.description,
    c.name AS category,
    o.name AS origin,
    t.value
FROM transactions t
JOIN categories c ON t.category_id = c.id
JOIN origins o ON t.origin_id = o.id
WHERE t.type = 'expense'
ORDER BY t.value DESC
LIMIT 5;
