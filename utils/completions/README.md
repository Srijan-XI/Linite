# Shell Completions for Linite

Two completion scripts are provided in this directory.

| File | Shell | Format |
|------|-------|--------|
| `linite.bash` | Bash | `bash-completion` hook |
| `_linite` | Zsh | compsys `#compdef` |

---

## Bash

### Per-user (no sudo)
```bash
mkdir -p ~/.bash_completion.d
cp linite.bash ~/.bash_completion.d/linite
echo 'source ~/.bash_completion.d/linite' >> ~/.bashrc
source ~/.bashrc
```

### System-wide
```bash
sudo cp linite.bash /etc/bash_completion.d/linite
```
Opens automatically on next shell session (requires `bash-completion` to be installed).

---

## Zsh

### Per-user (recommended)
```zsh
mkdir -p ~/.zsh/completions
cp _linite ~/.zsh/completions/_linite

# If not already in ~/.zshrc:
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc

exec zsh
```

### System-wide (Arch / most distros)
```bash
sudo cp _linite /usr/share/zsh/site-functions/_linite
```

### Oh-My-Zsh
```bash
cp _linite ~/.oh-my-zsh/completions/_linite
```

---

## What gets completed

- All top-level flags (`--cli`, `--pm`, `--export-profile`, `--light`, …)
- `--pm` values: `apt dnf pacman zypper snap flatpak nix`
- `--cli` sub-commands: `install update uninstall`
- App IDs from the catalog (after `--cli install` / `--cli uninstall`)
- File paths for `--export`, `--export-profile`, `--import-profile`
- Daemon interval hour choices for `--daemon-interval-hours`
