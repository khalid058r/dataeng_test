"""Tests des classements et de la comparaison de périodes."""

from collections import Counter, defaultdict
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from etl.export_reports import REPORT_QUERIES, export_reports
from etl.load_sources import load_sources


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def report_db():
    """Préparer les dimensions et les vues dans une base en mémoire."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    for filename in ("02_star_schema.sql", "03_monthly_sales.sql", "04_business_reports.sql"):
        connection.executescript((ROOT / "sql" / filename).read_text(encoding="utf-8"))
    connection.executemany("INSERT INTO dim_customer VALUES (?, ?, ?, ?, ?)", [
        (i, f"Client {i}", "BUILDING", i - 1 if i <= 6 else 0,
         f"Pays {i - 1 if i <= 6 else 0}") for i in range(1, 9)
    ])
    connection.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?)", [
        ("1997-11-01", 1997, 11, 1), ("1997-12-01", 1997, 12, 1),
        ("1998-01-01", 1998, 1, 1), ("1998-02-01", 1998, 2, 1),
        ("1998-03-02", 1998, 3, 2),
    ])
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def ranked_sales(report_db):
    """Ajouter des ventes avec égalités pour tester les classements."""
    modes = ("AIR", "AIR", "MAIL", "MAIL", "RAIL")
    report_db.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (i, 1, i, "1998-01-01", 10 if i == 1 else 1, 100, 0, modes[i - 1])
        for i in range(1, 6)
    ] + [
        (6, line, 6, "1998-01-01", 100, 10, 0, "RAIL") for line in range(1, 11)
    ] + [(7, 1, 7, "1998-01-01", 1, 50, 0, "SHIP")])
    return report_db


def test_top_five_aggregate_clients_and_break_country_ties(ranked_sales):
    assert ranked_sales.execute(
        "SELECT nation_id, revenue_cents FROM top_5_nations ORDER BY revenue_cents DESC, nation_id"
    ).fetchall() == [(0, 150), (1, 100), (2, 100), (3, 100), (4, 100)]
    assert ranked_sales.execute(
        "SELECT SUM(sales_lines), SUM(quantity), SUM(revenue_cents) FROM sales_by_nation"
    ).fetchone() == (16, 1015, 650)


def test_shipping_counts_lines_of_top_five_globally_and_keeps_ties(ranked_sales):
    # Le sixième pays est exclu, même si RAIL y domine.
    # AIR et MAIL ont deux lignes chacun, sans pondérer la quantité.
    assert ranked_sales.execute("SELECT * FROM top_shipping_modes ORDER BY ship_mode").fetchall() == [
        ("AIR", 2), ("MAIL", 2),
    ]


def test_customer_rankings_have_different_measures_and_stable_ties(ranked_sales):
    assert ranked_sales.execute(
        "SELECT customer_id FROM customers_by_revenue ORDER BY position"
    ).fetchall() == [(i,) for i in (1, 2, 3, 4, 5, 6, 7)]
    assert ranked_sales.execute(
        "SELECT customer_id FROM customers_by_quantity ORDER BY position"
    ).fetchall() == [(i,) for i in (6, 1, 2, 3, 4, 5, 7)]
    # Le client 8 n'a pas de vente.
    assert ranked_sales.execute("SELECT COUNT(*) FROM sales_by_customer").fetchone()[0] == 7


def test_best_months_keep_year_and_break_ties_chronologically(ranked_sales):
    ranked_sales.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (20, 1, 1, "1997-12-01", 1, 650, 0, "AIR"),
        (21, 1, 1, "1998-02-01", 1, 1000, 0, "AIR"),
    ])
    assert ranked_sales.execute(
        "SELECT position, period, revenue_cents FROM best_sales_months ORDER BY position"
    ).fetchall() == [(1, "1998-02", 1000), (2, "1997-12", 650), (3, "1998-01", 650)]


@pytest.mark.parametrize(("previous", "current", "difference", "percent", "status"), [
    (100, 125, 25, "25.00", "ok"),
    (100, 0, -100, "-100.00", "ok"),
    (0, 200, 200, None, "base précédente nulle"),
    (0, 0, 0, None, "base précédente nulle"),
    (None, 200, None, None, "période absente"),
    (100, None, None, None, "période absente"),
    (None, None, None, None, "période absente"),
])
def test_comparison_keeps_missing_periods_distinct_from_zero(
    report_db, previous, current, difference, percent, status,
):
    for order, (month, revenue) in enumerate((("1998-01-01", previous), ("1998-02-01", current)), 1):
        if revenue is not None:
            report_db.execute(
                "INSERT INTO fact_sales VALUES (?, 1, 1, ?, 1, ?, 0, 'AIR')", (order, month, revenue)
            )
    # Ignorer mars, même si son revenu est le plus élevé.
    report_db.execute("INSERT INTO fact_sales VALUES (3, 1, 1, '1998-03-02', 1, 99999, 0, 'AIR')")
    assert report_db.execute("SELECT * FROM period_comparison").fetchone() == (
        "1998-02", "1998-01", current, previous, difference, percent, status,
    )


def test_comparison_crosses_year_boundary(report_db):
    report_db.execute("DELETE FROM dim_date WHERE date_id > '1998-01-01'")
    report_db.executemany("INSERT INTO fact_sales VALUES (?, 1, 1, ?, 1, ?, 0, 'AIR')", [
        (1, "1997-11-01", 200), (2, "1997-12-01", 250),
    ])
    assert report_db.execute("SELECT * FROM period_comparison").fetchone() == (
        "1997-12", "1997-11", 250, 200, 50, "25.00", "ok",
    )


def test_empty_data_and_fewer_than_five_countries(report_db):
    for name in REPORT_QUERIES:
        rows = report_db.execute(REPORT_QUERIES[name]).fetchall()
        assert len(rows) == (1 if name == "period_comparison" else 0)
    report_db.execute("INSERT INTO fact_sales VALUES (1, 1, 1, '1998-01-01', 1, 100, 0, 'AIR')")
    assert report_db.execute("SELECT nation_id FROM top_5_nations").fetchall() == [(0,)]
    assert report_db.execute("SELECT * FROM top_shipping_modes").fetchall() == [("AIR", 1)]


def read_records(name):
    """Lire un fichier source pour calculer les résultats attendus."""
    with (ROOT / "data" / f"{name}.tbl").open(encoding="ascii", newline="") as source:
        return list(csv.reader(source, delimiter="|", quoting=csv.QUOTE_NONE))


def test_supplied_business_reports_and_exports_against_files(tmp_path):
    database = tmp_path / "warehouse.sqlite"
    load_sources(ROOT / "data", database)
    nations = {int(row[0]): row[1] for row in read_records("nation")}
    customers = {int(row[0]): (row[1], int(row[3])) for row in read_records("customer")}
    orders = {int(row[0]): (int(row[1]), row[4][:7]) for row in read_records("orders")}
    customer_totals = defaultdict(lambda: [0, 0, 0])
    nation_totals = defaultdict(lambda: [0, 0, 0])
    month_revenues = Counter()
    shipping = Counter()
    for row in read_records("lineitem"):
        customer, month = orders[int(row[0])]
        nation = customers[customer][1]
        quantity = int(row[4])
        revenue = int((Decimal(row[5]) * (1 - Decimal(row[6]))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ) * 100)
        for totals in (customer_totals[customer], nation_totals[nation]):
            totals[0] += 1
            totals[1] += quantity
            totals[2] += revenue
        month_revenues[month] += revenue
        shipping[nation, row[14]] += 1
    top_nations = sorted(nation_totals, key=lambda key: (-nation_totals[key][2], key))[:5]
    modes = Counter()
    for (nation, mode), count in shipping.items():
        if nation in top_nations:
            modes[mode] += count
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT nation_id, nation_name, sales_lines, quantity, revenue_cents "
            "FROM top_5_nations ORDER BY revenue_cents DESC, nation_id"
        ).fetchall() == [(key, nations[key], *nation_totals[key]) for key in top_nations]
        assert connection.execute("SELECT * FROM top_shipping_modes ORDER BY ship_mode").fetchall() == [
            (mode, count) for mode, count in sorted(modes.items()) if count == max(modes.values())
        ]
        assert connection.execute(
            "SELECT period, revenue_cents FROM best_sales_months ORDER BY position"
        ).fetchall() == sorted(month_revenues.items(), key=lambda item: (-item[1], item[0]))
        for measure, view in ((2, "customers_by_revenue"), (1, "customers_by_quantity")):
            keys = sorted(customer_totals, key=lambda key: (-customer_totals[key][measure], key))
            assert connection.execute(
                f"SELECT customer_id, sales_lines, quantity, revenue_cents FROM {view} ORDER BY position"
            ).fetchall() == [(key, *customer_totals[key]) for key in keys]
        current, previous = month_revenues["1998-07"], month_revenues["1998-06"]
        percent = (Decimal(100) * (current - previous) / previous).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert connection.execute("SELECT * FROM period_comparison").fetchone() == (
            "1998-07", "1998-06", current, previous, current - previous, str(percent), "ok",
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    output = tmp_path / "reports"
    counts = export_reports(database, output)
    first_exports = {name: (output / f"{name}.csv").read_bytes() for name in counts}
    assert counts["top_5_nations"] == 5
    assert counts["period_comparison"] == 1
    assert counts["customers_by_revenue"] == len(customer_totals)
    assert export_reports(database, output) == counts
    assert {name: (output / f"{name}.csv").read_bytes() for name in counts} == first_exports
    with (output / "period_comparison.csv").open(encoding="utf-8", newline="") as source:
        assert list(csv.DictReader(source))[0]["change_percent"] == str(percent)


def test_export_missing_database_does_not_create_it_or_publish_files(tmp_path):
    database = tmp_path / "absent.sqlite"
    output = tmp_path / "reports"
    result = subprocess.run([
        sys.executable, str(ROOT / "etl/export_reports.py"),
        "--database", str(database), "--output-dir", str(output),
    ], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert "ERREUR" in result.stderr
    assert not database.exists()
    assert not output.exists()
