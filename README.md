# Linite 🐧

> **The Linux equivalent of [Ninite](https://ninite.com/)** — pick your apps, click **Install**, and Linite silently sets up your entire system using the right package manager for your distro.

---

## ✨ Features

### Core
- 🖥️ **Full system detection** — distro, version, desktop environment, display server (X11/Wayland), CPU arch, RAM, GPU vendor & driver, VM/container awareness
- 📦 **Smart package selection** — native PMs (`apt`, `dnf`, `pacman`, `zypper`) with automatic fallback to `flatpak` → `snap`
- 🗺️ **TOML-driven package maps** — per-PM TOML files are the source of truth; the Python catalog is the fallback
- 🔄 **One-click system update** — upgrades all packages including Flatpak and Snap
- 📜 **TOML profiles & YAML history** — profiles stored as TOML; install history stored as human-readable YAML

### Quick-Start Profiles
- ⚡ **6 pre-built presets** — Developer, Student, Gamer, Content Creator, Daily User, Security/Pentester
- 🛠️ **System tweaks** — each profile runs post-install commands (enable Docker, add user to groups, set defaults…)
- 🧩 **User-defined profiles** — save, load, export and import custom selections as TOML

### Smart Execution
- 🔗 **Dependency ordering** — topological sort ensures curl installs before Docker, not after
- ⚡ **Parallel installs** — configurable thread pool installs independent apps simultaneously
- 🔁 **Retry with back-off** — up to 3 attempts with exponential delay (2 s → 4 s → 8 s)
- 🛡️ **Failure recovery** — if the native PM fails, automatically falls back to Flatpak then Snap

### Intelligence
- 💡 **10 contextual checks** run before installation:
  - Low / very-low RAM → suggests lighter alternatives (MPV instead of VLC, Vim instead of VS Code…)
  - NVIDIA GPU without proprietary driver → prompts to install nvidia-driver
  - NVIDIA + Wayland session → compatibility warning
  - Running inside a VM → GPU & performance advisory
  - Running in a container → blocks GUI-only apps
  - No desktop environment → warns about GUI apps on a server
  - Old Ubuntu LTS repos → suggests Flatpak for fresher versions
  - Non-x86 architecture → flags apps with no ARM package
  - Proprietary apps → licensing reminder
  - GPU-heavy apps on constrained hardware → performance warning

### GUI
- 🎨 **Dark-mode Tkinter GUI** — categorised, searchable, filterable software grid
- 🔍 **Debounced search** and category sidebar with app counts
- 📋 **App detail modal** — full description, website, install method per PM
- 🖱️ **Keyboard shortcuts** — `Ctrl+Q` Quick Start, `Ctrl+A` select all, `Enter` install, `Esc` cancel
- ⌨️ **CLI mode** — headless installs; export reproducible bash scripts with `--export`

---

## 🏗️ [Architecture](ARCHITECTURE.md)

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

> ★ = added or significantly enhanced in the latest update.

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Linite Pipeline                                  │
│                                                                         │
│  1. detect_system()                                                     │
│     └─ distro · DE · RAM · GPU · arch · VM/container · available PMs   │
│                                                                         │
│  2. IntelligenceEngine.analyze(system, selected_apps)                  │
│     └─ 10 checks → prioritised Suggestion list shown in GUI            │
│                                                                         │
│  3. PackageMapLoader.get_spec(app_id, pm)                              │
│     └─ TOML map (data/package_maps/<pm>.toml)                          │
│        └─ fallback: Python software_catalog.py                         │
│                                                                         │
│  4. ExecutionEngine.build_plan(app_ids, available_pms)                 │
│     └─ topological sort → installation waves                           │
│                                                                         │
│  5. ExecutionEngine.execute(plan, progress_cb)                         │
│     ├─ Wave 1 (no deps) ────────────────────────────────────────────── │
│     │   ├─ [thread] curl   ─ retry × 3, back-off, fallback PM         │
│     │   └─ [thread] wget   ─ retry × 3, back-off, fallback PM         │
│     └─ Wave 2 (depends on wave 1) ─────────────────────────────────── │
│         ├─ [thread] docker  ─ retry × 3, back-off, fallback PM        │
│         └─ [thread] vscode  ─ retry × 3, back-off, fallback PM        │
│                                                                         │
│  6. ProfileEngine.apply_tweaks(profile, installed_ids)                 │
│     └─ run post-install system commands (enable services, add groups…) │
│                                                                         │
│  7. history.record(…) → ~/.config/linite/history.yaml                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Software Catalog  (92 apps · 17 categories)

| Category | Count | Notable Apps |
|----------|------:|--------------|
| Web Browsers | 7 | Firefox, Chromium, Brave, Chrome, Opera, Tor Browser, Vivaldi |
| Development | 8 | VS Code, Git, Python 3, Node.js, Docker, Vim, Neovim, GitHub CLI |
| Media | 6 | VLC, Spotify, mpv, OBS Studio, Audacity, HandBrake |
| Communication | 5 | Discord, Telegram, Slack, Zoom, Dropbox |
| Utilities | 10 | htop, curl, wget, 7-Zip, Timeshift, Flatpak, Neofetch, Flameshot, Wireshark, Notepad++ |
| Office | 6 | LibreOffice, Thunderbird, Okular, Evince, Foxit Reader, OpenOffice |
| Gaming | 7 | Steam, Lutris, Heroic Games Launcher, Bottles, GameMode, MangoHud, ProtonUp-Qt |
| Graphics | 3 | GIMP, Inkscape, Blender |
| Torrents | 4 | qBittorrent, qBittorrent-nox, Deluge, Transmission |
| Virtualization | 3 | VirtualBox, VMware Workstation Player, QEMU |
| Java | 5 | OpenJDK, Eclipse Temurin, Amazon Corretto, Zulu JDK, Oracle JDK |
| Security | 10 | Nmap, Zenmap, Angry IP Scanner, Metasploit, Burp Suite, SQLMap, Hydra, John, Aircrack-ng, Hashcat |
| Note Taking | 4 | Obsidian, Joplin, Logseq, CherryTree |
| Password Managers | 3 | Bitwarden, KeePassXC, 1Password |
| Terminal Emulators | 4 | Alacritty, kitty, WezTerm, Tilix |
| VPN | 4 | ProtonVPN, WireGuard, Mullvad VPN, OpenVPN |
| Video Editors | 3 | Kdenlive, Shotcut, OpenShot |

---

## ⚡ Quick-Start Profiles

| Profile | Icon | Apps | System Tweaks |
|---------|------|-----:|--------------|
| Developer | 💻 | 12 | Enable Docker daemon, add docker group, git rebase default, Flathub remote |
| Student | 🎓 | 11 | Set git default branch to `main` |
| Gamer | 🎮 | 9 | Enable Steam multilib (Arch), Flathub remote, gamemode hint |
| Content Creator | 🎬 | 10 | Load v4l2loopback for OBS virtual camera, realtime audio group |
| Daily User | 🏠 | 11 | Set Firefox as default browser, Thunderbird as default email client |
| Security / Pentester | 🔐 | 12 | Add user to wireshark group, msfdb init, monitor-mode advisory |

> Custom profiles are saved to `~/.config/linite/profiles/*.toml` and persist across sessions. Legacy `.yaml` profiles are auto-migrated to TOML on first load.

---

## 🚀 Getting Started

### Install dependencies

```bash
# No required third-party packages — Linite uses Python 3.11+ stdlib only.
# tkinter is bundled with Python on most distros, but may need:
sudo apt install python3-tk       # Debian / Ubuntu / Mint
sudo dnf install python3-tkinter  # Fedora / RHEL
sudo pacman -S tk                 # Arch / Manjaro
sudo zypper install python3-tk    # openSUSE
```

### Launch the GUI

```bash
python main.py
```

### CLI — install apps directly

```bash
python main.py --cli install vlc git docker discord
```

### CLI — update the whole system

```bash
python main.py --cli update
```

### List all available apps

```bash
python main.py --list
```

### Export a reproducible bash script

```bash
python main.py --export mysetup.sh                                         # full catalog
python main.py --export mysetup.sh --pm apt --cli install vlc git discord  # filtered
bash mysetup.sh                                                            # run on target machine
```

### Verbose / debug output

```bash
python main.py --verbose
```

---

## 🗂️ Data Files

| File / Location | Format | Purpose |
|-----------------|--------|---------|
| `data/catalog/<category>.toml` | TOML | App definitions (92 apps across 17 categories) |
| `data/package_maps/<pm>.toml` | TOML | Authoritative per-PM package names & install commands |
| `data/profiles/<id>.toml` | TOML | Built-in Quick-Start profiles with system tweaks |
| `~/.config/linite/history.yaml` | YAML | Install / uninstall event log |
| `~/.config/linite/profiles/*.toml` | TOML | User-saved custom profiles |

> Legacy `.yaml` profile files are auto-migrated to TOML on first load. Legacy `history.json` files from older versions are auto-migrated to YAML.

---

## 🧠 Intelligence Engine — Example Suggestions

| Situation | Suggestion |
|-----------|------------|
| RAM < 2 GB + Blender selected | Replace Blender → Inkscape; replace VLC → MPV |
| NVIDIA GPU, nouveau driver | Install proprietary nvidia-driver for full performance |
| Ubuntu 22.04, VS Code selected | Older repo version — prefer Flatpak for latest release |
| Running inside Docker | ⛔ GUI apps cannot launch without a display server |
| ARM64 CPU, Steam selected | Steam has no native ARM64 package |
| Discord selected | Proprietary app — consider open-source alternatives |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| GUI toolkit | Tkinter (stdlib) |
| Catalog & config | TOML (`tomllib`, stdlib) — catalog, package maps, profiles |
| History | PyYAML — install/uninstall event log |
| Threading | `threading` + `concurrent.futures.ThreadPoolExecutor` |
| Package managers | apt · dnf · yum · pacman · zypper · flatpak · snap |
| Algorithms | Kahn's topological sort for dependency ordering |

---

## 📋 Requirements

- **Python 3.11+** — uses `tomllib` from the standard library
- **tkinter** — see distro-specific install above (GUI mode only)
- **PyYAML** (optional) — `pip install pyyaml` — only needed for legacy YAML history files

No required third-party packages.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.


[Linite](https://srijan-xi.github.io/Linite/) © 2026 Srijan Kumar | Srijan-XI · [GitHub](https://github.com/Srijan-XI/Linite) · [Changelog](https://srijan-xi.github.io/Linite/changelog) · [Contributing](https://srijan-xi.github.io/Linite/contributing) · [Git Clone](https://github.com/Srijan-XI/Linite.git)
