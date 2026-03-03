# Linite — Suggestions & Improvement Recommendations

> Full codebase analysis conducted on 2026-03-02.  
> Covers new applications, missing features, dependency reduction, architecture improvements, and UX quick wins.
>
> **Status review updated** — ✅ Done · ❌ Todo · ⚠️ Partial

---

## Current State Snapshot

| Metric | Value |
|---|---|
| Total apps in catalog | ~90+ across 17 categories |
| 3rd-party dependencies | 0 |
| Supported package managers | 6 (apt, dnf, pacman, zypper, flatpak, snap) |
| Profiles / presets | 6 (developer, student, gamer, content\_creator, daily\_user, security) |
| Lines of code | ~4,500+ |

---

## 1. New Applications to Add

### Password Managers *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Bitwarden** | Most popular open-source PM; official Flatpak available | ✅ Done |
| **KeePassXC** | Offline, cross-platform, privacy-first; available on all PMs | ✅ Done |
| **1Password** | Popular with developers; official `.deb` / `.rpm` packages | ✅ Done |

---

### Video Editors *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Kdenlive** | Best free NLE on Linux; apt / Flatpak | ✅ Done |
| **Shotcut** | Cross-platform, beginner-friendly; Flatpak | ✅ Done |
| **DaVinci Resolve** | Industry standard; script-based install only | ❌ Todo |
| **OpenShot** | Lightweight alternative; Flatpak | ✅ Done |

---

### Note-Taking Apps *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Obsidian** | Extremely popular markdown vault app; AppImage / `.deb` | ✅ Done |
| **Joplin** | Open-source, E2E encrypted; Flatpak | ✅ Done |
| **Logseq** | Outliner / knowledge graph; Flatpak | ✅ Done |
| **CherryTree** | Classic structured note-taking; available via apt | ✅ Done |

---

### Terminal Emulators *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Alacritty** | GPU-accelerated, very popular with developers | ✅ Done |
| **Kitty** | GPU-accelerated, scriptable | ✅ Done |
| **WezTerm** | GPU-accelerated, Lua-configurable | ✅ Done |
| **Tilix** | Tiling terminal, common on GNOME | ✅ Done |

---

### System Monitors *(only `htop` present)*

| App | Notes | Status |
|---|---|---|
| **btop++** | Modern, beautiful TUI resource monitor | ❌ Todo |
| **Glances** | Web-UI capable system monitor; pip-installable | ❌ Todo |
| **Stacer** | GUI system optimizer + monitor | ❌ Todo |
| **Mission Center** | GNOME-native task manager; Flatpak | ❌ Todo |

---

### VPN Apps *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **ProtonVPN** | Privacy-first; official `.deb` / `.rpm`; free tier available | ✅ Done |
| **Mullvad** | Privacy-focused; official packages | ✅ Done |
| **WireGuard** | Kernel module / protocol; essential for modern VPN setups | ✅ Done |
| **OpenVPN** | Industry standard; available on all PMs | ✅ Done |

---

### File Managers *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Nautilus** | GNOME default file manager | ❌ Todo |
| **Thunar** | Lightweight XFCE file manager | ❌ Todo |
| **Nemo** | Cinnamon / Linux Mint file manager | ❌ Todo |
| **Dolphin** | KDE file manager | ❌ Todo |

---

### Remote Desktop *(category entirely missing)*

| App | Notes | Status |
|---|---|---|
| **Remmina** | Best multi-protocol remote desktop client; apt / Flatpak | ❌ Todo |
| **RustDesk** | Open-source AnyDesk alternative; self-hostable | ❌ Todo |
| **AnyDesk** | Popular commercial option; official `.deb` | ❌ Todo |

---

### Cloud Storage *(only Dropbox present)*

| App | Notes | Status |
|---|---|---|
| **Nextcloud Desktop** | Open-source self-hosted cloud; Flatpak | ❌ Todo |
| **rclone** | CLI for all cloud providers (OneDrive, GDrive, S3 …) | ❌ Todo |
| **Insync** | Google Drive + OneDrive sync client for Linux | ❌ Todo |

---

### Development Extras *(several key tools missing)*

| App | Notes | Status |
|---|---|---|
| **Postman** | API testing; Flatpak available | ❌ Todo |
| **Insomnia** | Open-source API client; Flatpak | ❌ Todo |
| **DBeaver** | Universal database GUI; Flatpak | ❌ Todo |
| **Android Studio** | Mobile development; script-based install | ❌ Todo |
| **JetBrains Toolbox** | Manages all JetBrains IDEs; script-based install | ❌ Todo |
| **Podman** | Docker-compatible rootless containers | ❌ Todo |
| **kubectl** | Kubernetes CLI | ❌ Todo |
| **Helm** | Kubernetes package manager | ❌ Todo |

