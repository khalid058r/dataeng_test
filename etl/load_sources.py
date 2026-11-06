"""Charger NATION, CUSTOMER, ORDERS, LINEITEM et leur schéma en étoile.

Exécution depuis la racine : python -m etl.load_sources
La bibliothèque standard Python suffit pour ce chargement.
"""

import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import re
import sqlite3
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQLITE_MAX = 2**63 - 1
SQLITE_MIN = -(2**63)
APPLICATION_ID = 0x44544554  # DTET : identifie les bases créées par ce projet.
SCHEMA_VERSION = 3
SQL_FILES = (
    "01_sources.sql",
    "02_star_schema.sql",
    "03_monthly_sales.sql",
    "04_business_reports.sql",
)


class LoadError(ValueError):
    """Donnée source ou destination incompatible avec le chargement."""


def hundredths(value: str) -> int:
    """Exemples : '12.34' devient 1234 ; '0.10' devient 10."""
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("nombre décimal attendu") from exc
    if not number.is_finite():
        raise ValueError("nombre fini attendu")
    # SQLite stocke ses entiers sur 64 bits.
    if number < SQLITE_MIN or number > SQLITE_MAX:
        raise ValueError("montant hors capacité SQLite (64 bits)")

    # Vérifier les décimales AVANT int(), qui supprimerait une fraction.
    # 28 chiffres suffisent pour les entiers SQLite (19 chiffres au maximum).
    with localcontext(prec=28):
        if number != number.quantize(Decimal("0.01")):
            raise ValueError("valeur non représentable exactement en centièmes")
        result = int(number * 100)

    if not SQLITE_MIN <= result <= SQLITE_MAX:
        raise ValueError("montant en centièmes hors capacité SQLite (64 bits)")
    return result


def convert_value(value: str, kind: str) -> str | int:
    """Convertir le texte du fichier selon le type indiqué pour la colonne."""
    if not value.strip():
        raise ValueError("champ obligatoire vide")
    if kind == "text":
        return value  # Conserver les espaces des adresses et commentaires.
    if kind == "integer":
        if not re.fullmatch(r"[+-]?[0-9]+", value):
            raise ValueError("entier attendu")
        result = int(value)
        if not SQLITE_MIN <= result <= SQLITE_MAX:
            raise ValueError("entier hors capacité SQLite (64 bits)")
        return result
    if kind == "hundredths":
        return hundredths(value)
    if kind == "date":
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError("date attendue au format AAAA-MM-JJ")
        return value
    raise ValueError(f"type de colonne inconnu : {kind}")


# Pour chaque colonne : son nom source et la conversion à effectuer.
# L'ordre est celui du fichier, qui n'a pas d'en-tête.
# Les règles métier (quantité > 0, remise entre 0 et 100, etc.) sont dans le SQL.
SOURCE_COLUMNS = {
    "nation": {
        "N_NATIONKEY": "integer",
        "N_NAME": "text",
        "N_REGIONKEY": "integer",
        "N_COMMENT": "text",
    },
    "customer": {
        "C_CUSTKEY": "integer",
        "C_NAME": "text",
        "C_ADDRESS": "text",
        "C_NATIONKEY": "integer",
        "C_PHONE": "text",
        "C_ACCTBAL": "hundredths",
        "C_MKTSEGMENT": "text",
        "C_COMMENT": "text",
    },
    "orders": {
        "O_ORDERKEY": "integer",
        "O_CUSTKEY": "integer",
        "O_ORDERSTATUS": "text",
        "O_TOTALPRICE": "hundredths",
        "O_ORDERDATE": "date",
        "O_ORDERPRIORITY": "text",
        "O_CLERK": "text",
        "O_SHIPPRIORITY": "integer",
        "O_COMMENT": "text",
    },
    "lineitem": {
        "L_ORDERKEY": "integer",
        "L_PARTKEY": "integer",
        "L_SUPPKEY": "integer",
        "L_LINENUMBER": "integer",
        "L_QUANTITY": "integer",
        "L_EXTENDEDPRICE": "hundredths",
        "L_DISCOUNT": "hundredths",
        "L_TAX": "hundredths",
        "L_RETURNFLAG": "text",
        "L_LINESTATUS": "text",
        "L_SHIPDATE": "date",
        "L_COMMITDATE": "date",
        "L_RECEIPTDATE": "date",
        "L_SHIPINSTRUCT": "text",
        "L_SHIPMODE": "text",
        "L_COMMENT": "text",
    },
}

STORED_NAMES = {
    "C_ACCTBAL": "C_ACCTBAL_CENTS",
    "O_TOTALPRICE": "O_TOTALPRICE_CENTS",
    "L_EXTENDEDPRICE": "L_EXTENDEDPRICE_CENTS",
    "L_DISCOUNT": "L_DISCOUNT_PERCENT",
    "L_TAX": "L_TAX_PERCENT",
}


