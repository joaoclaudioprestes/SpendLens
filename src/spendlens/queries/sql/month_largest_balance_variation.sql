-- Month with the largest balance variation (income - expenses)
WITH monthly_balance AS (
    SELECT
        strftime('%Y-%m', t.date) AS month,
        SUM(CASE WHEN t.type = 'receita' THEN t.value ELSE 0 END) AS income,
        SUM(CASE WHEN t.type = 'despesa' THEN t.value ELSE 0 END) AS expenses,
        SUM(CASE WHEN t.type = 'receita' THEN t.value ELSE -t.value END) AS balance
    FROM transactions t
    GROUP BY strftime('%Y-%m', t.date)
)
SELECT
    month,
    income,
    expenses,
    balance,
    ABS(balance) AS abs_variation
FROM monthly_balance
ORDER BY abs_variation DESC;
