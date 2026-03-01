# Linite 🐧

**Linite** is the Linux equivalent of [Ninite](https://ninite.com/) — select the apps you want, click **Install**, and Linite fetches and silently installs them all at once using the right package manager for your distro.

---

## Features

- 🖥 **Auto-detects your distro** — Ubuntu, Fedora, Arch, openSUSE, and more
- 📦 **Native package managers** — `apt`, `dnf`, `yum`, `pacman`, `zypper`
- 🌐 **Universal fallbacks** — `flatpak` and `snap` when no native package exists
- 🔄 **One-click system update** — upgrade all packages across all package managers
- 🎨 **Dark-mode Tkinter GUI** — categorised, searchable software catalog
- ⌨️  **CLI mode** — headless installs for scripts and servers
- 69 curated apps across 12 categories

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| GUI | Tkinter (stdlib) |
| Package mgmt | apt / dnf / pacman / zypper / snap / flatpak |
| Threading | `threading` (non-blocking UI during install) |

---

## Project Structure

```
linite/
├── main.py                   # Entry point (GUI + CLI)
├── requirements.txt
├── core/
│   ├── distro.py             # Linux distro detection
│   ├── package_manager.py    # PM abstraction (apt, dnf, pacman …)
│   ├── installer.py          # Orchestrates app installation
│   └── updater.py            # System-wide update logic
├── data/
│   └── software_catalog.py   # All app definitions & install specs
├── gui/
│   ├── app.py                # Main Tkinter window
│   ├── styles.py             # Dark-mode colour palette & fonts
│   └── components/
│       ├── category_panel.py # Left sidebar
│       ├── software_panel.py # Scrollable app grid
│       └── progress_panel.py # Progress bar + live log
└── utils/
    └── helpers.py            # Logging, root-check, path helpers
```

---

## Software Categories

| Category | Apps (count) | Notable Entries |
|----------|--------------|-----------------|
| Web Browsers | 7 | Firefox, Chromium, Brave, Chrome, Opera, Tor Browser, Vivaldi |
| Development | 8 | VS Code, Git, Python 3, Node.js, Docker, Vim, Neovim, GitHub CLI |
| Media | 6 | VLC, Spotify, mpv, OBS Studio, Audacity, HandBrake |
| Communication | 5 | Discord, Telegram, Slack, Zoom, Dropbox |
| Utilities | 10 | htop, curl, wget, 7-Zip, Timeshift, Flatpak, Neofetch, Flameshot, Wireshark, Notepad++ |
| Office | 6 | LibreOffice, Thunderbird, Okular, Evince, OpenOffice, Foxit PDF Reader |
| Gaming | 2 | Steam, Lutris |
| Graphics | 3 | GIMP, Inkscape, Blender |
| Torrents | 4 | qBittorrent, qBittorrent-nox, Deluge, Transmission |
| Virtualization | 3 | VirtualBox, VMware Workstation Player, QEMU |
| Java | 5 | OpenJDK, Eclipse Temurin, Amazon Corretto, Zulu JDK, Oracle JDK |
| Security | 10 | Nmap, Metasploit, Burp Suite, SQLMap, Hydra, John the Ripper, Aircrack-ng, Hashcat |

---

## Usage

### GUI (default)

```bash
python main.py
```

### CLI — install apps

```bash
python main.py --cli install vlc git nodejs discord
```

### CLI — update system

```bash
python main.py --cli update
```

### List available apps

```bash
python main.py --list
```

### Verbose / debug output

```bash
python main.py --verbose
```

---

## How It Works

1. **Detect distro** — reads `/etc/os-release` to identify the distro family, version, and architecture.
2. **Select package manager** — maps the distro to `apt`, `dnf`, `pacman`, etc.
3. **Resolve install spec** — every app in the catalog has per-PM install specs (package names, pre/post commands, Flatpak IDs, Snap names).
4. **Install silently** — runs the PM with non-interactive flags (`-y`, `--noconfirm`, `DEBIAN_FRONTEND=noninteractive`) using `sudo`.
5. **Stream output** — live log lines appear in the GUI progress panel during installation.

---

## Requirements

- Python 3.10+
- `tkinter` (usually needs a system package):

```bash
# Debian / Ubuntu / Mint
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch / Manjaro
sudo pacman -S tk

# openSUSE
sudo zypper install python3-tk
```

No third-party Python packages are required.
