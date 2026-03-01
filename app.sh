#!/usr/bin/env bash
# =============================================================================
#  Linite - Launcher Script
#  Usage:
#    ./app.sh              → launch GUI
#    ./app.sh --cli install vlc git
#    ./app.sh --cli update
#    ./app.sh --list
#    ./app.sh --install-deps   → install Python + tkinter only
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERR]${RESET}   $*" >&2; }
die()     { error "$*"; exit 1; }

# ── Detect distro & package manager ──────────────────────────────────────────
detect_pm() {
    if   command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf     &>/dev/null; then echo "dnf"
    elif command -v yum     &>/dev/null; then echo "yum"
    elif command -v pacman  &>/dev/null; then echo "pacman"
    elif command -v zypper  &>/dev/null; then echo "zypper"
    else echo "unknown"
    fi
}

# ── Install tkinter for the detected distro ───────────────────────────────────
install_tkinter() {
    local pm
    pm=$(detect_pm)
    info "Installing tkinter via $pm …"
    case "$pm" in
        apt)    sudo apt-get install -y python3-tk ;;
        dnf)    sudo dnf install -y python3-tkinter ;;
        yum)    sudo yum install -y python3-tkinter ;;
        pacman) sudo pacman -S --noconfirm tk ;;
        zypper) sudo zypper install -y python3-tk ;;
        *)      warn "Could not auto-install tkinter. Install it manually for your distro." ;;
    esac
}

# ── Find a suitable Python interpreter ───────────────────────────────────────
find_python() {
    for cmd in python3 python python3.12 python3.11 python3.10; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            local major minor
            major="${ver%%.*}"
            minor="${ver##*.}"
            if [[ "$major" -ge "$MIN_PYTHON_MAJOR" && "$minor" -ge "$MIN_PYTHON_MINOR" ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# ── Check tkinter availability ────────────────────────────────────────────────
check_tkinter() {
    local python="$1"
    "$python" -c "import tkinter" &>/dev/null
}

# ── --install-deps mode ───────────────────────────────────────────────────────
cmd_install_deps() {
    local pm
    pm=$(detect_pm)
    info "Detected package manager: $pm"

    info "Checking for Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ …"
    if ! find_python &>/dev/null; then
        info "Python not found or too old. Installing …"
        case "$pm" in
            apt)    sudo apt-get update -y && sudo apt-get install -y python3 python3-pip ;;
            dnf)    sudo dnf install -y python3 python3-pip ;;
            yum)    sudo yum install -y python3 python3-pip ;;
            pacman) sudo pacman -S --noconfirm python python-pip ;;
            zypper) sudo zypper install -y python3 python3-pip ;;
            *)      die "Cannot auto-install Python. Please install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ manually." ;;
        esac
    else
        success "Python $(find_python) is available."
    fi

    local python
    python=$(find_python)

    info "Checking for tkinter …"
    if ! check_tkinter "$python"; then
        install_tkinter
    else
        success "tkinter is available."
    fi

    success "All dependencies satisfied. Run  ./app.sh  to launch Linite."
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}${CYAN}"
    echo "  ██╗     ██╗███╗   ██╗██╗████████╗███████╗"
    echo "  ██║     ██║████╗  ██║██║╚══██╔══╝██╔════╝"
    echo "  ██║     ██║██╔██╗ ██║██║   ██║   █████╗  "
    echo "  ██║     ██║██║╚██╗██║██║   ██║   ██╔══╝  "
    echo "  ███████╗██║██║ ╚████║██║   ██║   ███████╗"
    echo "  ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝   ╚══════╝"
    echo -e "${RESET}"
    echo -e "  Universal Linux Software Installer\n"

    # --install-deps flag handled before Python check
    if [[ "${1:-}" == "--install-deps" ]]; then
        cmd_install_deps
        exit 0
    fi

    # Locate Python
    local python
    if ! python=$(find_python); then
        error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ not found."
        echo -e "  Run  ${BOLD}./app.sh --install-deps${RESET}  to install required dependencies."
        exit 1
    fi
    info "Using Python: $python ($(${python} --version 2>&1))"

    # Check tkinter (only needed for GUI mode)
    if [[ "${1:-}" != "--cli" ]] && [[ "${1:-}" != "--list" ]]; then
        if ! check_tkinter "$python"; then
            warn "tkinter not found. Attempting to install it …"
            install_tkinter
            if ! check_tkinter "$python"; then
                die "tkinter still unavailable. Run  ./app.sh --install-deps  or install it manually."
            fi
        fi
    fi

    # Change to project directory and launch
    cd "$SCRIPT_DIR"
    info "Launching Linite …"
    exec "$python" main.py "$@"
}

main "$@"
