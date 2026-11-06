"""Tests du chargement et de la reprise après erreur."""

import csv
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from etl.load_sources import APPLICATION_ID, LoadError, SCHEMA_VERSION, SOURCE_COLUMNS, load_file, load_sources


ROOT = Path(__file__).resolve().parents[1]


def write_files(data_dir, rows, trailing=True):
    """Écrire les petits fichiers utilisés par les tests."""
    data_dir.mkdir(exist_ok=True)
    for table, records in rows.items():
        content = "".join(
            "|".join(record) + ("|" if trailing else "") + "\n"
            for record in records
        )
        (data_dir / f"{table}.tbl").write_text(content, encoding="ascii")


@pytest.fixture
def source(tmp_path):
    """Fournir un lot modifiable et le chemin de sa base temporaire."""
    rows = {
        "nation": [
            ["0", "ALGERIA", "0", "pays"],
            ["1", "ARGENTINA", "1", "pays"],
        ],
        "customer": [
            ["1", "Alice", "Adresse", "0", "01-23", "-12.34", "BUILDING", " client "],
            ["2", "Bob", "Adresse", "1", "04-56", "25.00", "MACHINERY", "client sans commande"],
        ],
        "orders": [
            ["10", "1", "O", "15.05", "1998-07-01", "1-URGENT", "Clerk#1", "0", "commande"],
            ["11", "1", "F", "20.00", "1998-06-01", "2-HIGH", "Clerk#1", "0", "commande"],
        ],
        "lineitem": [
            ["10", "1", "1", "1", "2", "10.05", "0.10", "0.02", "N", "O",
             "1998-07-02", "1998-07-03", "1998-07-04", "DELIVER IN PERSON", "AIR", "ligne"],
            ["10", "1", "1", "2", "1", "5.00", "0.00", "0.00", "R", "F",
             "1998-07-02", "1998-07-03", "1998-07-04", "DELIVER IN PERSON", "MAIL", "ligne"],
            ["11", "1", "1", "1", "1", "20.00", "0.05", "0.08", "N", "F",
             "1998-06-02", "1998-06-03", "1998-06-04", "DELIVER IN PERSON", "AIR", "ligne"],
        ],
    }
    data_dir = tmp_path / "data"
    database = tmp_path / "out" / "sources.sqlite"
    write_files(data_dir, rows)
    return data_dir, database, rows


def snapshot(database):
    """Lire les tables pour comparer deux chargements."""
    with sqlite3.connect(database) as conn:
        return {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
            for table in (*SOURCE_COLUMNS, "dim_customer", "dim_date", "fact_sales")
        }


@pytest.mark.parametrize("trailing", [True, False])
def test_load_and_reload_preserve_values(source, trailing):
    data_dir, database, rows = source
    write_files(data_dir, rows, trailing)
    expected_counts = {
        "nation": 2, "customer": 2, "orders": 2, "lineitem": 3,
        "dim_customer": 2, "dim_date": 31, "fact_sales": 3,
    }
    assert load_sources(data_dir, database) == expected_counts
    before = snapshot(database)
    assert load_sources(data_dir, database) == expected_counts
    assert snapshot(database) == before
    with sqlite3.connect(database) as conn:
        assert conn.execute(
            "SELECT C_ACCTBAL_CENTS, C_PHONE, C_COMMENT FROM customer WHERE C_CUSTKEY = 1"
        ).fetchone() == (-1234, "01-23", " client ")
        assert conn.execute(
            "SELECT L_QUANTITY, L_EXTENDEDPRICE_CENTS, L_DISCOUNT_PERCENT, L_TAX_PERCENT "
            "FROM lineitem WHERE L_ORDERKEY = 10 AND L_LINENUMBER = 1"
        ).fetchone() == (2, 1005, 10, 2)
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute(
            "SELECT COUNT(*) FROM orders o JOIN customer c ON c.C_CUSTKEY = o.O_CUSTKEY "
            "JOIN lineitem l ON l.L_ORDERKEY = o.O_ORDERKEY"
        ).fetchone()[0] == 3
        assert conn.execute(
            "SELECT COUNT(*) FROM customer c WHERE NOT EXISTS "
            "(SELECT 1 FROM orders o WHERE o.O_CUSTKEY = c.C_CUSTKEY)"
        ).fetchone()[0] == 1


