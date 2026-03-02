# Linite — Suggestions & Improvement Recommendations

> Full codebase analysis conducted on 2026-03-02.  
> Covers new applications, missing features, dependency reduction, architecture improvements, and UX quick wins.

---

## Current State Snapshot

| Metric | Value |
|---|---|
| Total apps in catalog | ~69 across 12 categories |
| 3rd-party dependencies | 1 (PyYAML only) |
| Supported package managers | 6 (apt, dnf, pacman, zypper, flatpak, snap) |
| Profiles / presets | 6 (developer, student, gamer, content\_creator, daily\_user, security) |
| Lines of code | ~3,500+ |

---

## 1. New Applications to Add

### Password Managers *(category entirely missing)*

| App | Notes |
|---|---|
| **Bitwarden** | Most popular open-source PM; official Flatpak available |
| **KeePassXC** | Offline, cross-platform, privacy-first; available on all PMs |
| **1Password** | Popular with developers; official `.deb` / `.rpm` packages |

---

### Video Editors *(category entirely missing)*

| App | Notes |
|---|---|
| **Kdenlive** | Best free NLE on Linux; apt / Flatpak |
| **Shotcut** | Cross-platform, beginner-friendly; Flatpak |
| **DaVinci Resolve** | Industry standard; script-based install only |
| **OpenShot** | Lightweight alternative; Flatpak |

---

### Note-Taking Apps *(category entirely missing)*

| App | Notes |
|---|---|
| **Obsidian** | Extremely popular markdown vault app; AppImage / `.deb` |
| **Joplin** | Open-source, E2E encrypted; Flatpak |
| **Logseq** | Outliner / knowledge graph; Flatpak |
| **CherryTree** | Classic structured note-taking; available via apt |

---

### Terminal Emulators *(category entirely missing)*

| App | Notes |
|---|---|
| **Alacritty** | GPU-accelerated, very popular with developers |
| **Kitty** | GPU-accelerated, scriptable |
| **WezTerm** | GPU-accelerated, Lua-configurable |
| **Tilix** | Tiling terminal, common on GNOME |

---

### System Monitors *(only `htop` present)*

| App | Notes |
|---|---|
| **btop++** | Modern, beautiful TUI resource monitor |
| **Glances** | Web-UI capable system monitor; pip-installable |
| **Stacer** | GUI system optimizer + monitor |
| **Mission Center** | GNOME-native task manager; Flatpak |

---

### VPN Apps *(category entirely missing)*

| App | Notes |
|---|---|
| **ProtonVPN** | Privacy-first; official `.deb` / `.rpm`; free tier available |
| **Mullvad** | Privacy-focused; official packages |
| **WireGuard** | Kernel module / protocol; essential for modern VPN setups |
| **OpenVPN** | Industry standard; available on all PMs |

---

### File Managers *(category entirely missing)*

| App | Notes |
|---|---|
| **Nautilus** | GNOME default file manager |
| **Thunar** | Lightweight XFCE file manager |
| **Nemo** | Cinnamon / Linux Mint file manager |
| **Dolphin** | KDE file manager |

---

### Remote Desktop *(category entirely missing)*

| App | Notes |
|---|---|
| **Remmina** | Best multi-protocol remote desktop client; apt / Flatpak |
| **RustDesk** | Open-source AnyDesk alternative; self-hostable |
| **AnyDesk** | Popular commercial option; official `.deb` |

---

### Cloud Storage *(only Dropbox present)*

| App | Notes |
|---|---|
| **Nextcloud Desktop** | Open-source self-hosted cloud; Flatpak |
| **rclone** | CLI for all cloud providers (OneDrive, GDrive, S3 …) |
| **Insync** | Google Drive + OneDrive sync client for Linux |

---

### Development Extras *(several key tools missing)*

| App | Notes |
|---|---|
| **Postman** | API testing; Flatpak available |
| **Insomnia** | Open-source API client; Flatpak |
| **DBeaver** | Universal database GUI; Flatpak |
| **Android Studio** | Mobile development; script-based install |
| **JetBrains Toolbox** | Manages all JetBrains IDEs; script-based install |
| **Podman** | Docker-compatible rootless containers |
| **kubectl** | Kubernetes CLI |
| **Helm** | Kubernetes package manager |

---

### Browsers *(minor gaps)*

| App | Notes |
|---|---|
| **LibreWolf** | Privacy-hardened Firefox fork |
| **Floorp** | Firefox-based; gaining popularity |
| **Microsoft Edge** | Required by many corporate / WSL users; official `.deb` |

---

### Gaming Extras *(critical gaps)*

| App | Notes |
|---|---|
| **Heroic Games Launcher** | Epic Games + GOG on Linux; Flatpak |
| **Bottles** | Wine-based Windows app manager; Flatpak |
| **GameMode** | Feral's CPU / GPU optimizer for games |
| **MangoHud** | In-game FPS / HUD overlay |
| **ProtonUp-Qt** | Manage Proton / Wine versions for Steam |