def load_file(connection: sqlite3.Connection, data_dir: Path, table: str) -> int:
    """Lire un fichier ligne par ligne et insérer ses valeurs dans sa table."""
    path = data_dir / f"{table}.tbl"
    columns = SOURCE_COLUMNS[table]
    stored_columns = []
    for name in columns:
        stored_columns.append(STORED_NAMES.get(name, name))
    stored = ", ".join(stored_columns)
    placeholders = ", ".join(["?"] * len(columns))
    # Noms SQL définis dans le code ; seules les valeurs viennent des fichiers.
    statement = f"INSERT INTO {table} ({stored}) VALUES ({placeholders})"
    count = 0
    line_number = 0
    try:
        with path.open(encoding="ascii", newline="") as source:
            reader = csv.reader(source, delimiter="|", quoting=csv.QUOTE_NONE)
            for line_number, row in enumerate(reader, start=1):
                if len(row) == len(columns) + 1 and row[-1] == "":
                    row.pop()
                if len(row) != len(columns):
                    raise LoadError(
                        f"{path.name}, ligne {line_number} : "
                        f"{len(columns)} colonnes attendues, {len(row)} reçues"
                    )
                values = []
                for (column, kind), raw in zip(columns.items(), row):
                    try:
                        values.append(convert_value(raw, kind))
                    except ValueError as exc:
                        raise LoadError(
                            f"{path.name}, ligne {line_number}, {column} : {exc}"
                        ) from exc
                try:
                    connection.execute(statement, values)
                except sqlite3.IntegrityError as exc:
                    detail = str(exc)
                    if exc.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY":
                        detail = {
                            "customer": "C_NATIONKEY : pays absent de NATION",
                            "orders": "O_CUSTKEY : client absent de CUSTOMER",
                            "lineitem": "L_ORDERKEY : commande absente de ORDERS",
                        }[table]
                    raise LoadError(
                        f"{path.name}, ligne {line_number} : {detail}"
                    ) from exc
                count += 1
    except (OSError, UnicodeError, csv.Error) as exc:
        raise LoadError(
            f"{path.name}, après {line_number} lignes lues : lecture impossible ({exc})"
        ) from exc
    if count == 0:
        raise LoadError(f"{path.name} : fichier vide")
    return count


def check_destination(connection: sqlite3.Connection) -> int:
    application_id = connection.execute("PRAGMA application_id").fetchone()[0]
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    has_objects = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
    ).fetchone()
    if application_id == 0 and not has_objects:
        return 0  # Une nouvelle base vide est autorisée.
    if application_id != APPLICATION_ID:
        raise LoadError("la base existante n'appartient pas au projet ; choisir une base dédiée")
    if version not in (1, 2, SCHEMA_VERSION):
        raise LoadError(f"version de schéma incompatible : {version}")
    return version


def nation_upgrade_sql(connection: sqlite3.Connection, version: int) -> str:
    """Préparer la migration des versions 1 et 2, dans la transaction du chargement."""
    if version not in (1, 2):
        return ""
    tables = []
    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
        tables.append(row[0])
    # Vider les enfants avant de recréer les deux tables dont la définition change.
    # SQLite ne permet pas d'ajouter une référence à une colonne déjà existante.
    statements = []
    for table in ("fact_sales", "lineitem", "orders"):
        if table in tables:
            statements.append(f"DELETE FROM {table};")
    for table in ("dim_customer", "customer"):
        if table in tables:
            statements.append(f"DROP TABLE {table};")
    return "\n".join(statements) + "\n"


