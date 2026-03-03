# Changelog

All notable changes to **Linite** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.4.0] — 2026-03-04

### Added
- Issue templates for bug reports, feature requests, and catalog additions
- `SECURITY.md` and `CODE_OF_CONDUCT.md` community health files
- GitHub Actions workflow for automated deployment to GitHub Pages
- Split monolithic `software_catalog.py` into per-category TOML files under `data/catalog/`

---

## [0.3.0] — 2026-03-03

### Added
- Initial project website (`site/`) with HTML, CSS, JavaScript, and images
- Interactive landing page with styling and interactivity for Linite
- **Export as Shell Script** — generate installable `.sh` scripts from selections (Priority 3)
- Confirmed full TOML catalog migration (Priority 4)

---

## [0.2.0] — 2026-03-02

### Added
- Fuzzy search for software using `difflib`, with AUR helper auto-detection
- Transaction log engine (`core/log_engine.py`) for persistent, structured audit logs
- GUI log viewer component (`gui/components/log_viewer.py`)
- Full GUI application window (`gui/app.py`) with category, software, progress, and action panels
- New software entries: gaming, password managers, video editors, terminal emulators, note-taking
- Free disk space check in system detection (`core/detection.py`)
- Package maps for apt, dnf, flatpak, pacman, snap, and zypper (`data/package_maps/`)
- User profiles: developer, student, gamer, content creator, daily user, security (`data/profiles/`)
- `CONTRIBUTING.md` and `ARCHITECTURE.md` documentation
- MIT License
- `.gitignore` with cached artifact cleanup
- `SUGGESTIONS.md` with status tracking and improvement metrics

### Changed
- Migrated log and profile storage formats from YAML to JSON
- Expanded package maps and updated all user profiles
- Updated README for improved clarity and completeness

### Fixed
- Flatpak installation command and install status checks

---

## [0.1.0] — 2026-03-01

### Added
- Initial commit of the Linite GUI application (`gui/`)
- Core software catalog (`data/software_catalog.py`)
- Installation engine (`core/installer.py`) and base package manager abstraction
- App detail popup window with resizable layout
- Uninstaller functionality (`core/uninstaller.py`)
- Category panel with per-category app counts
- Software panel with search bar, card hover highlights, and selection stripe click binding
- Cancel functionality for in-progress package management operations
- Mousewheel scrolling support in `SoftwarePanel`
- Retry logic for `apt` commands to handle lock contention
- Busy-dot guard to prevent UI errors before initialization
- Error logging during installation and update processes
- Syntax checker (`check_syntax.py`) covering core module paths
- Initial `README.md`

### Fixed
- Startup crash and miscellaneous codebase bugs
- Removed unnecessary `os` import from `BasePackageManager`

---

[Unreleased]: https://github.com/Srijan-XI/Linite/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Srijan-XI/Linite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Srijan-XI/Linite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Srijan-XI/Linite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Srijan-XI/Linite/releases/tag/v0.1.0