@pytest.mark.parametrize(("balance", "expected_cents"), [
    ("92233720368547758.07", 9223372036854775807),
    ("-92233720368547758.08", -9223372036854775808),
    ("1.00000000000000000000000000000", 100),
    ("-0.00", 0),
])
def test_exact_money_at_storage_limits(source, balance, expected_cents):
    data_dir, database, rows = source
    rows["customer"][0][5] = balance
    write_files(data_dir, rows)
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute(
            "SELECT C_ACCTBAL_CENTS FROM customer WHERE C_CUSTKEY = 1"
        ).fetchone()[0] == expected_cents


@pytest.mark.parametrize(("table", "column", "bad_value"), [
    ("nation", "N_NATIONKEY", "-1"),
    ("nation", "N_NAME", " "),
    ("nation", "N_REGIONKEY", "-1"),
    ("customer", "C_CUSTKEY", "1.5"),
    ("customer", "C_NATIONKEY", "999"),
    ("customer", "C_NAME", "  "),
    ("customer", "C_ACCTBAL", "1.001"),
    ("customer", "C_ACCTBAL", "1.00000000000000000000000000001"),
    ("customer", "C_ACCTBAL", "NaN"),
    ("customer", "C_ACCTBAL", "Infinity"),
    ("customer", "C_ACCTBAL", "92233720368547758.08"),
    ("orders", "O_ORDERDATE", "1998-02-30"),
    ("orders", "O_ORDERDATE", "19980701"),
    ("orders", "O_TOTALPRICE", "-0.01"),
    ("orders", "O_CUSTKEY", "999"),
    ("lineitem", "L_ORDERKEY", "999"),
    ("lineitem", "L_QUANTITY", "0"),
    ("lineitem", "L_QUANTITY", "1.5"),
    ("lineitem", "L_DISCOUNT", "1.01"),
    ("lineitem", "L_TAX", "-0.01"),
    ("lineitem", "L_DISCOUNT", "0.005"),
    ("lineitem", "L_EXTENDEDPRICE", "-1.00"),
    ("lineitem", "L_SHIPDATE", "1998-13-01"),
])
def test_invalid_value_reports_location_and_rolls_back(source, table, column, bad_value):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    before = snapshot(database)
    # Changer aussi un nom pour vérifier l'annulation complète.
    rows["customer"][1][1] = "Nom qui ne doit pas etre publie"
    index = list(SOURCE_COLUMNS[table]).index(column)
    rows[table][0][index] = bad_value
    write_files(data_dir, rows)
    with pytest.raises(LoadError) as error:
        load_sources(data_dir, database)
    assert f"{table}.tbl, ligne 1" in str(error.value)
    assert column in str(error.value)
    assert snapshot(database) == before


@pytest.mark.parametrize("table", ["nation", "customer", "orders", "lineitem"])
def test_duplicate_primary_key_is_not_silently_ignored(source, table):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    before = snapshot(database)
    rows[table].append(rows[table][0].copy())
    write_files(data_dir, rows)
    with pytest.raises(LoadError, match="UNIQUE constraint failed"):
        load_sources(data_dir, database)
    assert snapshot(database) == before


@pytest.mark.parametrize("extra", [True, False])
def test_wrong_field_count_rolls_back(source, extra):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    before = snapshot(database)
    if extra:
        rows["lineitem"][1].append("champ en trop")
    else:
        rows["lineitem"][1].pop()
    write_files(data_dir, rows, trailing=False)
    with pytest.raises(LoadError, match="lineitem.tbl, ligne 2.*colonnes attendues"):
        load_sources(data_dir, database)
    assert snapshot(database) == before


@pytest.mark.parametrize("table", ["nation", "lineitem"])
@pytest.mark.parametrize("problem", ["missing", "empty", "non_ascii"])
def test_unreadable_source_preserves_database(source, problem, table):
    data_dir, database, _ = source
    load_sources(data_dir, database)
    before = snapshot(database)
    path = data_dir / f"{table}.tbl"
    if problem == "missing":
        path.unlink()
    elif problem == "empty":
        path.write_text("")
    else:
        path.write_bytes(path.read_bytes() + b"\xff\n")
    with pytest.raises(LoadError, match=f"{table}.tbl"):
        load_sources(data_dir, database)
    assert snapshot(database) == before


