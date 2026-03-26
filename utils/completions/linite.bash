#!/usr/bin/env bash
# Bash tab-completion for Linite
# ---------------------------------------------------
# Installation (choose one):
#
#  1. Per-user (no sudo required):
#       mkdir -p ~/.bash_completion.d
#       cp linite.bash ~/.bash_completion.d/linite
#       echo 'source ~/.bash_completion.d/linite' >> ~/.bashrc
#       source ~/.bashrc
#
#  2. System-wide:
#       sudo cp linite.bash /etc/bash_completion.d/linite
#       (opens automatically on next shell session)
#
# ---------------------------------------------------

_linite_completions() {
    local cur prev words cword
    _init_completion || return

    # ── Top-level flags ──────────────────────────────────────────────────
    local global_flags=(
        --cli
        --list
        --export
        --export-profile
        --import-profile
        --cache
        --cache-info
        --clear-cache
        --light
        --rollback
        --dry
        --daemon
        --daemon-interval-hours
        --skip-network-check
        --pm
        --verbose -v
        --help -h
    )

    # ── Package managers ─────────────────────────────────────────────────
    local pms=(apt dnf pacman zypper snap flatpak nix)

    # ── Sub-commands for --cli ────────────────────────────────────────────
    local cli_subcmds=(install update uninstall)

    case "${prev}" in
        --pm)
            COMPREPLY=( $(compgen -W "${pms[*]}" -- "${cur}") )
            return 0
            ;;
        --export | --export-profile | --import-profile)
            # Suggest JSON / sh files from the current directory
            _filedir '@(json|sh)'
            return 0
            ;;
        --daemon-interval-hours)
            COMPREPLY=( $(compgen -W "1 2 4 6 12 24 48" -- "${cur}") )
            return 0
            ;;
        --cli)
            COMPREPLY=( $(compgen -W "${cli_subcmds[*]}" -- "${cur}") )
            return 0
            ;;
        install | update | uninstall)
            # If we are in a --cli install / uninstall context,
            # try to complete app IDs from the catalog (best-effort).
            local catalog
            catalog=$(python3 -c "
from data.software_catalog import CATALOG_MAP
print(' '.join(sorted(CATALOG_MAP.keys())))
" 2>/dev/null)
            if [[ -n "${catalog}" ]]; then
                COMPREPLY=( $(compgen -W "${catalog}" -- "${cur}") )
            fi
            return 0
            ;;
    esac

    # Default: complete global flags
    COMPREPLY=( $(compgen -W "${global_flags[*]}" -- "${cur}") )
} && complete -F _linite_completions linite python3
