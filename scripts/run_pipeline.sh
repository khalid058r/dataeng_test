#!/usr/bin/env bash
# Exécuter le chargement et l'export sous un même verrou, avec un journal quotidien.
set -euo pipefail

PIPELINE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_PYTHON="${PIPELINE_PYTHON:-$PIPELINE_ROOT/.venv/bin/python}"
PIPELINE_DATA_DIR="${PIPELINE_DATA_DIR:-$PIPELINE_ROOT/data}"
PIPELINE_OUTPUT_DIR="${PIPELINE_OUTPUT_DIR:-$PIPELINE_ROOT/outputs}"
PIPELINE_DATABASE="${PIPELINE_DATABASE:-$PIPELINE_OUTPUT_DIR/warehouse.sqlite}"
PIPELINE_LOG_DIR="${PIPELINE_LOG_DIR:-$PIPELINE_ROOT/logs}"

mkdir -p "$PIPELINE_OUTPUT_DIR" "$PIPELINE_LOG_DIR" "$(dirname -- "$PIPELINE_DATABASE")"
PIPELINE_LOG_FILE="$PIPELINE_LOG_DIR/pipeline-$(date +%F).log"
printf 'Journal : %s\n' "$PIPELINE_LOG_FILE"
exec >>"$PIPELINE_LOG_FILE" 2>&1

pipeline_finish() {
    local pipeline_status=$?
    if [[ "$pipeline_status" -eq 75 ]]; then
        printf '[%s] IGNORÉ : une exécution utilise déjà cette base.\n' "$(date --iso-8601=seconds)"
    elif [[ "$pipeline_status" -ne 0 ]]; then
        printf '[%s] ÉCHEC : code %s ; consulter les messages précédents.\n' "$(date --iso-8601=seconds)" "$pipeline_status"
    fi
}
trap pipeline_finish EXIT

# Ne pas supprimer ce fichier : c'est le verrou système ouvert qui protège l'exécution.
exec 9>"${PIPELINE_DATABASE}.pipeline.lock"
flock -n -E 75 9

printf '[%s] DÉBUT\n' "$(date --iso-8601=seconds)"
cd -- "$PIPELINE_ROOT"
"$PIPELINE_PYTHON" -m etl.load_sources --data-dir "$PIPELINE_DATA_DIR" --database "$PIPELINE_DATABASE"
"$PIPELINE_PYTHON" -m etl.export_reports --database "$PIPELINE_DATABASE" --output-dir "$PIPELINE_OUTPUT_DIR"
printf '[%s] SUCCÈS : base et rapports disponibles.\n' "$(date --iso-8601=seconds)"
