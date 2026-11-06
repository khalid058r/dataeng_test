-- Grain des faits : une ligne de commande (commande + numéro de ligne).
-- Le revenu sera calculé dans les rapports, sans colonne bonus persistée.

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id INTEGER PRIMARY KEY CHECK (customer_id > 0),
    customer_name TEXT NOT NULL CHECK (length(trim(customer_name)) > 0),
    market_segment TEXT NOT NULL CHECK (length(trim(market_segment)) > 0),
    nation_id INTEGER NOT NULL CHECK (nation_id >= 0),
    nation_name TEXT NOT NULL CHECK (length(trim(nation_name)) > 0)
) STRICT;

CREATE TABLE IF NOT EXISTS dim_date (
    date_id TEXT PRIMARY KEY NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1 AND 9999),
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),
    CHECK (date_id = printf('%04d-%02d-%02d', year, month, day))
) STRICT;

CREATE TABLE IF NOT EXISTS fact_sales (
    order_id INTEGER NOT NULL CHECK (order_id > 0),
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    customer_id INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    date_id TEXT NOT NULL REFERENCES dim_date(date_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    extended_price_cents INTEGER NOT NULL CHECK (extended_price_cents >= 0),
    discount_percent INTEGER NOT NULL CHECK (discount_percent BETWEEN 0 AND 100),
    ship_mode TEXT NOT NULL CHECK (length(trim(ship_mode)) > 0),
    PRIMARY KEY (order_id, line_number)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(date_id);