def test_first_failed_load_rolls_back_schema_creation(source):
    data_dir, database, rows = source
    rows["lineitem"][0][0] = "999"
    write_files(data_dir, rows)
    with pytest.raises(LoadError):
        load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT name FROM sqlite_master").fetchall() == []
        assert conn.execute("PRAGMA application_id").fetchone()[0] == 0


def test_foreign_database_is_not_modified(source):
    data_dir, database, _ = source
    database.parent.mkdir()
    with sqlite3.connect(database) as conn:
        conn.execute("CREATE TABLE customer (private_note TEXT)")
        conn.execute("INSERT INTO customer VALUES ('a conserver')")
    with pytest.raises(LoadError, match="base dédiée"):
        load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT * FROM customer").fetchall() == [("a conserver",)]
        assert conn.execute("SELECT name FROM sqlite_master").fetchall() == [("customer",)]


def test_reload_preserves_unrelated_tables_in_project_database(source):
    data_dir, database, _ = source
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        conn.execute("CREATE TABLE notes (note TEXT)")
        conn.execute("INSERT INTO notes VALUES ('a conserver')")
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT * FROM notes").fetchall() == [("a conserver",)]


def test_cli_from_another_working_directory_and_error_status(source, tmp_path):
    data_dir, database, _ = source
    command = [
        sys.executable, str(ROOT / "etl/load_sources.py"),
        "--data-dir", str(data_dir), "--database", str(database),
    ]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "LINEITEM : 3 lignes chargées" in result.stdout
    assert "FACT_SALES : 3 lignes chargées" in result.stdout
    assert "Chargement validé" in result.stdout
    (data_dir / "orders.tbl").write_text("")
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert "orders.tbl" in result.stderr
    assert "Chargement validé" not in result.stdout


def test_supplied_files_counts_types_and_totals(tmp_path):
    database = tmp_path / "provided.sqlite"
    counts = load_sources(ROOT / "data", database)
    assert {table: counts[table] for table in SOURCE_COLUMNS} == {
        "nation": 25, "customer": 1500, "orders": 15000, "lineitem": 60175,
    }
    assert counts["dim_customer"] == 1500
    assert counts["fact_sales"] == 60175
    with (ROOT / "data/lineitem.tbl").open(encoding="ascii", newline="") as source:
        records = list(csv.reader(source, delimiter="|", quoting=csv.QUOTE_NONE))
    expected_quantity = sum(int(row[4]) for row in records)
    expected_price = int(sum(Decimal(row[5]) for row in records) * 100)
    with sqlite3.connect(database) as conn:
        assert conn.execute(
            "SELECT SUM(L_QUANTITY), SUM(L_EXTENDEDPRICE_CENTS) FROM lineitem"
        ).fetchone() == (expected_quantity, expected_price)
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute(
            "SELECT COUNT(*) FROM lineitem WHERE typeof(L_EXTENDEDPRICE_CENTS) != 'integer' "
            "OR typeof(L_DISCOUNT_PERCENT) != 'integer' OR typeof(L_TAX_PERCENT) != 'integer'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT SUM(quantity), SUM(extended_price_cents) FROM fact_sales"
        ).fetchone() == (expected_quantity, expected_price)
        expected_revenue = sum(
            int((Decimal(row[5]) * (1 - Decimal(row[6]))).quantize(
                Decimal("0.01"), rounding="ROUND_HALF_UP"
            ) * 100)
            for row in records
        )
        assert conn.execute(
            "SELECT SUM((extended_price_cents * (100 - discount_percent) + 50) / 100) "
            "FROM fact_sales"
        ).fetchone()[0] == expected_revenue
        assert conn.execute(
            "SELECT COUNT(*) FROM dim_customer c WHERE NOT EXISTS "
            "(SELECT 1 FROM fact_sales f WHERE f.customer_id = c.customer_id)"
        ).fetchone()[0] == 500
        first, last = conn.execute(
            "SELECT MIN(O_ORDERDATE), MAX(O_ORDERDATE) FROM orders"
        ).fetchone()
        expected_dates = [
            (date.fromisoformat(first) + timedelta(days=offset)).isoformat()
            for offset in range((date.fromisoformat(last) - date.fromisoformat(first)).days + 1)
        ]
        assert [row[0] for row in conn.execute(
            "SELECT date_id FROM dim_date ORDER BY date_id"
        )] == expected_dates
    before = snapshot(database)
    assert load_sources(ROOT / "data", database) == counts
    assert snapshot(database) == before


