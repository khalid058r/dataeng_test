Implement a reproducible Python/SQLite ETL and reporting solution

This solution loads NATION, CUSTOMER, ORDERS and LINEITEM, builds customer and continuous date dimensions, and creates one sales fact per order line. SQL views answer all five business questions; seven CSV exports provide reproducible results. Amounts use integer cents with rounding per line, and failed loads restore the previous validated database.

The submission also includes both Python coding exercises, a cron-ready launcher with logging and mutual exclusion, and documentation covering setup, scheduling, deployment, production evolution and compound data growth. The original exercise is preserved in the README.

Validation:

- Fresh Python 3.12 environment installed from `requirements.txt`; dependency check succeeds.
- 109 tests pass, including source validation, atomic migrations, reports, coding exercises and launcher failures or overlapping runs.
- A new database loads 25 nations, 1,500 customers, 15,000 orders and 60,175 line items; dimensions contain 1,500 customers and 2,406 dates, with 60,175 sales facts.
- Repeated execution preserves the contents of all seven tables and all seven CSV exports. SQLite integrity and foreign-key checks pass.
- The updated submission archive was extracted and checked again: 109 tests pass, the launcher works from another directory, and all seven Datasette HTML/CSV reports match the SQL exports.

The implementation performs full refreshes on one Linux host. Streaming, Docker and the remaining optional data enrichment bonuses are deferred. Run instructions and report definitions are linked from the root README.
