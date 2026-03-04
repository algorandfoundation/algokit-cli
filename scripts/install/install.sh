#!/usr/bin/env bash
# AlgoKit CLI Installer for Unix/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/algorandfoundation/algokit-cli/main/scripts/install/install.sh | bash
set -euo pipefail

UV_INSTALL_URL="https://astral.sh/uv/install.sh"
PYTHON_VERSION="3.12"
PACKAGE="algokit"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

log()  { printf "${GREEN}[algokit]${NC} %b\n" "$*"; }
warn() { printf "${YELLOW}[algokit]${NC} %b\n" "$*"; }
die()  { printf "${RED}[algokit]${NC} %b\n" "$*" >&2; exit 1; }

check_curl() {
    command -v curl >/dev/null 2>&1 || die "curl is required but not installed."
}

ensure_uv() {
    if command -v uv >/dev/null 2>&1; then
        log "uv found: $(uv --version 2>/dev/null || echo 'unknown')"
        return 0
    fi

    log "Installing uv..."

    local temp_file
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    curl -fsSL --connect-timeout 30 --max-time 300 "$UV_INSTALL_URL" > "$temp_file" \
        || die "Failed to download uv installer."

    [[ $(wc -c < "$temp_file") -ge 1000 ]] \
        || die "uv installer appears corrupted (too small)."

    bash "$temp_file" || die "uv installation failed."
    rm -f "$temp_file"
    trap - EXIT

    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1 \
        || die "uv installed but not found on PATH. Restart your shell and try again."
    log "uv installed successfully."
}

ensure_python() {
    if uv python find "${PYTHON_VERSION}" >/dev/null 2>&1; then
        log "Python ${PYTHON_VERSION} found."
        return 0
    fi

    log "Installing Python ${PYTHON_VERSION} via uv..."
    uv python install "$PYTHON_VERSION" \
        || die "Failed to install Python ${PYTHON_VERSION}."
    log "Python ${PYTHON_VERSION} installed."
}

install_algokit() {
    log "Installing ${PACKAGE}..."
    uv tool install "$PACKAGE" \
        || die "Failed to install ${PACKAGE}."

    if command -v algokit >/dev/null 2>&1; then
        local active_algokit
        active_algokit=$(command -v algokit)
        local -a all_algokit_paths=()
        local -a path_entries=()
        local seen_paths=":"
        local path_entry
        IFS=: read -r -a path_entries <<< "$PATH"
        for path_entry in "${path_entries[@]}"; do
            [[ -z "$path_entry" ]] && continue
            local candidate="$path_entry/algokit"
            if [[ -f "$candidate" && -x "$candidate" ]]; then
                case "$seen_paths" in
                    *":$candidate:"*) ;;
                    *)
                        seen_paths="${seen_paths}${candidate}:"
                        all_algokit_paths+=("$candidate")
                        ;;
                esac
            fi
        done

        log "Installed: $(algokit --version 2>/dev/null || echo "${PACKAGE}")"
        log "Run ${BOLD}algokit --help${NC} to get started."

        if [[ ${#all_algokit_paths[@]} -gt 1 ]]; then
            warn "Multiple algokit executables were found on PATH."
            warn "Active executable: ${active_algokit}"
            warn "All PATH matches:"
            local match_path
            for match_path in "${all_algokit_paths[@]}"; do
                warn "  - ${match_path}"
            done
            warn "If this is not the uv-managed executable, move ~/.local/bin earlier on PATH or remove legacy binary."
            warn "Restart your shell and run: algokit --version"
        fi
    else
        warn "${PACKAGE} installed but not found on PATH."
        warn "Add ~/.local/bin to your PATH:"
        printf '  export PATH="$HOME/.local/bin:$PATH"\n'
    fi
}

main() {
    log "AlgoKit CLI Installer"
    echo ""

    check_curl
    ensure_uv
    ensure_python
    install_algokit

    echo ""
    log "Done."
}

main "$@"