def test_star_mapping_and_rounding(source):
    data_dir, database, _ = source
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT * FROM dim_customer ORDER BY customer_id").fetchall() == [
            (1, "Alice", "BUILDING", 0, "ALGERIA"),
            (2, "Bob", "MACHINERY", 1, "ARGENTINA"),
        ]
        assert conn.execute(
            "SELECT * FROM fact_sales ORDER BY order_id, line_number"
        ).fetchall() == [
            (10, 1, 1, "1998-07-01", 2, 1005, 10, "AIR"),
            (10, 2, 1, "1998-07-01", 1, 500, 0, "MAIL"),
            (11, 1, 1, "1998-06-01", 1, 2000, 5, "AIR"),
        ]
        assert conn.execute(
            "SELECT SUM((extended_price_cents * (100 - discount_percent) + 50) / 100) "
            "FROM fact_sales"
        ).fetchone()[0] == 3305  # 9,05 + 5,00 + 19,00.


@pytest.mark.parametrize(("first", "last", "days"), [
    ("2000-02-28", "2000-03-01", ["2000-02-28", "2000-02-29", "2000-03-01"]),
    ("9999-12-31", "9999-12-31", ["9999-12-31"]),
])
def test_continuous_calendar_includes_bounds_and_leap_day(source, first, last, days):
    data_dir, database, rows = source
    rows["orders"][0][4] = last
    rows["orders"][1][4] = first
    write_files(data_dir, rows)
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT * FROM dim_date ORDER BY date_id").fetchall() == [
            (day, date.fromisoformat(day).year, date.fromisoformat(day).month,
             date.fromisoformat(day).day) for day in days
        ]


def test_round_each_line_before_summing_and_full_discount(source):
    data_dir, database, rows = source
    for row in rows["lineitem"][:2]:
        row[5:7] = ["0.05", "0.10"]
    rows["lineitem"][2][6] = "1.00"
    write_files(data_dir, rows)
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        assert conn.execute(
            "SELECT SUM((extended_price_cents * (100 - discount_percent) + 50) / 100) "
            "FROM fact_sales"
        ).fetchone()[0] == 10


def test_failure_during_fact_load_restores_sources_and_dimensions(source):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    before = snapshot(database)
    with sqlite3.connect(database) as conn:
        conn.execute(
            "CREATE TRIGGER reject_facts BEFORE INSERT ON fact_sales "
            "BEGIN SELECT RAISE(ABORT, 'échec de test'); END"
        )
    rows["customer"][0][1] = "Autre nom"
    rows["orders"][0][4] = "1999-01-01"
    write_files(data_dir, rows)
    with pytest.raises(sqlite3.IntegrityError, match="échec de test"):
        load_sources(data_dir, database)
    assert snapshot(database) == before


@pytest.mark.parametrize("problem", ["line_revenue", "quantity_total"])
def test_integer_overflow_rolls_back_entire_load(source, problem):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    before = snapshot(database)
    if problem == "line_revenue":
        rows["lineitem"][0][5] = "2000000000000000.00"
        expected = LoadError
    else:
        rows["lineitem"][0][4] = str(2**63 - 1)
        expected = sqlite3.OperationalError
    write_files(data_dir, rows)
    with pytest.raises(expected, match="capacité SQLite|integer overflow"):
        load_sources(data_dir, database)
    assert snapshot(database) == before