def load_star(connection: sqlite3.Connection) -> dict[str, int]:
    """Alimenter les dimensions, puis les faits, sans valider la transaction."""
    connection.execute(
        "INSERT INTO dim_customer "
        "(customer_id, customer_name, market_segment, nation_id, nation_name) "
        "SELECT c.C_CUSTKEY, c.C_NAME, c.C_MKTSEGMENT, c.C_NATIONKEY, n.N_NAME "
        "FROM customer c JOIN nation n ON n.N_NATIONKEY = c.C_NATIONKEY"
    )

    first, last = connection.execute(
        "SELECT MIN(O_ORDERDATE), MAX(O_ORDERDATE) FROM orders"
    ).fetchone()
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    # Inclure tous les jours, même ceux sans commande, ainsi que les deux bornes.
    # Le décalage évite d'incrémenter au-delà du 31/12/9999.
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        connection.execute(
            "INSERT INTO dim_date (date_id, year, month, day) VALUES (?, ?, ?, ?)",
            (day.isoformat(), day.year, day.month, day.day),
        )

    connection.execute(
        "INSERT INTO fact_sales "
        "(order_id, line_number, customer_id, date_id, quantity, "
        "extended_price_cents, discount_percent, ship_mode) "
        "SELECT l.L_ORDERKEY, l.L_LINENUMBER, o.O_CUSTKEY, o.O_ORDERDATE, "
        "l.L_QUANTITY, l.L_EXTENDEDPRICE_CENTS, l.L_DISCOUNT_PERCENT, l.L_SHIPMODE "
        "FROM lineitem l JOIN orders o ON o.O_ORDERKEY = l.L_ORDERKEY"
    )

    source_totals = connection.execute(
        "SELECT COUNT(*), SUM(L_QUANTITY), SUM(L_EXTENDEDPRICE_CENTS) FROM lineitem"
    ).fetchone()
    fact_totals = connection.execute(
        "SELECT COUNT(*), SUM(quantity), SUM(extended_price_cents) FROM fact_sales"
    ).fetchone()
    if fact_totals != source_totals:
        raise LoadError("faits incohérents : volumes, quantités ou prix différents des sources")

    # SQLite convertirait silencieusement une multiplication trop grande en REAL.
    # Vérifier sa capacité avant de calculer le revenu arrondi des futurs rapports.
    overflow = connection.execute(
        "SELECT order_id, line_number FROM fact_sales "
        "WHERE discount_percent < 100 "
        "AND extended_price_cents > ? / (100 - discount_percent) LIMIT 1",
        (SQLITE_MAX - 50,),
    ).fetchone()
    if overflow:
        raise LoadError(f"revenu hors capacité SQLite : commande {overflow[0]}, ligne {overflow[1]}")
    # SUM sur des entiers lève une erreur si le total dépasse la capacité SQLite.
    connection.execute(
        "SELECT SUM((extended_price_cents * (100 - discount_percent) + 50) / 100) "
        "FROM fact_sales"
    ).fetchone()

    counts = {}
    for table in ("dim_customer", "dim_date", "fact_sales"):
        row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        counts[table] = row[0]
    return counts


def load_sources(data_dir: Path, database: Path) -> dict[str, int]:
    """Remplacer sources, dimensions et faits dans une transaction, ou tout annuler."""
    data_dir = Path(data_dir)
    database = Path(database)

    # 1. Vérifier les fichiers avant de commencer à écrire dans la base.
    for table in SOURCE_COLUMNS:
        source = data_dir / f"{table}.tbl"
        if not source.is_file():
            raise LoadError(f"{source} : fichier source absent")
        if source.stat().st_size == 0:
            raise LoadError(f"{source.name} : fichier vide")

    # 2. Lire les définitions SQL dans l'ordre indiqué en haut du fichier.
    sql_scripts = []
    for filename in SQL_FILES:
        path = PROJECT_ROOT / "sql" / filename
        sql_scripts.append(path.read_text(encoding="utf-8"))
    schema_sql = "\n".join(sql_scripts)

    # 3. Ouvrir la base, puis démarrer la transaction dans le script SQL.
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, isolation_level=None, timeout=5)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        version = check_destination(connection)
        upgrade_sql = nation_upgrade_sql(connection, version)
        # executescript peut valider une transaction précédente : on démarre
        # explicitement la nôtre DANS le script, avant toute création de table.
        connection.executescript(
            "BEGIN IMMEDIATE;\n" + upgrade_sql + schema_sql
        )

        # 4. Vider les enfants avant leurs parents pour respecter les relations.
        connection.execute("DELETE FROM fact_sales")
        connection.execute("DELETE FROM dim_date")
        connection.execute("DELETE FROM dim_customer")
        connection.execute("DELETE FROM lineitem")
        connection.execute("DELETE FROM orders")
        connection.execute("DELETE FROM customer")
        connection.execute("DELETE FROM nation")

        # 5. Charger les sources, puis les dimensions et les faits.
        counts = {}
        for table in SOURCE_COLUMNS:
            counts[table] = load_file(connection, data_dir, table)
        counts.update(load_star(connection))

        # 6. Identifier la base du projet et valider tout le chargement.
        connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()  # Tout a réussi : valider les nouvelles données.
    except Exception:
        connection.rollback()  # Une erreur : revenir aux données précédentes.
        raise
    finally:
        connection.close()  # Fermer la base, que le chargement ait réussi ou non.
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument(
        "--database", type=Path, default=PROJECT_ROOT / "outputs" / "warehouse.sqlite"
    )
    args = parser.parse_args(argv)
    try:
        counts = load_sources(args.data_dir, args.database)
    except (LoadError, OSError, sqlite3.Error) as exc:
        print(f"ERREUR : {exc}. Chargement non validé.", file=sys.stderr)
        return 1
    for table, count in counts.items():
        print(f"{table.upper()} : {count:,} lignes chargées".replace(",", " "))
    print(f"Chargement validé : {args.database.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