---

### Browsers *(minor gaps)*

| App | Notes | Status |
|---|---|---|
| **LibreWolf** | Privacy-hardened Firefox fork | ❌ Todo |
| **Floorp** | Firefox-based; gaining popularity | ❌ Todo |
| **Microsoft Edge** | Required by many corporate / WSL users; official `.deb` | ❌ Todo |

---

### Gaming Extras *(critical gaps)*

| App | Notes | Status |
|---|---|---|
| **Heroic Games Launcher** | Epic Games + GOG on Linux; Flatpak | ✅ Done |
| **Bottles** | Wine-based Windows app manager; Flatpak | ✅ Done |
| **GameMode** | Feral's CPU / GPU optimizer for games | ✅ Done |
| **MangoHud** | In-game FPS / HUD overlay | ✅ Done |
| **ProtonUp-Qt** | Manage Proton / Wine versions for Steam | ✅ Done |

---

### Media Extras

| App | Notes | Status |
|---|---|---|
| **Kooha** | Wayland screen recorder; Flatpak | ❌ Todo |
| **Pitivi** | GNOME video editor | ❌ Todo |
| **LMMS** | Free music production | ❌ Todo |
| **Ardour** | Professional DAW | ❌ Todo |
| **Rhythmbox** | GNOME music player | ❌ Todo |
| **Strawberry** | Modern music player with Last.fm scrobbling | ❌ Todo |

---

### Security & Privacy Extras *(build on existing Security category)*

| App | Notes | Status |
|---|---|---|
| **ClamAV** | Open-source antivirus; apt / dnf / pacman | ❌ Todo |
| **UFW / Gufw** | Uncomplicated Firewall + GUI frontend | ❌ Todo |
| **Fail2ban** | Brute-force login protection | ❌ Todo |
| **Nikto** | Web server vulnerability scanner | ❌ Todo |
| **Gobuster** | Directory / DNS brute-forcer | ❌ Todo |

---

## 2. New Features to Build

### 🔴 High Priority

#### ✅ A. Export as Shell Script
Generate a reproducible `.sh` from any selection. One of the most requested features on Ninite-style tools. Users can version-control their machine setup.

```python
def export_as_script(selected_ids: list[str], path: str) -> None:
    # Write #!/usr/bin/env bash + install commands per selected app
```

CLI usage:
```bash
linite --export mysetup.sh
linite --export mysetup.sh --pm apt
linite --export mysetup.sh --cli install vlc git docker
```

> **Implemented** in `core/script_exporter.py` — `export_as_script()` and `export_to_file()`.  
> CLI flag `--export <FILE>` added to `main.py` (optionally combined with `--pm` and `--cli install <ids>`).  
> GUI button **"📜 Export Script"** added to the action bar in `gui/app.py` — opens a save-file dialog, writes the script, and shows a success message.

Generated scripts:
- Start with `#!/usr/bin/env bash` + `set -euo pipefail`
- Auto-detect the host distro's package manager at runtime
- Emit `pre_commands`, install command, and `post_commands` per app
- Support all six PMs: apt, dnf, pacman, zypper, snap, flatpak
- Are chmod +x'd automatically on POSIX systems

---

#### ✅ B. Disk Space Pre-check
Before installing, estimate required space and warn if free space is low. Read from `df -h /` and compare against known package sizes.

> **Implemented** in `core/execution_engine.py` (lines 242–270) — uses `shutil.disk_usage("/")` and warns if space is low or insufficient before starting any install.

---

#### ❌ C. Network Connectivity Check
Perform a ping/DNS check before starting any installation. Show a warning banner in the GUI if the machine appears offline.

---

#### ❌ D. Rollback / Undo Last Session
`history.yaml` already records every action. Add a `--rollback` CLI flag (and a GUI button) that uninstalls every app installed during the most recent session.

```bash
linite --rollback        # undo last session
linite --rollback --dry  # show what would be removed
```

---

#### ❌ E. AppImage Support
Add `"appimage"` as a 4th fallback (after flatpak → snap). Many apps (Obsidian, Joplin, Headlamp) only distribute AppImages. Implement a standard installer that places the binary in `~/.local/bin` and creates a `.desktop` file.

---

### 🟠 Medium Priority

#### ✅ F. AUR Helper Auto-Install for Arch
`core/detection.py` already identifies Arch Linux. If neither `yay` nor `paru` is present, offer to install one automatically. This unlocks the `"aur"` pm key in `install_specs`.

---

