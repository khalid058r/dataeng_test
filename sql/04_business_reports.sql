-- Les vues calculent le revenu après remise, arrondi par ligne, hors taxe.
-- Les montants restent des centimes entiers ; le pays est celui du client.

CREATE VIEW IF NOT EXISTS sales_by_customer AS
SELECT c.customer_id, c.customer_name, c.nation_id, c.nation_name,
       COUNT(*) AS sales_lines, SUM(f.quantity) AS quantity,
       SUM((f.extended_price_cents * (100 - f.discount_percent) + 50) / 100)
           AS revenue_cents
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.customer_id, c.customer_name, c.nation_id, c.nation_name;

CREATE VIEW IF NOT EXISTS sales_by_nation AS
SELECT nation_id, nation_name, SUM(sales_lines) AS sales_lines,
       SUM(quantity) AS quantity, SUM(revenue_cents) AS revenue_cents
FROM sales_by_customer
GROUP BY nation_id, nation_name;

-- 1. Exactement cinq pays au maximum, départagés par code pays.
CREATE VIEW IF NOT EXISTS top_5_nations AS
SELECT * FROM sales_by_nation
ORDER BY revenue_cents DESC, nation_id
LIMIT 5;

-- 2. Fréquence globale des lignes de ces cinq pays, tous les ex æquo inclus.
CREATE VIEW IF NOT EXISTS top_shipping_modes AS
WITH top_countries AS MATERIALIZED (
    -- Calculer une fois les cinq pays avant de parcourir les lignes de vente.
    SELECT nation_id FROM top_5_nations
), modes AS MATERIALIZED (
    SELECT f.ship_mode, COUNT(*) AS sales_lines
    FROM fact_sales f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN top_countries n ON n.nation_id = c.nation_id
    GROUP BY f.ship_mode
)
SELECT ship_mode, sales_lines FROM modes
WHERE sales_lines = (SELECT MAX(sales_lines) FROM modes)
ORDER BY ship_mode;

-- 3. Classement des années-mois, y compris le dernier mois signalé comme partiel.
CREATE VIEW IF NOT EXISTS best_sales_months AS
SELECT ROW_NUMBER() OVER (ORDER BY revenue_cents DESC, period) AS position,
       period, sales_lines, quantity, revenue_cents, revenue, period_note
FROM monthly_sales
ORDER BY position;

-- 4. Deux classements de tous les clients ayant des lignes de vente.
CREATE VIEW IF NOT EXISTS customers_by_revenue AS
SELECT ROW_NUMBER() OVER (ORDER BY revenue_cents DESC, customer_id) AS position, *
FROM sales_by_customer
ORDER BY position;

CREATE VIEW IF NOT EXISTS customers_by_quantity AS
SELECT ROW_NUMBER() OVER (ORDER BY quantity DESC, customer_id) AS position, *
FROM sales_by_customer
ORDER BY position;

-- 5. Les deux mois précédant celui de la dernière date de commande.
-- Une absence reste NULL ; une période présente à revenu nul reste zéro.
CREATE VIEW IF NOT EXISTS period_comparison AS
WITH periods AS (
    SELECT substr(date(MAX(date_id), 'start of month', '-1 month'), 1, 7) AS current_period,
           substr(date(MAX(date_id), 'start of month', '-2 months'), 1, 7) AS previous_period
    FROM dim_date
), totals AS (
    SELECT p.current_period, p.previous_period,
           c.revenue_cents AS current_revenue_cents,
           b.revenue_cents AS previous_revenue_cents
    FROM periods p
    LEFT JOIN monthly_sales c ON c.period = p.current_period
    LEFT JOIN monthly_sales b ON b.period = p.previous_period
)
SELECT *,
       current_revenue_cents - previous_revenue_cents AS difference_cents,
       CASE WHEN previous_revenue_cents > 0 AND current_revenue_cents IS NOT NULL
            THEN printf('%.2f', 100.0 * (current_revenue_cents - previous_revenue_cents)
                                     / previous_revenue_cents)
       END AS change_percent,
       CASE WHEN current_revenue_cents IS NULL OR previous_revenue_cents IS NULL
                THEN 'période absente'
            WHEN previous_revenue_cents = 0 THEN 'base précédente nulle'
            ELSE 'ok'
       END AS status
FROM totals;
