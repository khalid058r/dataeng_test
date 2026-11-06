"""Tests du rapport mensuel et de ses arrondis."""

from collections import defaultdict
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sqlite3

import pytest

from etl.load_sources import load_sources


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def connection():
    """Préparer l'étoile et le rapport dans une base en mémoire."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((ROOT / "sql/02_star_schema.sql").read_text(encoding="utf-8"))
    conn.executescript((ROOT / "sql/03_monthly_sales.sql").read_text(encoding="utf-8"))
    conn.execute("INSERT INTO dim_customer VALUES (1, 'Alice', 'BUILDING', 0, 'ALGERIA')")
    conn.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?)", [
        ("1997-01-31", 1997, 1, 31),
        ("1998-01-01", 1998, 1, 1),
        ("1998-02-01", 1998, 2, 1),  # Aucune vente en février.
        ("1998-03-02", 1998, 3, 2),
    ])
    try:
        yield conn
    finally:
        conn.close()


def test_manual_monthly_totals_and_rounding(connection):
    connection.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 1, 1, "1997-01-31", 2, 1005, 10, "AIR"),  # 9,045 -> 9,05.
        (1, 2, 1, "1997-01-31", 1, 500, 0, "MAIL"),
        (2, 1, 1, "1998-01-01", 1, 5, 10, "AIR"),    # 0,045 -> 0,05.
        (2, 2, 1, "1998-01-01", 1, 5, 10, "AIR"),
        (3, 1, 1, "1998-03-02", 4, 2000, 100, "AIR"), # Vente à revenu nul.
    ])
    assert connection.execute("SELECT * FROM monthly_sales ORDER BY period").fetchall() == [
        ("1997-01", 2, 3, 1405, "14.05", ""),
        ("1998-01", 2, 2, 10, "0.10", ""),
        ("1998-03", 1, 4, 0, "0.00", "potentiellement partiel"),
    ]


def test_no_sales_returns_no_months(connection):
    assert connection.execute("SELECT * FROM monthly_sales").fetchall() == []


def test_partial_note_uses_last_order_month_even_without_sales(connection):
    connection.execute(
        "INSERT INTO fact_sales VALUES (1, 1, 1, '1998-01-01', 1, 100, 0, 'AIR')"
    )
    assert connection.execute("SELECT period, period_note FROM monthly_sales").fetchall() == [
        ("1998-01", ""),
    ]


def test_revenue_display_keeps_exact_cents_for_large_totals(connection):
    connection.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 1, 1, "1998-01-01", 1, 9_007_199_254_740_991, 0, "AIR"),
        (1, 2, 1, "1998-01-01", 1, 9_007_199_254_740_991, 0, "AIR"),
    ])
    assert connection.execute(
        "SELECT revenue_cents, revenue, typeof(revenue_cents) FROM monthly_sales"
    ).fetchone() == (18_014_398_509_481_982, "180143985094819.82", "integer")


def test_supplied_months_match_independent_file_calculation(tmp_path):
    database = tmp_path / "warehouse.sqlite"
    load_sources(ROOT / "data", database)
    with (ROOT / "data/orders.tbl").open(encoding="ascii", newline="") as source:
        order_months = {
            int(row[0]): row[4][:7]
            for row in csv.reader(source, delimiter="|", quoting=csv.QUOTE_NONE)
        }
    expected = defaultdict(lambda: [0, 0, 0])
    with (ROOT / "data/lineitem.tbl").open(encoding="ascii", newline="") as source:
        for row in csv.reader(source, delimiter="|", quoting=csv.QUOTE_NONE):
            totals = expected[order_months[int(row[0])]]
            totals[0] += 1
            totals[1] += int(row[4])
            totals[2] += int((Decimal(row[5]) * (1 - Decimal(row[6]))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ) * 100)
    with sqlite3.connect(database) as conn:
        rows = conn.execute(
            "SELECT period, sales_lines, quantity, revenue_cents FROM monthly_sales ORDER BY period"
        ).fetchall()
        assert rows == [(month, *totals) for month, totals in sorted(expected.items())]
        assert conn.execute(
            "SELECT period FROM monthly_sales WHERE period_note != ''"
        ).fetchall() == [(max(order_months.values()),)]
        assert conn.execute("SELECT SUM(revenue_cents) FROM monthly_sales").fetchone()[0] == 204_513_495_230