---

### Media Extras

| App | Notes |
|---|---|
| **Kooha** | Wayland screen recorder; Flatpak |
| **Pitivi** | GNOME video editor |
| **LMMS** | Free music production |
| **Ardour** | Professional DAW |
| **Rhythmbox** | GNOME music player |
| **Strawberry** | Modern music player with Last.fm scrobbling |

---

### Security & Privacy Extras *(build on existing Security category)*

| App | Notes |
|---|---|
| **ClamAV** | Open-source antivirus; apt / dnf / pacman |
| **UFW / Gufw** | Uncomplicated Firewall + GUI frontend |
| **Fail2ban** | Brute-force login protection |
| **Nikto** | Web server vulnerability scanner |
| **Gobuster** | Directory / DNS brute-forcer |

---

## 2. New Features to Build

### 🔴 High Priority

#### A. Export as Shell Script
Generate a reproducible `.sh` from any selection. One of the most requested features on Ninite-style tools. Users can version-control their machine setup.

```python
def export_as_script(selected_ids: list[str], path: str) -> None:
    # Write #!/usr/bin/env bash + install commands per selected app
```

CLI usage:
```bash
linite --export mysetup.sh
```

---

#### B. Disk Space Pre-check
Before installing, estimate required space and warn if free space is low. Read from `df -h /` and compare against known package sizes.

---

#### C. Network Connectivity Check
Perform a ping/DNS check before starting any installation. Show a warning banner in the GUI if the machine appears offline.

---

#### D. Rollback / Undo Last Session
`history.yaml` already records every action. Add a `--rollback` CLI flag (and a GUI button) that uninstalls every app installed during the most recent session.

```bash
linite --rollback        # undo last session
linite --rollback --dry  # show what would be removed
```

---

#### E. AppImage Support
Add `"appimage"` as a 4th fallback (after flatpak → snap). Many apps (Obsidian, Joplin, Headlamp) only distribute AppImages. Implement a standard installer that places the binary in `~/.local/bin` and creates a `.desktop` file.

---

### 🟠 Medium Priority

#### F. AUR Helper Auto-Install for Arch
`core/detection.py` already identifies Arch Linux. If neither `yay` nor `paru` is present, offer to install one automatically. This unlocks the `"aur"` pm key in `install_specs`.

---

#### G. Scheduled Update Notifications
Add a `--daemon` mode that runs `update_system()` once per day and fires a `notify-send` desktop notification showing the number of pending updates.

```bash
linite --daemon &
```

---

#### H. Fuzzy Search in GUI
Replace exact-match filtering in `SoftwarePanel` with fuzzy matching. Typing `"cod"` should still find `"VS Code"`. Implement using `difflib.SequenceMatcher` — **no new dependency required**.

---

#### I. Tag / Label Filtering
Add an optional `tags` field to `SoftwareEntry` (e.g., `tags=["privacy", "browser"]`) and render a tag-cloud sidebar in the GUI. Works alongside the existing category filter.

---

#### J. Per-App Version Badge / Changelog
Show the latest version and changelog for Flatpak apps by querying the Flathub API:

```
GET https://flathub.org/api/v2/appstream/<flatpak-id>
```

Cache responses locally for offline use.

---

#### K. Remote / SSH Install Mode
Install apps on a remote machine over SSH:

```bash
linite --remote user@192.168.1.10 --install vscode git docker
```

Useful for sysadmins provisioning servers or home-lab machines.

---

#### L. App Popularity Indicators
Pull install-count data from the Flathub API and display a small badge (e.g., `★ 50k`) next to popular apps. Helps new users make better choices.

---

### 🟡 Lower Priority

#### M. Nix / NixOS Support
Add `"nix"` as a package manager backend. Detect it via `nix --version`. Enables NixOS users and anyone running Nix on another distro.

---

#### N. Offline / Cached Mode
Pre-download `.deb` / `.rpm` packages to a local cache directory before presenting the GUI. Useful for air-gapped servers or slow/metered connections.

---

#### O. Plugin / Drop-In Catalog
Load any `*.yaml` files from `~/.config/linite/catalog/` at startup and merge them into `CATALOG`. Lets teams distribute custom app definitions without forking the project.

---

#### P. Light Mode Toggle
Currently dark-mode only (`gui/styles.py`). Add a `--light` flag and an in-app menu option that swaps the colour palette.

---

#### Q. Profile Import / Export
```bash
linite --export-profile mysetup.yaml   # save current selection as a profile
linite --import-profile mysetup.yaml   # restore from file
```

Enables easy machine cloning and sharing configurations with teammates.

---

## 3. Dependency Reduction

### Eliminate PyYAML → stdlib TOML *(highest value, zero runtime cost)*