#### ❌ G. Scheduled Update Notifications
Add a `--daemon` mode that runs `update_system()` once per day and fires a `notify-send` desktop notification showing the number of pending updates.

```bash
linite --daemon &
```

---

#### ✅ H. Fuzzy Search in GUI
Replace exact-match filtering in `SoftwarePanel` with fuzzy matching. Typing `"cod"` should still find `"VS Code"`. Implement using `difflib.SequenceMatcher` — **no new dependency required**.

> **Current state:** `_apply_filters()` uses plain substring match (`q in e.name.lower()`). No `difflib` usage found anywhere in the codebase.

---

#### ❌ I. Tag / Label Filtering
Add an optional `tags` field to `SoftwareEntry` (e.g., `tags=["privacy", "browser"]`) and render a tag-cloud sidebar in the GUI. Works alongside the existing category filter.

---

#### ❌ J. Per-App Version Badge / Changelog
Show the latest version and changelog for Flatpak apps by querying the Flathub API:

```
GET https://flathub.org/api/v2/appstream/<flatpak-id>
```

Cache responses locally for offline use.

---

#### ❌ K. Remote / SSH Install Mode
Install apps on a remote machine over SSH:

```bash
linite --remote user@192.168.1.10 --install vscode git docker
```

Useful for sysadmins provisioning servers or home-lab machines.

---

#### ❌ L. App Popularity Indicators
Pull install-count data from the Flathub API and display a small badge (e.g., `★ 50k`) next to popular apps. Helps new users make better choices.

---

### 🟡 Lower Priority

#### ❌ M. Nix / NixOS Support
Add `"nix"` as a package manager backend. Detect it via `nix --version`. Enables NixOS users and anyone running Nix on another distro.

---

#### ❌ N. Offline / Cached Mode
Pre-download `.deb` / `.rpm` packages to a local cache directory before presenting the GUI. Useful for air-gapped servers or slow/metered connections.

---

#### ❌ O. Plugin / Drop-In Catalog
Load any `*.yaml` files from `~/.config/linite/catalog/` at startup and merge them into `CATALOG`. Lets teams distribute custom app definitions without forking the project.

---

#### ❌ P. Light Mode Toggle
Currently dark-mode only (`gui/styles.py`). Add a `--light` flag and an in-app menu option that swaps the colour palette.

---

#### ⚠️ Q. Profile Import / Export
```bash
linite --export-profile mysetup.yaml   # save current selection as a profile
linite --import-profile mysetup.yaml   # restore from file
```

Enables easy machine cloning and sharing configurations with teammates.

> **Partial:** GUI Export / Import Profile buttons exist (`_export_btn`, `_import_btn` in `gui/app.py`) and `core/profiles.py` has `load_profile` / `save_profile`. The CLI flags `--export-profile` / `--import-profile` have **not** been added to `main.py`.

---

## 3. Dependency Reduction

### ✅ Eliminate PyYAML → stdlib TOML *(highest value, zero runtime cost)*

PyYAML is the **only** 3rd-party dependency. Python 3.11+ ships `tomllib` in the standard library with no install required. Migrating all YAML data files to TOML would make Linite a truly zero-dependency project.

> **Completed.** All data files converted to TOML; all loaders updated to `tomllib`; `pyyaml>=6.0` removed from `requirements.txt`. History reverts to JSON (write-support; no extra dep). User-created profiles serialised via a hand-written `_profile_to_toml()` helper. Legacy `.yaml` files auto-migrated to `.toml`/`.json` on first run.

**Files migrated:**

| Previous | Final |
|---|---|
| `data/profiles/*.yaml` | `data/profiles/*.toml` |
| `data/package_maps/*.yaml` | `data/package_maps/*.toml` |
| `~/.config/linite/history.yaml` | `~/.config/linite/history.json` (JSON — writable without extra dep) |
| `~/.config/linite/profiles/*.yaml` | `~/.config/linite/profiles/*.toml` (auto-migrated) |

**Code changes applied:**
- `core/history.py` — `yaml` removed; `json` only; YAML→JSON migration added
- `core/profile_engine.py` — `tomllib` loader; `_profile_to_toml()` serialiser; YAML→TOML migration on startup
- `core/package_map.py` — `tomllib` loader replacing `yaml.safe_load`
- `requirements.txt` — PyYAML entry deleted; file now lists zero runtime deps

---

## 4. Architecture Improvements

### ❌ A. Split `software_catalog.py` into Per-Category YAML / TOML Files
At 1,594 lines, `software_catalog.py` is becoming a maintenance bottleneck. Move app definitions to `data/catalog/<category>.yaml` and load dynamically at startup. New apps get added without touching Python.