@pytest.mark.parametrize("fail", [True, False])
def test_upgrade_step4_database_is_atomic(source, fail):
    data_dir, database, rows = source
    load_sources(data_dir, database)
    with sqlite3.connect(database) as conn:
        for table in ("fact_sales", "dim_date", "dim_customer"):
            conn.execute(f"DROP TABLE {table}")
        conn.execute("PRAGMA user_version = 1")
        before = conn.execute("SELECT * FROM customer ORDER BY C_CUSTKEY").fetchall()
    if fail:
        rows["lineitem"][0][5] = "2000000000000000.00"
        write_files(data_dir, rows)
        with pytest.raises(LoadError, match="capacité SQLite"):
            load_sources(data_dir, database)
    else:
        assert load_sources(data_dir, database)["fact_sales"] == 3
    with sqlite3.connect(database) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == (1 if fail else SCHEMA_VERSION)
        assert conn.execute("SELECT * FROM customer ORDER BY C_CUSTKEY").fetchall() == before
        assert bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'fact_sales'"
        ).fetchone()) is (not fail)


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("fail", [True, False])
def test_real_legacy_schema_upgrade_preserves_data_and_rolls_back_ddl(source, version, fail):
    data_dir, database, rows = source
    database.parent.mkdir()
    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        # Ancien schéma : ni table NATION ni nom de pays.
        conn.execute("""CREATE TABLE customer (
            C_CUSTKEY INTEGER PRIMARY KEY CHECK (C_CUSTKEY > 0),
            C_NAME TEXT NOT NULL, C_ADDRESS TEXT NOT NULL,
            C_NATIONKEY INTEGER NOT NULL CHECK (C_NATIONKEY >= 0),
            C_PHONE TEXT NOT NULL, C_ACCTBAL_CENTS INTEGER NOT NULL,
            C_MKTSEGMENT TEXT NOT NULL, C_COMMENT TEXT NOT NULL
        ) STRICT""")
        conn.executescript((ROOT / "sql/01_sources.sql").read_text(encoding="utf-8"))
        conn.execute("DROP TABLE nation")
        for table in ("customer", "orders", "lineitem"):
            load_file(conn, data_dir, table)
        if version == 2:
            conn.execute("""CREATE TABLE dim_customer (
                customer_id INTEGER PRIMARY KEY CHECK (customer_id > 0),
                customer_name TEXT NOT NULL CHECK (length(trim(customer_name)) > 0),
                market_segment TEXT NOT NULL CHECK (length(trim(market_segment)) > 0),
                nation_id INTEGER NOT NULL CHECK (nation_id >= 0)
            ) STRICT""")
            conn.executescript((ROOT / "sql/02_star_schema.sql").read_text(encoding="utf-8"))
            conn.execute("INSERT INTO dim_customer SELECT C_CUSTKEY, C_NAME, C_MKTSEGMENT, C_NATIONKEY FROM customer")
            for offset in range(31):
                day = date(1998, 6, 1) + timedelta(days=offset)
                conn.execute("INSERT INTO dim_date VALUES (?, ?, ?, ?)", (day.isoformat(), day.year, day.month, day.day))
            conn.execute(
                "INSERT INTO fact_sales SELECT l.L_ORDERKEY, l.L_LINENUMBER, o.O_CUSTKEY, "
                "o.O_ORDERDATE, l.L_QUANTITY, l.L_EXTENDEDPRICE_CENTS, l.L_DISCOUNT_PERCENT, l.L_SHIPMODE "
                "FROM lineitem l JOIN orders o ON o.O_ORDERKEY = l.L_ORDERKEY"
            )
            conn.executescript((ROOT / "sql/03_monthly_sales.sql").read_text(encoding="utf-8"))
        conn.execute("CREATE TABLE notes (note TEXT)")
        conn.execute("INSERT INTO notes VALUES ('a conserver')")
        conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        conn.execute(f"PRAGMA user_version = {version}")
        before_schema = conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        before_data = {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
            for table in ("customer", "orders", "lineitem")
        }
        before_monthly = conn.execute("SELECT * FROM monthly_sales").fetchall() if version == 2 else None
    if fail:
        rows["lineitem"][0][5] = "2000000000000000.00"
        write_files(data_dir, rows)
        with pytest.raises(LoadError, match="capacité SQLite"):
            load_sources(data_dir, database)
    else:
        assert load_sources(data_dir, database)["nation"] == 2
    with sqlite3.connect(database) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == (version if fail else SCHEMA_VERSION)
        assert conn.execute("SELECT * FROM notes").fetchall() == [("a conserver",)]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, expected in before_data.items():
            assert conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall() == expected
        if fail:
            assert conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall() == before_schema
        else:
            assert any(row[2:4] == ("nation", "C_NATIONKEY") for row in conn.execute("PRAGMA foreign_key_list(customer)"))
            assert conn.execute("SELECT nation_name FROM dim_customer ORDER BY customer_id").fetchall() == [("ALGERIA",), ("ARGENTINA",)]
        if before_monthly is not None:
            assert conn.execute("SELECT * FROM monthly_sales").fetchall() == before_monthly


def test_unknown_schema_version_is_rejected_without_changes(source):
    data_dir, database, _ = source
    load_sources(data_dir, database)
    before = snapshot(database)
    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA user_version = 99")
    with pytest.raises(LoadError, match="version de schéma incompatible : 99"):
        load_sources(data_dir, database)
    assert snapshot(database) == before
