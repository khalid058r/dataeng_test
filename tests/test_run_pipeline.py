"""Contrat du lanceur planifiable : succès, arrêt après erreur et exclusion mutuelle."""

import csv
import fcntl
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_pipeline(tmp_path, data_dir):
    environment = os.environ.copy()
    environment.update({
        "PIPELINE_PYTHON": sys.executable,
        "PIPELINE_DATA_DIR": str(data_dir),
        "PIPELINE_OUTPUT_DIR": str(tmp_path / "outputs"),
        "PIPELINE_LOG_DIR": str(tmp_path / "logs"),
        "PIPELINE_DATABASE": str(tmp_path / "outputs/warehouse.sqlite"),
    })
    return subprocess.run(
        ["bash", str(ROOT / "scripts/run_pipeline.sh")],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=60,
    )


def test_launcher_loads_and_exports_from_another_directory(tmp_path):
    result = run_pipeline(tmp_path, ROOT / "data")
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(tmp_path / "outputs/warehouse.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0] == 60175
    with (tmp_path / "outputs/top_5_nations.csv").open(encoding="utf-8", newline="") as source:
        assert list(csv.DictReader(source))[0]["nation_name"] == "CANADA"
    assert len(list((tmp_path / "outputs").glob("*.csv"))) == 7
    log = next((tmp_path / "logs").glob("pipeline-*.log")).read_text(encoding="utf-8")
    assert "DÉBUT" in log and "SUCCÈS" in log


def test_launcher_stops_before_export_on_source_failure(tmp_path):
    output = tmp_path / "outputs"
    output.mkdir()
    report = output / "monthly_sales.csv"
    report.write_text("rapport precedent", encoding="utf-8")
    result = run_pipeline(tmp_path, tmp_path / "data_absente")
    assert result.returncode == 1
    assert not (output / "warehouse.sqlite").exists()
    assert report.read_text(encoding="utf-8") == "rapport precedent"
    log = next((tmp_path / "logs").glob("pipeline-*.log")).read_text(encoding="utf-8")
    assert "source absent" in log and "ÉCHEC" in log
    assert "SUCCÈS" not in log


def test_launcher_does_not_run_when_database_lock_is_held(tmp_path):
    output = tmp_path / "outputs"
    output.mkdir()
    with (output / "warehouse.sqlite.pipeline.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run_pipeline(tmp_path, ROOT / "data")
    assert result.returncode == 75
    assert not (output / "warehouse.sqlite").exists()
    log = next((tmp_path / "logs").glob("pipeline-*.log")).read_text(encoding="utf-8")
    assert "IGNORÉ" in log
    assert "DÉBUT" not in log
