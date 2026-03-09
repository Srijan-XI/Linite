# Linite — Architecture Overview

This document describes the internal architecture of Linite: how the modules are structured, how data flows through the system, and the design decisions behind the implementation.

---

## Table of Contents

- [High-Level Overview](#high-level-overview)
- [Module Map](#module-map)
- [Layer Descriptions](#layer-descriptions)
  - [Entry Point](#entry-point-mainpy)
  - [Core Layer](#core-layer)
  - [Data Layer](#data-layer)
  - [GUI Layer](#gui-layer)
  - [Utils Layer](#utils-layer)
- [Key Data Flows](#key-data-flows)
  - [GUI Install Flow](#gui-install-flow)
  - [CLI Install Flow](#cli-install-flow)
  - [System Update Flow](#system-update-flow)
- [Design Patterns](#design-patterns)
- [Threading Model](#threading-model)
- [Package Manager Priority](#package-manager-priority)
- [Distro Detection](#distro-detection)
- [Software Catalog Schema](#software-catalog-schema)

---

## High-Level Overview

```
┌───────────────────────────────────────────────────────────┐
│                        main.py                            │
│              Entry point · GUI or CLI dispatch            │
└────────────────────┬─────────────────────┬────────────────┘
                     │                     │
          ┌──────────▼──────┐   ┌──────────▼──────────┐
          │    gui/app.py   │   │   CLI (argparse)     │
          │  Tkinter Window │   │  install / update    │
          └──────────┬──────┘   └──────────┬───────────┘
                     │                     │
          ┌──────────▼─────────────────────▼───────────┐
          │                  core/                      │
          │  distro · package_manager · installer       │
          │  uninstaller · updater · history · profiles │
          └──────────┬──────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │       data/         │
          │  software_catalog   │
          └─────────────────────┘
```

---

## Module Map

```
linite/
├── main.py                        # Entry point
├── requirements.txt               # Zero mandatory deps; stdlib only
├── check_syntax.py                # Quick syntax validator
│
├── core/
│   ├── __init__.py
│   ├── distro.py                  # Distro detection → DistroInfo
│   ├── package_manager.py         # PM abstraction (apt/dnf/pacman/zypper/snap/flatpak)
│   ├── installer.py               # Orchestrates installs, parallel support
│   ├── uninstaller.py             # Orchestrates removals
│   ├── updater.py                 # Full system update across all PMs
│   ├── history.py                 # Persists install history to disk
│   └── profiles.py                # JSON-based save/load of app selections
│
├── data/
│   ├── __init__.py
│   └── software_catalog.py        # 69 SoftwareEntry definitions, CATALOG list
│
├── gui/
│   ├── __init__.py
│   ├── app.py                     # LiniteApp(tk.Tk) — root window, orchestrator
│   ├── styles.py                  # BG_DARK, fonts, colour constants
│   └── components/
│       ├── __init__.py
│       ├── category_panel.py      # Left sidebar (category filter)
│       ├── software_panel.py      # Scrollable app grid
│       ├── progress_panel.py      # Live install log + progress bar
│       └── app_detail.py          # Popup with full app info
│
└── utils/
    ├── __init__.py
    └── helpers.py                  # setup_logging, is_root, warn_if_not_linux
```

---

## Layer Descriptions

### Entry Point (`main.py`)

Responsibilities:
- Parse CLI arguments (`argparse`)
- Call `setup_logging()` and `warn_if_not_linux()`
- Dispatch to GUI (`LiniteApp().mainloop()`) or CLI handlers (`cmd_install`, `cmd_update`, `cmd_list`)

No business logic lives here — `main.py` is purely a router.

---

### Core Layer

#### `core/distro.py` — Distro Detection

**Key type:** `DistroInfo` (dataclass)

```python
@dataclass
class DistroInfo:
    name: str           # "Ubuntu"
    id: str             # "ubuntu"
    id_like: list       # ["debian"]
    version: str        # "24.04"
    arch: str           # "x86_64"
    package_manager: str  # "apt"
```

Detection reads `/etc/os-release` (with fallback to `/usr/lib/os-release`), then resolves which native package manager to assign.

**Family helpers** (`is_debian_based`, `is_fedora_based`, `is_arch_based`, `is_opensuse`) use both `id` and `id_like` so derived distros (e.g. Pop!_OS, Manjaro) are identified correctly.

---

#### `core/package_manager.py` — PM Abstraction

Implements the **Strategy pattern**.

```
BasePackageManager (ABC)
├── AptPackageManager       → apt
├── DnfPackageManager       → dnf
├── YumPackageManager       → yum
├── PacmanPackageManager    → pacman
├── ZypperPackageManager    → zypper
├── SnapPackageManager      → snap
└── FlatpakPackageManager   → flatpak
```

All subclasses share a `run()` method that:
1. Prepends `sudo` when needed
2. Streams stdout line-by-line
3. Calls an optional `progress_cb(line)` callback for live UI updates
4. Returns `(returncode, combined_output)`

A global `threading.Event` (`_CANCEL_EVENT`) allows any in-progress apt lock-retry loop to be aborted immediately from the GUI cancel button.

**Factory function:** `get_package_manager(pm_name: str) -> BasePackageManager`

---

#### `core/installer.py` — Install Orchestration

```python
def install_apps(
    entries: List[SoftwareEntry],
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> List[InstallResult]:
```

For each app:
1. `_pick_pm()` selects the best package manager (see [Package Manager Priority](#package-manager-priority))
2. The appropriate `BasePackageManager` instance is obtained via the factory
3. Install is executed; output is streamed to `progress_cb`
4. Result (`Status.SUCCESS` / `Status.FAILED` / `Status.SKIPPED`) is recorded

`InstallResult` captures: `app_id`, `app_name`, `status`, `pm_used`, `output`, `error`.

For script-based installs (`preferred_pm="script"`), the installer downloads the script URL, verifies its **SHA-256 checksum** against `PackageSpec.sha256`, then executes it.

---

#### `core/updater.py` — System Update

`update_system()` runs update on every available package manager in sequence:
1. Native PM (`apt upgrade`, `dnf upgrade`, etc.)
2. Flatpak (`flatpak update`) — if available
3. Snap (`snap refresh`) — if available

Results are returned as `{ pm_name: (returncode, output) }`.

---

#### `core/profiles.py` — App Selections

Profiles are stored as JSON files under `~/.config/linite/profiles/`:

```json
{
  "version": 1,
  "name": "dev-machine",
  "apps": ["git", "nodejs", "docker", "vs-code", "discord"]
}
```

`save_profile()` / `load_profile()` allow the GUI's Export/Import buttons to persist and replay any selection.

---

#### `core/history.py` — Install History

Tracks which app IDs have been installed in the current session. The GUI uses this to visually mark already-installed apps.

---

### Data Layer

#### `data/software_catalog.py`

Defines two key types:

**`PackageSpec`** — How to install one app via one PM:
```python
@dataclass
class PackageSpec:
    packages: List[str]         # package names for apt/dnf/pacman/zypper
    snap_classic: bool          # use --classic flag
    flatpak_remote: str         # usually "flathub"
    script_url: str             # download-and-run install script
    sha256: str                 # checksum for script/deb
    pre_commands: List[str]     # run before install
    post_commands: List[str]    # run after install
```

**`SoftwareEntry`** — One app with all its PM variants:
```python
@dataclass
class SoftwareEntry:
    id: str
    name: str
    description: str
    category: str
    icon: str
    website: str
    install_specs: Dict[str, PackageSpec]  # key = pm name or "universal"
    preferred_pm: Optional[str]
```

The special key `"universal"` in `install_specs` acts as a catch-all fallback when no PM-specific spec exists.

**Exported symbols:**
| Symbol | Type | Description |
|--------|------|-------------|
| `CATALOG` | `List[SoftwareEntry]` | All 69 app entries |
| `CATALOG_MAP` | `Dict[str, SoftwareEntry]` | Fast lookup by `id` |
| `CATEGORIES` | `List[str]` | Ordered category list |

---

### GUI Layer

#### `gui/app.py` — `LiniteApp(tk.Tk)`

The root window. Owns:
- `_distro: DistroInfo` — detected at startup
- `_busy: bool` — mutex to prevent concurrent installs
- `_selected: Set[str]` — currently checked app IDs

Assembles four panels:
```
┌─────────────────────────────────────────────────────┐
│  header bar  (distro info · search · update button)  │
├──────────────┬──────────────────────────────────────┤
│ CategoryPanel│           SoftwarePanel               │
│  (sidebar)   │    (scrollable app grid)              │
├──────────────┴──────────────────────────────────────┤
│              ProgressPanel (log + progress bar)      │
└─────────────────────────────────────────────────────┘
```

Install / Uninstall / Update all run in **daemon threads** with callbacks back to the main thread for UI updates.

---

#### `gui/styles.py`

Single source of truth for all visual constants:
```python
BG_DARK   = "#1e1e2e"
BG_PANEL  = "#2a2a3e"
ACCENT    = "#7c6af7"
FG_TEXT   = "#cdd6f4"
FONT_BODY = ("Inter", 10)
WINDOW_W  = 1100
WINDOW_H  = 720
```

---

#### `gui/components/`

| Component | Responsibility |
|-----------|----------------|
| `CategoryPanel` | Left sidebar; emits a filter event when a category is clicked |
| `SoftwarePanel` | Scrollable grid of app cards; manages checkbox state |
| `ProgressPanel` | Scrollable log widget + ttk progress bar |
| `AppDetailWindow` | Toplevel popup showing full app info, website, and uninstall button |

---

### Utils Layer

#### `utils/helpers.py`

| Function | Purpose |
|----------|---------|
| `setup_logging(verbose)` | Configures root logger |
| `is_root()` | Cross-platform root/admin check |
| `warn_if_not_root()` | Prints warning; does not exit |
| `warn_if_not_linux()` | Prints info if not on Linux; GUI opens in preview mode |

---

## Key Data Flows

### GUI Install Flow

```
User clicks "Install"
        │
        ▼
LiniteApp._on_install_click()
        │   collect checked SoftwareEntry list
        │   set _busy = True
        │   clear_cancel()
        ▼
threading.Thread(target=install_apps, args=(..., progress_cb))
        │
        ▼ (background thread)
installer.install_apps()
        │   for each entry:
        │     _pick_pm() → pm name
        │     get_package_manager(pm) → BasePackageManager
        │     pm.install(packages, progress_cb)  ──► streams lines
        │                                              │
        │                     progress_cb(app_id, line)◄─┘
        │                              │
        ▼                              ▼ (main thread via after())
InstallResult list             ProgressPanel.append_log(line)
        │
        ▼
LiniteApp._on_install_done()
        set _busy = False
        refresh SoftwarePanel (mark installed apps)
```

### CLI Install Flow

```
main.py --cli install vlc git nodejs
        │
        ▼
cmd_install(app_ids=["vlc", "git", "nodejs"])
        │   distro.detect()
        │   [CATALOG_MAP[id] for id in app_ids]
        ▼
install_apps(entries, distro, progress_cb=print)
        │   (same core logic as GUI, callbacks print to stdout)
        ▼
print summary table
```

### System Update Flow

```
User clicks "Update System"  (or --cli update)
        │
        ▼
update_system(distro, include_flatpak, include_snap, progress_cb)
        │
        ├─► native PM update   (apt upgrade / dnf upgrade / …)
        ├─► flatpak update      (if flatpak binary found)
        └─► snap refresh        (if snap binary found)
        │
        ▼
results dict { pm: (rc, output) }
```

---

## Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Strategy** | `core/package_manager.py` | Swap PM implementations transparently |
| **Factory** | `get_package_manager()` | Instantiate correct PM at runtime |
| **Observer / Callback** | `installer.py` → `gui/app.py` | Stream live output without coupling |
| **Dataclass** | `DistroInfo`, `SoftwareEntry`, `PackageSpec`, `InstallResult` | Immutable, type-safe configuration objects |
| **Abstract Base Class** | `BasePackageManager` | Enforce a consistent interface contract |
| **Data-Driven UI** | `data/software_catalog.py` | Catalog is pure data; UI has no hardcoded app logic |

---

## Threading Model

```
Main Thread (Tkinter event loop)
    │
    ├── GUI rendering & event handling
    ├── Receives progress callbacks via widget.after()
    └── Flips _busy flag to block re-entry

Installer Thread (daemon)
    │
    ├── Runs install_apps() or update_system()
    ├── Invokes progress_cb(app_id, line) for each output line
    └── Calls on_done callback when finished

Cancel Mechanism
    └── request_cancel() sets _CANCEL_EVENT
        └── apt lock-retry loops in package_manager.py check this event
```

**Rule:** No Tkinter widget methods are called directly from background threads. All UI updates go through `self.after(0, callback)`.

---

## Package Manager Priority

When selecting how to install an app, `_pick_pm()` in `installer.py` follows this order:

```
1. entry.preferred_pm          (explicit override in catalog)
       │ if spec exists for this PM
       ▼
2. distro.package_manager      (native: apt / dnf / pacman / zypper)
       │ if entry has a spec for this PM
       ▼
3. "universal"                  (catch-all spec)
       │ if catalog has a "universal" key
       ▼
4. flatpak                      (if binary available on system)
       ▼
5. snap                         (if binary available on system)
       ▼
6. None → SKIPPED
```

---

## Distro Detection

`core/distro.detect()` proceeds as follows:

```
1. Read /etc/os-release (or /usr/lib/os-release)
2. Extract: ID, ID_LIKE, NAME, VERSION_ID, VERSION_CODENAME
3. Derive: is_debian_based / is_fedora_based / is_arch_based / is_opensuse
4. Assign package_manager string:
       debian-based  → "apt"
       fedora-based  → "dnf"  (or "yum" for older RHEL)
       arch-based    → "pacman"
       opensuse      → "zypper"
       other/unknown → "unknown"
5. Detect architecture via platform.machine()
6. Return DistroInfo dataclass
```

---

## Software Catalog Schema

```
SoftwareEntry
├── id             str          "vs-code"
├── name           str          "Visual Studio Code"
├── description    str          "Code editor by Microsoft"
├── category       str          "Development"
├── icon           str          "💻"
├── website        str          "https://code.visualstudio.com"
├── preferred_pm   str|None     None  (use distro default)
└── install_specs  dict
    ├── "apt"      PackageSpec  packages=["code"]
    ├── "dnf"      PackageSpec  packages=["code"]
    ├── "pacman"   PackageSpec  packages=["visual-studio-code-bin"]
    ├── "snap"     PackageSpec  packages=["code"], snap_classic=True
    ├── "flatpak"  PackageSpec  packages=["com.visualstudio.code"]
    └── "universal" PackageSpec packages=["code"]  ← fallback

PackageSpec
├── packages       List[str]    package name(s) to pass to PM
├── snap_classic   bool         add --classic flag to snap install
├── flatpak_remote str          "flathub" (default)
├── script_url     str          URL of install shell script
├── sha256         str          expected hash of downloaded file
├── pre_commands   List[str]    shell commands run before install
└── post_commands  List[str]    shell commands run after install
```
