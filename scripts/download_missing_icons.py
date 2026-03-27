#!/usr/bin/env python3
"""
Linite — Missing Icon Downloader
=================================
Checks every app ID in the catalog against the assets/ directory and
downloads missing SVG icons from Simple Icons (https://simpleicons.org)
or Iconify (https://iconify.design) where available.

Run from the project root:
    python scripts/download_missing_icons.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
import urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog"
ASSETS  = ROOT / "assets"

# ── Simple Icons slug overrides ────────────────────────────────────────────────
# Map Linite app-id → Simple Icons slug (https://simpleicons.org/?q=<slug>)
SI_SLUGS: dict[str, str] = {
    # Browsers
    "firefox":           "firefox",
    "chromium":          "googlechrome",
    "brave":             "brave",
    "epiphany":          "gnome",
    "microsoft-edge":    "microsoftedge",
    "librewolf":         "librewolf",
    "tor-browser":       "torbrowser",
    "waterfox":          "waterfox",
    "falkon":            "kde",
    "vivaldi":           "vivaldi",
    "opera":             "opera",
    "mullvad-browser":   "mullvad",
    "floorp":            "firefox",
    # Communication
    "discord":           "discord",
    "signal-desktop":    "signal",
    "telegram":          "telegram",
    "thunderbird":       "thunderbird",
    "element":           "element",
    "slack":             "slack",
    "zoom":              "zoom",
    "teams":             "microsoftteams",
    "skype":             "skype",
    "mumble":            "mumble",
    "hexchat":           "hexchat",
    "weechat":           "weechat",
    "revolt":            "revolt",
    # Development
    "vscode":            "visualstudiocode",
    "vscodium":          "vscodium",
    "neovim":            "neovim",
    "git":               "git",
    "github-desktop":    "github",
    "gitkraken":         "gitkraken",
    "docker":            "docker",
    "python":            "python",
    "nodejs":            "nodedotjs",
    "openjdk":           "openjdk",
    "openjdk-21":        "openjdk",
    "openjdk-17":        "openjdk",
    "openjdk-11":        "openjdk",
    "openjdk-8":         "openjdk",
    "rust":              "rust",
    "golang":            "go",
    "postman":           "postman",
    "insomnia":          "insomnia",
    "dbeaver":           "dbeaver",
    "arduino":           "arduino",
    "sublime-text":      "sublimetext",
    "atom":              "atom",
    "jetbrains-toolbox": "jetbrains",
    "android-studio":    "androidstudio",
    "intellij-idea":     "intellijidea",
    "pycharm":           "pycharm",
    "clion":             "clion",
    "webstorm":          "webstorm",
    "vim":               "vim",
    "emacs":             "gnuemacs",
    "heroku":            "heroku",
    "kubectl":           "kubernetes",
    "minikube":          "kubernetes",
    "helm":              "helm",
    # Security
    "burpsuite":         "burpsuite",
    "wireshark":         "wireshark",
    "protonvpn":         "protonvpn",
    "wireguard":         "wireguard",
    "mullvad":           "mullvad",
    "tailscale":         "tailscale",
    "openvpn":           "openvpn",
    # Utilities
    "virtualbox":        "virtualbox",
    "vmware":            "vmware",
    "qemu-kvm":          "qemu",
    "flameshot":         "flameshot",
    "obsidian":          "obsidian",
    "notion":            "notion",
    "libreoffice":       "libreoffice",
    "calibre":           "calibre",
    # Media
    "vlc":               "vlc",
    "obs":               "obsstudio",
    "audacity":          "audacity",
    "krita":             "krita",
    "inkscape":          "inkscape",
    "blender":           "blender",
    "gimp":              "gimp",
    "ffmpeg":            "ffmpeg",
    "spotify":           "spotify",
    "steam":             "steam",
    "kdenlive":          "kdenlive",
    "shotcut":           "shotcut",
    "openshot":          "openshot",
    "davinci-resolve":   "davinciresolve",
}

# ── Iconify fallbacks (for apps not on Simple Icons) ──────────────────────────
ICONIFY_ICONS: dict[str, tuple[str, str]] = {
    # (collection, icon_name) — browse at https://icon-sets.iconify.design/
    "nmap":       ("mdi", "radar"),
    "htop":       ("mdi", "monitor-dashboard"),
    "curl":       ("mdi", "web"),
    "wget":       ("mdi", "download"),
    "7zip":       ("mdi", "zip-box"),
    "rsync":      ("mdi", "sync"),
    "tmux":       ("mdi", "console"),
    "zsh":        ("mdi", "console"),
    "fish":       ("mdi", "console"),
    "bash":       ("mdi", "bash"),
    "ufw":        ("mdi", "firewall"),
    "gufw":       ("mdi", "firewall"),
    "fail2ban":   ("mdi", "shield-lock"),
    "clamav":     ("mdi", "shield-check"),
    "nikto":      ("mdi", "security-network"),
    "gobuster":   ("mdi", "magnify"),
    "lynis":      ("mdi", "security"),
    "opensnitch": ("mdi", "eye"),
    "dnscrypt-proxy": ("mdi", "dns"),
    "hashcat":    ("mdi", "key"),
    "john":       ("mdi", "lock-open"),
    "hydra":      ("mdi", "lock"),
    "aircrack-ng":("mdi", "wifi"),
    "sqlmap":     ("mdi", "database"),
    "metasploit": ("mdi", "sword"),
    "angryip":    ("mdi", "ip-network"),
    "zenmap":     ("mdi", "map"),
    "tlp":        ("mdi", "battery-charging"),
    "stacer":     ("mdi", "speedometer"),
    "bashtop":    ("mdi", "monitor"),
    "btop":       ("mdi", "monitor"),
    "bpytop":     ("mdi", "monitor"),
    "gparted":    ("mdi", "harddisk"),
    "timeshift":  ("mdi", "backup-restore"),
    "syncthing":  ("mdi", "sync"),
    "nextcloud":  ("simple-icons", "nextcloud"),
    "cryptomator":("mdi", "lock"),
    "keepassxc":  ("simple-icons", "keepassxc"),
    "bitwarden":  ("simple-icons", "bitwarden"),
    "gnome-keyring": ("mdi", "key-chain"),
    "pass":       ("mdi", "key"),
    "ansible":    ("simple-icons", "ansible"),
    "terraform":  ("simple-icons", "terraform"),
    "vagrant":    ("simple-icons", "vagrant"),
    "packer":     ("simple-icons", "hashicorp"),
    "nginx":      ("simple-icons", "nginx"),
    "apache":     ("simple-icons", "apache"),
    "postgresql": ("simple-icons", "postgresql"),
    "mysql":      ("simple-icons", "mysql"),
    "mariadb":    ("simple-icons", "mariadb"),
    "redis":      ("simple-icons", "redis"),
    "mongodb":    ("simple-icons", "mongodb"),
    "elasticsearch":("simple-icons", "elasticsearch"),
    "kubectl":    ("simple-icons", "kubernetes"),
    "minikube":   ("simple-icons", "kubernetes"),
    "flatpak":    ("simple-icons", "flatpak"),
    "snap":       ("simple-icons", "snapcraft"),
    "kate":       ("mdi", "pencil"),
    "gedit":      ("mdi", "pencil"),
    "mousepad":   ("mdi", "pencil"),
    "featherpad": ("mdi", "pencil"),
    "pluma":      ("mdi", "pencil"),
    "geany":      ("mdi", "pencil-box"),
    # Communication apps not in SI
    "slack":      ("simple-icons", "slack"),
    "mattermost-desktop": ("simple-icons", "mattermost"),
    # Media apps with Iconify fallbacks
    "vlc":        ("simple-icons", "vlc"),
    "mpv":        ("mdi", "play-circle"),
    "handbrake":  ("simple-icons", "handbrake"),
    "kooha":      ("mdi", "record-circle"),
    "pitivi":     ("mdi", "film"),
    "lmms":       ("simple-icons", "lmms"),
    "ardour":     ("mdi", "music"),
    "rhythmbox":  ("mdi", "music"),
    "strawberry": ("mdi", "music"),
    "mixxx":      ("mdi", "mixing-board"),
    "easyeffects":("mdi", "equalizer"),
    # Productivity
    "joplin":     ("simple-icons", "joplin"),
    "logseq":     ("simple-icons", "logseq"),
    "cherrytree": ("mdi", "tree"),
    "okular":     ("mdi", "book-open"),
    "evince":     ("mdi", "file-pdf-box"),
    "zathura":    ("mdi", "file-document"),
    "xournalpp":  ("mdi", "pencil"),
    "openoffice": ("simple-icons", "apacheopenoffice"),
    "onlyoffice": ("simple-icons", "onlyoffice"),
    "foxitreader": ("mdi", "file-pdf-box"),
    # Gaming
    "lutris":     ("simple-icons", "lutris"),
    "heroic":     ("mdi", "controller-classic"),
    "bottles":    ("mdi", "bottle-wine"),
    "gamemode":   ("mdi", "controller"),
    "mangohud":   ("mdi", "monitor-dashboard"),
    "protonup-qt":("mdi", "steam"),
    # Terminals
    "alacritty":  ("simple-icons", "alacritty"),
    "kitty":      ("mdi", "cat"),
    "wezterm":    ("mdi", "console"),
    "tilix":      ("mdi", "console"),
    # File sharing
    "qbittorrent":("simple-icons", "qbittorrent"),
    "qbittorrent-nox": ("simple-icons", "qbittorrent"),
    "deluge":     ("simple-icons", "deluge"),
    "transmission":("simple-icons", "transmission"),
    # Misc
    "dropbox":    ("simple-icons", "dropbox"),
    "remmina":    ("mdi", "remote-desktop"),
    "rustdesk":   ("mdi", "remote-desktop"),
    "anydesk":    ("simple-icons", "anydesk"),
    "nextcloud-desktop": ("simple-icons", "nextcloud"),
    "rclone":     ("mdi", "cloud-sync"),
    "insync":     ("mdi", "google-drive"),
    "darktable":  ("simple-icons", "darktable"),
    "rawtherapee":("mdi", "camera"),
    "neofetch":   ("mdi", "information"),
    "lazygit":    ("simple-icons", "git"),
    "podman":     ("simple-icons", "podman"),
    "kind":       ("simple-icons", "kubernetes"),
    "k9s":        ("simple-icons", "kubernetes"),
    "notepadplusplus": ("simple-icons", "notepadplusplus"),
    "gedit":      ("mdi", "pencil"),
    # Java variants
    "eclipse-temurin": ("simple-icons", "eclipse"),
    "amazon-corretto": ("simple-icons", "amazon"),
    "zulu-jdk":   ("mdi", "coffee"),
    "oracle-jdk": ("simple-icons", "oracle"),
    "python3":    ("simple-icons", "python"),
    "gh":         ("simple-icons", "github"),
    # More media/video
    "vlc":                ("simple-icons", "vlc"),
    "handbrake":          ("simple-icons", "handbrake"),
    "mixxx":              ("simple-icons", "mixxx"),
    "darktable":          ("simple-icons", "darktable"),
    # Productivity / privacy
    "1password":          ("simple-icons", "1password"),
    # System tools
    "glances":            ("mdi", "monitor-eye"),
    "mission-center":     ("mdi", "monitor-dashboard"),
    "nautilus":           ("mdi", "folder"),
    "thunar":             ("mdi", "folder"),
    "nemo":               ("mdi", "folder"),
    "dolphin":            ("mdi", "folder"),
    # CLI utilities
    "ripgrep":            ("mdi", "text-search"),
    "fd":                 ("mdi", "file-search"),
    "bat":                ("mdi", "bat"),
    "fzf":                ("mdi", "magnify"),
    "jq":                 ("mdi", "code-json"),
    "yq":                 ("mdi", "code-json"),
    "eclipse-temurin":    ("simple-icons", "eclipse"),
}

ICONIFY_BASE = "https://api.iconify.design/{collection}/{icon}.svg?color=%23ffffff&width=64&height=64"
SI_BASE      = "https://cdn.simpleicons.org/{slug}/white"


def _collect_catalog_ids() -> list[str]:
    """Return all unique app IDs from all TOML catalog files."""
    ids: list[str] = []
    for toml_path in sorted(CATALOG.glob("*.toml")):
        data = tomllib.loads(toml_path.read_bytes().decode())
        for app in data.get("apps", []):
            ids.append(app["id"])
    return ids


def _asset_exists(app_id: str) -> bool:
    """Return True if any SVG exists for this app_id in assets/."""
    from gui.icon_loader import get_svg_path_for_app  # local import, add project root to path
    return bool(get_svg_path_for_app(app_id))


def _download(url: str, dest: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY-RUN] would download -> {dest.relative_to(ROOT)}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Linite/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        if len(data) < 50:   # empty / error SVG
            return False
        dest.write_bytes(data)
        print(f"  ✓  {dest.relative_to(ROOT)}")
        return True
    except Exception as exc:
        print(f"  ✗  {url}: {exc}")
        return False


def main(dry_run: bool = False) -> None:
    sys.path.insert(0, str(ROOT))   # make gui.icon_loader importable

    ids = _collect_catalog_ids()
    print(f"Catalog has {len(ids)} apps")

    missing = [aid for aid in ids if not _asset_exists(aid)]
    print(f"Missing icons: {len(missing)}\n")

    downloaded = skipped = 0
    for aid in missing:
        print(f"[{aid}]")

        # Try Simple Icons
        if aid in SI_SLUGS:
            slug = SI_SLUGS[aid]
            url  = SI_BASE.format(slug=slug)
            dest = ASSETS / aid / f"{aid}-auto.svg"
            if _download(url, dest, dry_run):
                downloaded += 1
                continue

        # Try Iconify
        if aid in ICONIFY_ICONS:
            collection, icon = ICONIFY_ICONS[aid]
            url  = ICONIFY_BASE.format(collection=collection, icon=icon)
            dest = ASSETS / aid / f"{aid}-auto.svg"
            if _download(url, dest, dry_run):
                downloaded += 1
                continue

        print(f"  — no source configured, keeping emoji")
        skipped += 1

    print(f"\nDone — downloaded: {downloaded}, no source: {skipped}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Download missing Linite app icons")
    ap.add_argument("--dry-run", action="store_true", help="Print what would be downloaded")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
