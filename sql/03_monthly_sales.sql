-- Revenu par année-mois de commande, après remise et hors taxe.
-- Arrondir chaque ligne au centime avant de sommer ; garder les entiers.
CREATE VIEW IF NOT EXISTS monthly_sales AS
WITH monthly AS (
    SELECT
        printf('%04d-%02d', d.year, d.month) AS period,
        COUNT(*) AS sales_lines,
        SUM(f.quantity) AS quantity,
        SUM((f.extended_price_cents * (100 - f.discount_percent) + 50) / 100)
            AS revenue_cents
    FROM fact_sales AS f
    JOIN dim_date AS d ON d.date_id = f.date_id
    GROUP BY d.year, d.month
)
SELECT
    period,
    sales_lines,
    quantity,
    revenue_cents,
    -- Affichage exact à deux décimales, sans conversion flottante.
    printf('%d.%02d', revenue_cents / 100, revenue_cents % 100) AS revenue,
    CASE
        WHEN period = (SELECT substr(MAX(date_id), 1, 7) FROM dim_date)
            THEN 'potentiellement partiel'
        ELSE ''
    END AS period_note
FROM monthly
ORDER BY period;