PyYAML is the **only** 3rd-party dependency. Python 3.11+ ships `tomllib` in the standard library with no install required. Migrating all YAML data files to TOML would make Linite a truly zero-dependency project.

**Files to migrate:**

| Current | Proposed |
|---|---|
| `data/profiles/*.yaml` | `data/profiles/*.toml` |
| `data/package_maps/*.yaml` | `data/package_maps/*.toml` |
| `~/.config/linite/history.yaml` | `~/.config/linite/history.toml` |
| `~/.config/linite/profiles/*.yaml` | `~/.config/linite/profiles/*.toml` |

**Code changes:**
- `core/history.py` — replace `yaml.safe_load` / `yaml.dump` with `tomllib.load` / manual TOML write (or `tomli-w` for writes)
- `core/profile_engine.py` — replace YAML loader with `tomllib`
- `core/package_map.py` — replace YAML loader with `tomllib`
- `requirements.txt` — **delete PyYAML entry** (file becomes empty or removed)

> `history.py` already has a JSON → YAML migration pattern; extend it to also migrate YAML → TOML for existing users.

> **Alternative:** If YAML authoring is preferred for human-edited files, keep PyYAML only for user-facing files and use `tomllib` everywhere else.

---

## 4. Architecture Improvements

### A. Split `software_catalog.py` into Per-Category YAML / TOML Files
At 1,237 lines, `software_catalog.py` is becoming a maintenance bottleneck. Move app definitions to `data/catalog/<category>.yaml` and load dynamically at startup. New apps get added without touching Python.

```
data/catalog/browsers.yaml
data/catalog/development.yaml
data/catalog/gaming.yaml
data/catalog/security.yaml
...
```

---

### B. Set `preferred_pm` Consistently for All Apps
Most entries lack `preferred_pm`. Apply a clear policy:

- Apps in `_BENEFITS_FROM_FLATPAK` (already tracked in `intelligence.py`) → `preferred_pm = "flatpak"`
- Server/CLI tools → native PM only
- Sync the `_BENEFITS_FROM_FLATPAK` list with the `preferred_pm` field across the catalog

---

### C. Catalog Validation at Startup
Add a `catalog_lint()` function in `utils/helpers.py` that checks every `SoftwareEntry` has at least one `install_spec` compatible with the currently detected distro's package manager. Emit a clear warning (not a crash) for missing entries.

---

### D. Stricter Type Hints
`core/execution_engine.py` uses `Any` in several places. Tighten types throughout and add a `py.typed` marker file to enable fully typed usage from downstream tools and IDEs.

---

### E. Shell Completion for CLI
Generate tab-completion for `linite --cli install <TAB>` using `argcomplete` or a hand-written completion script. Arch and Fedora users especially expect this.

---

## 5. UX Quick Wins

| Fix | Effort | Impact |
|---|---|---|
| Show `✓` badge for apps already installed on the system | Low | High |
| Remember last window size and position across sessions | Very Low | Medium |
| Right-click app → **"Open Website"** context menu | Very Low | Medium |
| `Ctrl+F` keyboard shortcut to focus the search box | Very Low | High |
| Batch-copy selected app IDs for CLI reuse | Low | Medium |
| "What's New" panel on first launch after an update | Low | Medium |
| Sort apps within each category by popularity | Medium | High |
| Show estimated total install time before confirming | Medium | Medium |

---

## 6. Priority Summary

| Priority | Item |
|---|---|
| 🔴 1 | Add Password Managers — Bitwarden, KeePassXC |
| 🔴 2 | Add Video Editors — Kdenlive, Shotcut |
| 🔴 3 | **Feature:** Export as Shell Script |
| 🔴 4 | **Dependency:** Eliminate PyYAML → stdlib TOML |
| 🟠 5 | Add Terminal Emulators — Alacritty, Kitty, WezTerm |
| 🟠 6 | Add VPN Apps — ProtonVPN, WireGuard, Mullvad |
| 🟠 7 | **Feature:** Disk space pre-check before install |
| 🟠 8 | **Feature:** AUR helper auto-detection for Arch |
| 🟠 9 | Add Note-Taking Apps — Obsidian, Joplin |
| 🟠 10 | Add Gaming Extras — Heroic, Bottles, MangoHud |
| 🟡 11 | **Architecture:** Split catalog into per-category YAML files |
| 🟡 12 | **Feature:** Fuzzy search in GUI |
| 🟡 13 | **Feature:** AppImage support as install fallback |
| 🟡 14 | **Feature:** Remote / SSH install mode |
| 🟡 15 | **Feature:** Plugin / drop-in catalog from `~/.config/linite/catalog/` |

---

> The three changes with the **best effort-to-impact ratio** are:
> 1. **Adding Bitwarden / KeePassXC** — users universally expect a password manager option
> 2. **Export as Shell Script** — makes Linite setups reproducible and version-controllable
> 3. **Dropping PyYAML for stdlib TOML** — zero runtime cost, eliminates the only external dependency