```
data/catalog/browsers.yaml
data/catalog/development.yaml
data/catalog/gaming.yaml
data/catalog/security.yaml
...
```

---

### ⚠️ B. Set `preferred_pm` Consistently for All Apps
Most entries lack `preferred_pm`. Apply a clear policy:

- Apps in `_BENEFITS_FROM_FLATPAK` (already tracked in `intelligence.py`) → `preferred_pm = "flatpak"`
- Server/CLI tools → native PM only
- Sync the `_BENEFITS_FROM_FLATPAK` list with the `preferred_pm` field across the catalog

> **Partial:** All newly added entries (Password Managers, Video Editors, Terminal Emulators, VPN, Note Taking) consistently set `preferred_pm`. Older catalog entries have not been audited / backfilled.

---

### ❌ C. Catalog Validation at Startup
Add a `catalog_lint()` function in `utils/helpers.py` that checks every `SoftwareEntry` has at least one `install_spec` compatible with the currently detected distro's package manager. Emit a clear warning (not a crash) for missing entries.

---

### ❌ D. Stricter Type Hints
`core/execution_engine.py` uses `Any` in several places. Tighten types throughout and add a `py.typed` marker file to enable fully typed usage from downstream tools and IDEs.

---

### ❌ E. Shell Completion for CLI
Generate tab-completion for `linite --cli install <TAB>` using `argcomplete` or a hand-written completion script. Arch and Fedora users especially expect this.

---

## 5. UX Quick Wins

| Fix | Effort | Impact | Status |
|---|---|---|---|
| Show `✓` badge for apps already installed on the system | Low | High | ✅ Done |
| Remember last window size and position across sessions | Very Low | Medium | ❌ Todo |
| Right-click app → **"Open Website"** context menu | Very Low | Medium | ❌ Todo |
| `Ctrl+F` keyboard shortcut to focus the search box | Very Low | High | ❌ Todo |
| Batch-copy selected app IDs for CLI reuse | Low | Medium | ❌ Todo |
| "What's New" panel on first launch after an update | Low | Medium | ❌ Todo |
| Sort apps within each category by popularity | Medium | High | ❌ Todo |
| Show estimated total install time before confirming | Medium | Medium | ❌ Todo |

> **Installed badge:** `set_installed_ids()` in `gui/components/software_panel.py` renders a green `✓ installed` label per card and dims the app name.  
> **Right-click:** `Button-3` is bound on cards but opens the detail panel — NOT `webbrowser.open`. One-line change needed.  
> **Ctrl+F:** `_bind_shortcuts()` in `gui/app.py` has `Ctrl+A`, `Ctrl+Q`, `Ctrl+L` but **no** `Ctrl+F` → `search_entry.focus_set()`.

---

## 6. Priority Summary

| Priority | Item | Status |
|---|---|---|
| 🔴 1 | Add Password Managers — Bitwarden, KeePassXC | ✅ Done |
| 🔴 2 | Add Video Editors — Kdenlive, Shotcut | ✅ Done |
| 🔴 3 | **Feature:** Export as Shell Script | ✅ Done |
| 🔴 4 | **Dependency:** Eliminate PyYAML → stdlib TOML | ✅ Done |
| 🟠 5 | Add Terminal Emulators — Alacritty, Kitty, WezTerm | ✅ Done |
| 🟠 6 | Add VPN Apps — ProtonVPN, WireGuard, Mullvad | ✅ Done |
| 🟠 7 | **Feature:** Disk space pre-check before install | ✅ Done |
| 🟠 8 | **Feature:** AUR helper auto-detection for Arch | ✅ Done |
| 🟠 9 | Add Note-Taking Apps — Obsidian, Joplin | ✅ Done |
| 🟠 10 | Add Gaming Extras — Heroic, Bottles, MangoHud | ✅ Done |
| 🟡 11 | **Architecture:** Split catalog into per-category YAML files | ❌ Todo |
| 🟡 12 | **Feature:** Fuzzy search in GUI | ✅ Done |
| 🟡 13 | **Feature:** AppImage support as install fallback | ❌ Todo |
| 🟡 14 | **Feature:** Remote / SSH install mode | ❌ Todo |
| 🟡 15 | **Feature:** Plugin / drop-in catalog from `~/.config/linite/catalog/` | ❌ Todo |

---

> The three changes with the **best effort-to-impact ratio** are:
> 1. **Export as Shell Script** — makes Linite setups reproducible and version-controllable *(top remaining feature)*
> 2. **Dropping PyYAML for stdlib TOML** — zero runtime cost, eliminates the only external dependency
> 3. **Ctrl+F shortcut + right-click → Open Website** — two one-liner fixes with high perceived polish
