#!/usr/bin/env bash
# =============================================================================
# Linite - Install Bootstrap Script
# Sets up a local virtual environment and installs project dependencies.
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
#   ./install.sh --system   # install requirements to current interpreter
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERR]${RESET}   $*" >&2; }
die()     { error "$*"; exit 1; }

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            "$cmd" - <<'PY' >/dev/null 2>&1 || continue
import sys
assert sys.version_info >= (3, 11)
PY
            echo "$cmd"
            return 0
        fi
    done
    return 1
}

ensure_requirements_file() {
    [[ -f "$REQ_FILE" ]] || die "requirements.txt not found at: $REQ_FILE"
}

install_system_mode() {
    local py="$1"
    info "Installing dependencies into current Python environment..."
    "$py" -m pip install --upgrade pip
    "$py" -m pip install -r "$REQ_FILE"
    success "Dependencies installed."
}

install_venv_mode() {
    local py="$1"
    local venv_dir="$SCRIPT_DIR/.venv"

    info "Creating virtual environment at $venv_dir"
    "$py" -m venv "$venv_dir"

    local vpy="$venv_dir/bin/python"
    [[ -x "$vpy" ]] || die "Virtual environment creation failed."

    info "Installing dependencies in virtual environment..."
    "$vpy" -m pip install --upgrade pip
    "$vpy" -m pip install -r "$REQ_FILE"

    success "Setup completed successfully."
    echo
    echo "Next steps:"
    echo "  source .venv/bin/activate"
    echo "  python main.py"
    echo "  ./app.sh"
}

main() {
    cd "$SCRIPT_DIR"
    ensure_requirements_file

    local py
    py="$(find_python)" || die "Python 3.11+ is required but was not found."
    info "Using Python: $py ($($py --version 2>&1))"

    if [[ "${1:-}" == "--system" ]]; then
        warn "Running in --system mode (no virtual environment)."
        install_system_mode "$py"
    else
        install_venv_mode "$py"
    fi
}

main "$@"
