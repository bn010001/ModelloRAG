#!/usr/bin/env bash
set -euo pipefail

# Cerca la root del progetto: quella che contiene sia .venv/ che src/
find_project_root() {
    local current="$1"
    while [[ "$current" != "/" ]]; do
        if [[ -d "$current/.venv" && -d "$current/src" ]]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    return 1
}

# 1. Parti dalla posizione dello script
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")"

if [[ -z "$PROJECT_ROOT" ]]; then
    echo "❌ Impossibile trovare root del progetto (cartella con .venv/ e src/)"
    exit 1
fi

cd "$PROJECT_ROOT"

# 2. Attiva virtualenv
if [[ -f ".venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
else
    echo "❌ Virtualenv non trovato in $PROJECT_ROOT/.venv/"
    echo "   Esegui: python -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

# 3. Lancia l'app
python -m src.ui.main_ui
