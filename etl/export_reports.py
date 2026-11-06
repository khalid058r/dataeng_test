"""Exporter les rapports SQL en CSV : python -m etl.export_reports."""

import argparse
import csv
from pathlib import Path
import sqlite3
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_QUERIES = {
    "monthly_sales": "SELECT * FROM monthly_sales ORDER BY period",
    "top_5_nations": "SELECT * FROM top_5_nations ORDER BY revenue_cents DESC, nation_id",
    "top_shipping_modes": "SELECT * FROM top_shipping_modes ORDER BY ship_mode",
    "best_sales_months": "SELECT * FROM best_sales_months ORDER BY position",
    "customers_by_revenue": "SELECT * FROM customers_by_revenue ORDER BY position",
    "customers_by_quantity": "SELECT * FROM customers_by_quantity ORDER BY position",
    "period_comparison": "SELECT * FROM period_comparison",
}


def export_reports(database: Path, output_dir: Path) -> dict[str, int]:
    """Lire un instantané de la base, puis écrire les sept résultats avec en-têtes."""
    # mode=ro refuse une base absente et interdit de modifier l'entrepôt.
    connection = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("BEGIN")
        results = {}
        for name, query in REPORT_QUERIES.items():
            cursor = connection.execute(query)
            results[name] = ([column[0] for column in cursor.description], cursor.fetchall())
    finally:
        connection.close()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, (columns, rows) in results.items():
        with (output_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(columns)
            writer.writerows(rows)
        counts[name] = len(rows)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=PROJECT_ROOT / "outputs/warehouse.sqlite")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    args = parser.parse_args(argv)
    try:
        counts = export_reports(args.database, args.output_dir)
    except (OSError, sqlite3.Error) as exc:
        print(f"ERREUR : export impossible ({exc}).", file=sys.stderr)
        return 1
    for name, count in counts.items():
        print(f"{name}.csv : {count} lignes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
