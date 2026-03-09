# Contributing to Linite 🐧

Thank you for considering a contribution! Linite is a community-driven project and every pull request, bug report, or new app suggestion is welcome.

---

## Table of Contents

- [Contributing to Linite 🐧](#contributing-to-linite-)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Development Setup](#development-setup)
  - [Project Structure](#project-structure)
  - [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting an App](#suggesting-an-app)
    - [Adding a New App to the Catalog](#adding-a-new-app-to-the-catalog)
    - [Adding a New Package Manager](#adding-a-new-package-manager)
    - [Improving the GUI](#improving-the-gui)
  - [Code Style](#code-style)
  - [Commit Conventions](#commit-conventions)
  - [Pull Request Checklist](#pull-request-checklist)
  - [Questions?](#questions)

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/linite.git
   cd linite
   ```
3. **Create a feature branch** off `main`:
   ```bash
   git checkout -b feat/add-my-app
   ```

---

## Development Setup

Linite's core has **zero third-party dependencies** — the entire stack runs on the Python standard library.

```bash
# Python 3.10+ required
python3 --version

# Tkinter must be available (may need a system package)
# Debian/Ubuntu:
sudo apt install python3-tk

# Fedora:
sudo dnf install python3-tkinter

# Arch:
sudo pacman -S tk

# Run the app
python3 main.py

# Run a syntax check
python3 check_syntax.py
```

Optional extras (not required):
```bash
pip install pillow   # enables PNG app icons instead of emoji
```

---

## Project Structure

```
linite/
├── core/
│   ├── distro.py             # Linux distro detection
│   ├── package_manager.py    # PM abstraction (apt, dnf, pacman …)
│   ├── installer.py          # Orchestrates installation
│   ├── uninstaller.py        # Orchestrates removal
│   ├── updater.py            # System-wide update logic
│   ├── history.py            # Install history tracking
│   └── profiles.py           # Save/load app selections as JSON
├── data/
│   └── software_catalog.py   # All app definitions (add new apps here)
├── gui/
│   ├── app.py                # Main window
│   ├── styles.py             # Dark-mode palette & fonts
│   └── components/
│       ├── category_panel.py
│       ├── software_panel.py
│       ├── progress_panel.py
│       └── app_detail.py
├── utils/
│   └── helpers.py            # Logging, root-check, platform helpers
└── main.py                   # Entry point (GUI + CLI)
```

---

## How to Contribute

### Reporting Bugs

Open a GitHub Issue and include:

- Your Linux distro and version (`cat /etc/os-release`)
- Python version (`python3 --version`)
- The full error traceback (run with `--verbose` to get more detail)
- Steps to reproduce

### Suggesting an App

Open an Issue with the label **`app-request`** and include:

- App name and website
- Package name on at least one package manager
- Category it belongs to
- Why you think it should be in Linite

### Adding a New App to the Catalog

All apps live in `data/software_catalog.py`. Adding a new app takes roughly 10 lines.

**Step 1** — Find the category constant and add your entry:

```python
# data/software_catalog.py

SoftwareEntry(
    id="my-app",                    # unique lowercase slug (used in CLI)
    name="My App",                  # display name
    description="Short description of what it does.",
    category="Utilities",           # must match an existing CATEGORIES entry
    icon="🛠️",                      # emoji icon
    website="https://myapp.io",
    install_specs={
        # Native package managers
        "apt":    _s(["my-app"]),
        "dnf":    _s(["my-app"]),
        "pacman": _s(["my-app"]),
        "zypper": _s(["my-app"]),
        # Universal fallbacks
        "flatpak": PackageSpec(
            packages=["io.myapp.MyApp"],
            flatpak_remote="flathub",
        ),
        "snap": PackageSpec(packages=["my-app"]),
    },
),
```

**Step 2** — Verify syntax:
```bash
python3 check_syntax.py
python3 main.py --list | grep my-app
```

**Step 3** — Test the install (on a real Linux machine or VM):
```bash
python3 main.py --cli install my-app
```

> **Tips:**
> - Always provide a `flatpak` or `snap` fallback so the app works on all distros.
> - Use the `_s()` shortcut for simple package name lists.
> - Use `PackageSpec(snap_classic=True)` for apps that need `--classic` snap flag.
> - Use `preferred_pm="flatpak"` if the native packages are outdated.

### Adding a New Package Manager

1. Add a new subclass in `core/package_manager.py`:

```python
class MyPMPackageManager(BasePackageManager):
    name = "mypm"

    def install(self, packages, progress_cb=None):
        return self.run(["mypm", "install"] + packages,
                        progress_cb=progress_cb)

    def remove(self, packages, progress_cb=None):
        return self.run(["mypm", "remove"] + packages,
                        progress_cb=progress_cb)

    def update_all(self, progress_cb=None):
        return self.run(["mypm", "upgrade"], progress_cb=progress_cb)
```

2. Register it in `get_package_manager()`.
3. Add detection logic in `core/distro.py`.
4. Add `PackageSpec` entries in relevant catalog entries.

### Improving the GUI

- All colours and fonts are in `gui/styles.py` — touch only that file for theming changes.
- Individual panels are in `gui/components/` — keep each component self-contained.
- Never do long-running work on the main thread; use `threading.Thread` and callbacks.

---

## Code Style

- **Python 3.10+** — use `match/case`, `X | Y` unions, and `dataclasses` freely.
- **Type hints** everywhere — functions must have annotated parameters and return types.
- **Docstrings** on every public function and class.
- Follow **PEP 8** — 4-space indent, max 100 chars per line.
- No third-party linters are required, but `ruff` and `mypy` are welcome:
  ```bash
  pip install ruff mypy
  ruff check .
  mypy .
  ```

---

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Obsidian to the catalog
fix: handle missing flatpak remote gracefully
docs: update CONTRIBUTING with mypy instructions
refactor: extract _pick_pm into standalone function
chore: bump Python requirement to 3.11
```

---

## Pull Request Checklist

Before opening a PR, make sure:

- [ ] `python3 check_syntax.py` passes with no errors
- [ ] `python3 main.py --list` displays your new app (if adding one)
- [ ] New app has at least one native PM spec **and** one universal fallback
- [ ] No hardcoded distro checks in GUI code
- [ ] Code follows PEP 8 and has type hints
- [ ] Commit messages follow Conventional Commits
- [ ] PR description explains **what** changed and **why**

---

## Questions?

Open a GitHub Discussion or drop a comment on a related Issue. We're happy to help!
