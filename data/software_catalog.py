"""
Linite - Software Catalog
Defines all installable apps, their packages per distro family, and metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PackageSpec:
    """
    Describes how to install a single application via a specific package manager.

    apt / dnf / pacman / zypper  → list of package names
    snap                         → snap name  (+ classic flag)
    flatpak                      → Flatpak app-id  (+ remote, usually 'flathub')
    script                       → URL of a shell script to download & run
    """
    packages: List[str] = field(default_factory=list)
    snap_classic: bool = False          # used when pm == "snap"
    flatpak_remote: str = "flathub"     # used when pm == "flatpak"
    script_url: str = ""                # used when pm == "script"
    sha256: str = ""                    # expected SHA-256 of downloaded file (script / deb)
    pre_commands: List[str] = field(default_factory=list)   # run before install
    post_commands: List[str] = field(default_factory=list)  # run after install


@dataclass
class SoftwareEntry:
    id: str                         # unique slug
    name: str                       # display name
    description: str
    category: str
    icon: str = "📦"               # emoji fallback icon
    website: str = ""

    # Keyed by package-manager name.
    # Special key "universal" falls back when a specific PM has no entry.
    install_specs: Dict[str, PackageSpec] = field(default_factory=dict)

    # Optional: preferred install method  (apt | dnf | … | snap | flatpak | script)
    # If None, the distro's native PM is tried first, then flatpak, then snap.
    preferred_pm: Optional[str] = None

    def get_spec(self, pm_name: str) -> Optional[PackageSpec]:
        return self.install_specs.get(pm_name) or self.install_specs.get("universal")


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def _s(packages, **kw) -> PackageSpec:
    """Shortcut to create a PackageSpec."""
    return PackageSpec(packages=packages if isinstance(packages, list) else [packages], **kw)


CATALOG: List[SoftwareEntry] = [

    # ── Web Browsers ──────────────────────────────────────────────────────
    SoftwareEntry(
        id="firefox",
        name="Firefox",
        description="Fast, private and free web browser by Mozilla.",
        category="Web Browsers",
        icon="🦊",
        website="https://www.mozilla.org/firefox",
        install_specs={
            "apt":    _s("firefox"),
            "dnf":    _s("firefox"),
            "pacman": _s("firefox"),
            "zypper": _s("MozillaFirefox"),
        },
    ),
    SoftwareEntry(
        id="chromium",
        name="Chromium",
        description="Open-source browser project that powers Chrome.",
        category="Web Browsers",
        icon="🔵",
        website="https://www.chromium.org",
        install_specs={
            "apt":    _s("chromium-browser"),
            "dnf":    _s("chromium"),
            "pacman": _s("chromium"),
            "zypper": _s("chromium"),
            "snap":   _s("chromium"),
            "flatpak": _s("org.chromium.Chromium"),
        },
    ),
    SoftwareEntry(
        id="brave",
        name="Brave Browser",
        description="Privacy-focused browser with ad-blocking built in.",
        category="Web Browsers",
        icon="🦁",
        website="https://brave.com",
        install_specs={
            "snap":    _s("brave", snap_classic=False),
            "flatpak": _s("com.brave.Browser"),
            "script":  PackageSpec(
                script_url="https://brave.com/linux/#release-channel-installation"
            ),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="google-chrome",
        name="Google Chrome",
        description="Google's popular web browser.",
        category="Web Browsers",
        icon="🌐",
        website="https://www.google.com/chrome",
        install_specs={
            "script": PackageSpec(
                script_url="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
            ),
            "flatpak": _s("com.google.Chrome"),
        },
        preferred_pm="flatpak",
    ),

    # ── Development Tools ─────────────────────────────────────────────────
    SoftwareEntry(
        id="vscode",
        name="Visual Studio Code",
        description="Lightweight but powerful source-code editor by Microsoft.",
        category="Development",
        icon="💻",
        website="https://code.visualstudio.com",
        install_specs={
            "snap":    _s("code", snap_classic=True),
            "flatpak": _s("com.visualstudio.code"),
            "apt": PackageSpec(
                packages=["code"],
                pre_commands=[
                    "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /tmp/packages.microsoft.gpg",
                    "install -o root -g root -m 644 /tmp/packages.microsoft.gpg /etc/apt/trusted.gpg.d/",
                    'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] '
                    'https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list',
                    "apt-get update",
                ],
            ),
        },
        preferred_pm="snap",
    ),
    SoftwareEntry(
        id="git",
        name="Git",
        description="Distributed version control system.",
        category="Development",
        icon="🔧",
        website="https://git-scm.com",
        install_specs={
            "apt":    _s("git"),
            "dnf":    _s("git"),
            "pacman": _s("git"),
            "zypper": _s("git"),
        },
    ),
    SoftwareEntry(
        id="python3",
        name="Python 3",
        description="High-level, versatile programming language.",
        category="Development",
        icon="🐍",
        website="https://www.python.org",
        install_specs={
            "apt":    _s(["python3", "python3-pip", "python3-venv"]),
            "dnf":    _s(["python3", "python3-pip"]),
            "pacman": _s(["python", "python-pip"]),
            "zypper": _s(["python3", "python3-pip"]),
        },
    ),
    SoftwareEntry(
        id="nodejs",
        name="Node.js",
        description="JavaScript runtime built on Chrome's V8 engine.",
        category="Development",
        icon="🟩",
        website="https://nodejs.org",
        install_specs={
            "apt":    _s(["nodejs", "npm"]),
            "dnf":    _s(["nodejs", "npm"]),
            "pacman": _s(["nodejs", "npm"]),
            "zypper": _s(["nodejs", "npm"]),
            "snap":   _s("node", snap_classic=True),
        },
    ),
    SoftwareEntry(
        id="docker",
        name="Docker",
        description="Platform for containerized applications.",
        category="Development",
        icon="🐳",
        website="https://www.docker.com",
        install_specs={
            "apt": PackageSpec(
                packages=["docker-ce", "docker-ce-cli", "containerd.io"],
                pre_commands=[
                    "apt-get install -y ca-certificates curl gnupg",
                    "install -m 0755 -d /etc/apt/keyrings",
                    "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
                    "chmod a+r /etc/apt/keyrings/docker.gpg",
                    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
                    'https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" '
                    '| tee /etc/apt/sources.list.d/docker.list > /dev/null',
                    "apt-get update",
                ],
                post_commands=["systemctl enable --now docker"],
            ),
            "dnf": PackageSpec(
                packages=["docker-ce", "docker-ce-cli", "containerd.io"],
                pre_commands=[
                    "dnf -y install dnf-plugins-core",
                    "dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo",
                ],
                post_commands=["systemctl enable --now docker"],
            ),
            "pacman": PackageSpec(
                packages=["docker"],
                post_commands=["systemctl enable --now docker"],
            ),
        },
    ),
    SoftwareEntry(
        id="vim",
        name="Vim",
        description="Highly configurable terminal text editor.",
        category="Development",
        icon="📝",
        website="https://www.vim.org",
        install_specs={
            "apt":    _s("vim"),
            "dnf":    _s("vim-enhanced"),
            "pacman": _s("vim"),
            "zypper": _s("vim"),
        },
    ),
    SoftwareEntry(
        id="neovim",
        name="Neovim",
        description="Hyperextensible Vim-based text editor.",
        category="Development",
        icon="📝",
        website="https://neovim.io",
        install_specs={
            "apt":    _s("neovim"),
            "dnf":    _s("neovim"),
            "pacman": _s("neovim"),
            "zypper": _s("neovim"),
            "snap":   _s("nvim", snap_classic=True),
            "flatpak": _s("io.neovim.nvim"),
        },
    ),
    SoftwareEntry(
        id="gh",
        name="GitHub CLI",
        description="Official GitHub command-line tool.",
        category="Development",
        icon="🐙",
        website="https://cli.github.com",
        install_specs={
            "apt": PackageSpec(
                packages=["gh"],
                pre_commands=[
                    "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
                    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] '
                    'https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null',
                    "apt update",
                ],
            ),
            "dnf":    _s("gh"),
            "pacman": _s("github-cli"),
        },
    ),

    # ── Media ─────────────────────────────────────────────────────────────
    SoftwareEntry(
        id="vlc",
        name="VLC Media Player",
        description="Free and open-source cross-platform multimedia player.",
        category="Media",
        icon="🎬",
        website="https://www.videolan.org/vlc/",
        install_specs={
            "apt":    _s("vlc"),
            "dnf":    _s("vlc"),
            "pacman": _s("vlc"),
            "zypper": _s("vlc"),
            "snap":   _s("vlc"),
            "flatpak": _s("org.videolan.VLC"),
        },
    ),
    SoftwareEntry(
        id="spotify",
        name="Spotify",
        description="Music streaming service.",
        category="Media",
        icon="🎵",
        website="https://www.spotify.com",
        install_specs={
            "snap":    _s("spotify"),
            "flatpak": _s("com.spotify.Client"),
        },
        preferred_pm="snap",
    ),
    SoftwareEntry(
        id="mpv",
        name="mpv",
        description="Free, open-source and cross-platform media player.",
        category="Media",
        icon="▶️",
        website="https://mpv.io",
        install_specs={
            "apt":    _s("mpv"),
            "dnf":    _s("mpv"),
            "pacman": _s("mpv"),
            "zypper": _s("mpv"),
            "flatpak": _s("io.mpv.Mpv"),
        },
    ),
    SoftwareEntry(
        id="obs",
        name="OBS Studio",
        description="Free and open source software for video recording and live streaming.",
        category="Media",
        icon="🎙️",
        website="https://obsproject.com",
        install_specs={
            "apt":    _s("obs-studio"),
            "dnf":    _s("obs-studio"),
            "pacman": _s("obs-studio"),
            "zypper": _s("obs-studio"),
            "flatpak": _s("com.obsproject.Studio"),
        },
    ),

    # ── Communication ─────────────────────────────────────────────────────
    SoftwareEntry(
        id="discord",
        name="Discord",
        description="Voice, video and text communication platform.",
        category="Communication",
        icon="💬",
        website="https://discord.com",
        install_specs={
            "snap":    _s("discord"),
            "flatpak": _s("com.discordapp.Discord"),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="telegram",
        name="Telegram",
        description="Fast and secure messaging app.",
        category="Communication",
        icon="✈️",
        website="https://telegram.org",
        install_specs={
            "snap":    _s("telegram-desktop"),
            "flatpak": _s("org.telegram.desktop"),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="slack",
        name="Slack",
        description="Business messaging platform.",
        category="Communication",
        icon="💼",
        website="https://slack.com",
        install_specs={
            "snap":    _s("slack", snap_classic=True),
            "flatpak": _s("com.slack.Slack"),
        },
        preferred_pm="snap",
    ),
    SoftwareEntry(
        id="zoom",
        name="Zoom",
        description="Video conferencing and meetings platform.",
        category="Communication",
        icon="📹",
        website="https://zoom.us",
        install_specs={
            "snap":    _s("zoom-client"),
            "flatpak": _s("us.zoom.Zoom"),
        },
        preferred_pm="flatpak",
    ),

    # ── Utilities ─────────────────────────────────────────────────────────
    SoftwareEntry(
        id="htop",
        name="htop",
        description="Interactive process viewer for Unix.",
        category="Utilities",
        icon="📊",
        website="https://htop.dev",
        install_specs={
            "apt":    _s("htop"),
            "dnf":    _s("htop"),
            "pacman": _s("htop"),
            "zypper": _s("htop"),
        },
    ),
    SoftwareEntry(
        id="curl",
        name="curl",
        description="Transfer data from or to a server.",
        category="Utilities",
        icon="🌀",
        website="https://curl.se",
        install_specs={
            "apt":    _s("curl"),
            "dnf":    _s("curl"),
            "pacman": _s("curl"),
            "zypper": _s("curl"),
        },
    ),
    SoftwareEntry(
        id="wget",
        name="wget",
        description="Non-interactive network downloader.",
        category="Utilities",
        install_specs={
            "apt":    _s("wget"),
            "dnf":    _s("wget"),
            "pacman": _s("wget"),
            "zypper": _s("wget"),
        },
    ),
    SoftwareEntry(
        id="7zip",
        name="7-Zip",
        description="File archiver with a high compression ratio.",
        category="Utilities",
        icon="📦",
        website="https://www.7-zip.org",
        install_specs={
            "apt":    _s("p7zip-full"),
            "dnf":    _s("p7zip"),
            "pacman": _s("p7zip"),
            "zypper": _s("p7zip"),
        },
    ),
    SoftwareEntry(
        id="timeshift",
        name="Timeshift",
        description="System restore tool for Linux.",
        category="Utilities",
        icon="🕰️",
        website="https://github.com/linuxmint/timeshift",
        install_specs={
            "apt":    _s("timeshift"),
            "dnf":    _s("timeshift"),
            "pacman": _s("timeshift"),  # AUR package
        },
    ),
    SoftwareEntry(
        id="neofetch",
        name="Neofetch",
        description="CLI system information tool.",
        category="Utilities",
        icon="🖥️",
        install_specs={
            "apt":    _s("neofetch"),
            "dnf":    _s("neofetch"),
            "pacman": _s("neofetch"),
            "zypper": _s("neofetch"),
        },
    ),
    SoftwareEntry(
        id="flatpak",
        name="Flatpak",
        description="Universal Linux application sandbox.",
        category="Utilities",
        icon="📦",
        website="https://flatpak.org",
        install_specs={
            "apt":    _s("flatpak"),
            "dnf":    _s("flatpak"),
            "pacman": _s("flatpak"),
            "zypper": _s("flatpak"),
        },
    ),

    # ── Office & Productivity ──────────────────────────────────────────────
    SoftwareEntry(
        id="libreoffice",
        name="LibreOffice",
        description="Free and powerful office suite.",
        category="Office",
        icon="📄",
        website="https://www.libreoffice.org",
        install_specs={
            "apt":    _s("libreoffice"),
            "dnf":    _s("libreoffice"),
            "pacman": _s("libreoffice-fresh"),
            "zypper": _s("libreoffice"),
            "flatpak": _s("org.libreoffice.LibreOffice"),
        },
    ),
    SoftwareEntry(
        id="okular",
        name="Okular",
        description="Universal document viewer.",
        category="Office",
        icon="📖",
        install_specs={
            "apt":    _s("okular"),
            "dnf":    _s("okular"),
            "pacman": _s("okular"),
            "flatpak": _s("org.kde.okular"),
        },
    ),
    SoftwareEntry(
        id="thunderbird",
        name="Thunderbird",
        description="Free email client from Mozilla.",
        category="Office",
        icon="📧",
        website="https://www.thunderbird.net",
        install_specs={
            "apt":    _s("thunderbird"),
            "dnf":    _s("thunderbird"),
            "pacman": _s("thunderbird"),
            "flatpak": _s("org.mozilla.Thunderbird"),
        },
    ),

    # ── Gaming ────────────────────────────────────────────────────────────
    SoftwareEntry(
        id="steam",
        name="Steam",
        description="Valve's gaming platform.",
        category="Gaming",
        icon="🎮",
        website="https://store.steampowered.com",
        install_specs={
            "apt":    _s("steam"),
            "dnf":    _s("steam"),
            "pacman": _s("steam"),
            "flatpak": _s("com.valvesoftware.Steam"),
        },
    ),
    SoftwareEntry(
        id="lutris",
        name="Lutris",
        description="Open gaming platform for Linux.",
        category="Gaming",
        icon="🕹️",
        website="https://lutris.net",
        install_specs={
            "apt":    _s("lutris"),
            "dnf":    _s("lutris"),
            "pacman": _s("lutris"),
            "flatpak": _s("net.lutris.Lutris"),
        },
    ),

    # ── Graphics & Design ─────────────────────────────────────────────────
    SoftwareEntry(
        id="gimp",
        name="GIMP",
        description="GNU Image Manipulation Program.",
        category="Graphics",
        icon="🖼️",
        website="https://www.gimp.org",
        install_specs={
            "apt":    _s("gimp"),
            "dnf":    _s("gimp"),
            "pacman": _s("gimp"),
            "zypper": _s("gimp"),
            "flatpak": _s("org.gimp.GIMP"),
        },
    ),
    SoftwareEntry(
        id="inkscape",
        name="Inkscape",
        description="Professional vector graphics editor.",
        category="Graphics",
        icon="✏️",
        website="https://inkscape.org",
        install_specs={
            "apt":    _s("inkscape"),
            "dnf":    _s("inkscape"),
            "pacman": _s("inkscape"),
            "flatpak": _s("org.inkscape.Inkscape"),
        },
    ),
    SoftwareEntry(
        id="blender",
        name="Blender",
        description="Free and open-source 3D creation suite.",
        category="Graphics",
        icon="🎨",
        website="https://www.blender.org",
        install_specs={
            "apt":    _s("blender"),
            "dnf":    _s("blender"),
            "pacman": _s("blender"),
            "zypper": _s("blender"),
            "snap":   _s("blender"),
            "flatpak": _s("org.blender.Blender"),
        },
    ),

    # ── Web Browsers (additions) ──────────────────────────────────────────
    SoftwareEntry(
        id="opera",
        name="Opera",
        description="Fast and secure browser with built-in VPN and ad blocker.",
        category="Web Browsers",
        icon="🔴",
        website="https://www.opera.com",
        install_specs={
            "apt": PackageSpec(
                packages=["opera-stable"],
                pre_commands=[
                    "curl -fsSL https://deb.opera.com/archive.key | gpg --dearmor | tee /usr/share/keyrings/opera.gpg > /dev/null",
                    'echo "deb [signed-by=/usr/share/keyrings/opera.gpg] https://deb.opera.com/opera-stable/ stable non-free" | tee /etc/apt/sources.list.d/opera.list',
                    "apt-get update",
                ],
            ),
            "dnf": PackageSpec(
                packages=["opera-stable"],
                pre_commands=[
                    "rpm --import https://rpm.opera.com/rpmrepo.key",
                    "tee /etc/yum.repos.d/opera.repo <<'EOF'\n[opera]\nname=Opera packages\ntype=rpm-md\nbaseurl=https://rpm.opera.com/rpm\ngpgcheck=1\ngpgkey=https://rpm.opera.com/rpmrepo.key\nenabled=1\nEOF",
                ],
            ),
            "flatpak": _s("com.opera.Opera"),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="tor-browser",
        name="Tor Browser",
        description="Browse the web anonymously via the Tor network.",
        category="Web Browsers",
        icon="🧅",
        website="https://www.torproject.org",
        install_specs={
            "apt":    _s("torbrowser-launcher"),
            "dnf":    _s("torbrowser-launcher"),
            "pacman": _s("torbrowser-launcher"),
            "flatpak": _s("com.github.micahflee.torbrowser-launcher"),
        },
    ),
    SoftwareEntry(
        id="vivaldi",
        name="Vivaldi",
        description="Feature-rich, highly customisable browser.",
        category="Web Browsers",
        icon="🟠",
        website="https://vivaldi.com",
        install_specs={
            "apt": PackageSpec(
                packages=["vivaldi-stable"],
                pre_commands=[
                    "curl -fsSL https://repo.vivaldi.com/archive/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/vivaldi.gpg > /dev/null",
                    'echo "deb [signed-by=/usr/share/keyrings/vivaldi.gpg arch=$(dpkg --print-architecture)] https://repo.vivaldi.com/archive/deb/ stable main" | tee /etc/apt/sources.list.d/vivaldi.list',
                    "apt-get update",
                ],
            ),
            "flatpak": _s("com.vivaldi.Vivaldi"),
        },
        preferred_pm="flatpak",
    ),

    # ── Torrent Clients ───────────────────────────────────────────────────
    SoftwareEntry(
        id="qbittorrent",
        name="qBittorrent",
        description="Free and open-source BitTorrent client.",
        category="Torrents",
        icon="🌊",
        website="https://www.qbittorrent.org",
        install_specs={
            "apt":    _s("qbittorrent"),
            "dnf":    _s("qbittorrent"),
            "pacman": _s("qbittorrent"),
            "zypper": _s("qbittorrent"),
            "flatpak": _s("org.qbittorrent.qBittorrent"),
        },
    ),
    SoftwareEntry(
        id="qbittorrent-nox",
        name="qBittorrent-nox",
        description="Headless qBittorrent for server/terminal use with Web UI.",
        category="Torrents",
        icon="🌊",
        website="https://www.qbittorrent.org",
        install_specs={
            "apt":    _s("qbittorrent-nox"),
            "dnf":    _s("qbittorrent-nox"),
            "pacman": _s("qbittorrent-nox"),
        },
    ),
    SoftwareEntry(
        id="deluge",
        name="Deluge",
        description="Lightweight, free BitTorrent client.",
        category="Torrents",
        icon="💧",
        website="https://deluge-torrent.org",
        install_specs={
            "apt":    _s("deluge"),
            "dnf":    _s("deluge"),
            "pacman": _s("deluge"),
            "zypper": _s("deluge"),
            "flatpak": _s("org.deluge_torrent.deluge"),
        },
    ),
    SoftwareEntry(
        id="transmission",
        name="Transmission",
        description="Fast, easy and free BitTorrent client.",
        category="Torrents",
        icon="📡",
        website="https://transmissionbt.com",
        install_specs={
            "apt":    _s("transmission"),
            "dnf":    _s("transmission"),
            "pacman": _s("transmission-gtk"),
            "zypper": _s("transmission"),
            "flatpak": _s("com.transmissionbt.Transmission"),
        },
    ),

    # ── Communication (additions) ─────────────────────────────────────────
    SoftwareEntry(
        id="dropbox",
        name="Dropbox",
        description="Cloud storage and file synchronisation service.",
        category="Communication",
        icon="📦",
        website="https://www.dropbox.com",
        install_specs={
            "apt": PackageSpec(
                packages=["dropbox"],
                pre_commands=[
                    "curl -fsSL https://linux.dropbox.com/packages/ubuntu/dropbox_2024.04.17_amd64.deb -o /tmp/dropbox.deb",
                    "apt-get install -y /tmp/dropbox.deb",
                ],
            ),
            "flatpak": _s("com.dropbox.Client"),
        },
        preferred_pm="flatpak",
    ),

    # ── Office (additions) ────────────────────────────────────────────────
    SoftwareEntry(
        id="openoffice",
        name="Apache OpenOffice",
        description="Leading open-source office software suite.",
        category="Office",
        icon="📄",
        website="https://www.openoffice.org",
        install_specs={
            "apt": PackageSpec(
                packages=[],
                pre_commands=[
                    "curl -fsSL https://sourceforge.net/projects/openofficeorg.mirror/files/latest/download -o /tmp/openoffice.tar.gz",
                    "tar -xzf /tmp/openoffice.tar.gz -C /tmp/",
                    "dpkg -i /tmp/en-US/DEBS/*.deb",
                    "dpkg -i /tmp/en-US/DEBS/desktop-integration/*.deb",
                ],
            ),
            "flatpak": _s("org.openoffice.OpenOffice"),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="evince",
        name="Evince",
        description="Simple and clean document viewer (PDF, DJVU, XPS, etc.).",
        category="Office",
        icon="📖",
        website="https://wiki.gnome.org/Apps/Evince",
        install_specs={
            "apt":    _s("evince"),
            "dnf":    _s("evince"),
            "pacman": _s("evince"),
            "zypper": _s("evince"),
            "flatpak": _s("org.gnome.Evince"),
        },
    ),
    SoftwareEntry(
        id="foxitreader",
        name="Foxit PDF Reader",
        description="Fast, lightweight and feature-rich PDF reader.",
        category="Office",
        icon="📕",
        website="https://www.foxit.com/pdf-reader",
        install_specs={
            "flatpak": _s("com.foxit.Reader"),
            "script": PackageSpec(
                script_url="https://www.foxit.com/downloads/latest.html#Foxit-Reader",
            ),
        },
        preferred_pm="flatpak",
    ),

    # ── Media (additions) ─────────────────────────────────────────────────
    SoftwareEntry(
        id="audacity",
        name="Audacity",
        description="Free, open-source, cross-platform audio editor.",
        category="Media",
        icon="🎤",
        website="https://www.audacityteam.org",
        install_specs={
            "apt":    _s("audacity"),
            "dnf":    _s("audacity"),
            "pacman": _s("audacity"),
            "zypper": _s("audacity"),
            "flatpak": _s("org.audacityteam.Audacity"),
        },
    ),
    SoftwareEntry(
        id="handbrake",
        name="HandBrake",
        description="Open-source video transcoder.",
        category="Media",
        icon="🎞️",
        website="https://handbrake.fr",
        install_specs={
            "apt":    _s("handbrake"),
            "dnf":    _s("HandBrake-gui"),
            "pacman": _s("handbrake"),
            "flatpak": _s("fr.handbrake.ghb"),
        },
    ),

    # ── Utilities (additions) ─────────────────────────────────────────────
    SoftwareEntry(
        id="flameshot",
        name="Flameshot",
        description="Powerful yet simple screenshot tool (ShareX equivalent for Linux).",
        category="Utilities",
        icon="🔥",
        website="https://flameshot.org",
        install_specs={
            "apt":    _s("flameshot"),
            "dnf":    _s("flameshot"),
            "pacman": _s("flameshot"),
            "zypper": _s("flameshot"),
            "flatpak": _s("org.flameshot.Flameshot"),
        },
    ),
    SoftwareEntry(
        id="wireshark",
        name="Wireshark",
        description="World's leading network protocol analyser.",
        category="Utilities",
        icon="🦈",
        website="https://www.wireshark.org",
        install_specs={
            "apt":    _s("wireshark"),
            "dnf":    _s("wireshark"),
            "pacman": _s("wireshark-qt"),
            "zypper": _s("wireshark"),
            "flatpak": _s("org.wireshark.Wireshark"),
        },
    ),
    SoftwareEntry(
        id="notepadplusplus",
        name="Notepad++",
        description="Popular source-code editor (via Wine wrapper on Linux).",
        category="Utilities",
        icon="📝",
        website="https://notepad-plus-plus.org",
        install_specs={
            "snap":    _s("notepad-plus-plus"),
            "flatpak": _s("io.github.mmtrt.Notepad_npp"),
        },
        preferred_pm="flatpak",
    ),

    # ── Virtualization ────────────────────────────────────────────────────
    SoftwareEntry(
        id="virtualbox",
        name="VirtualBox",
        description="Free and open-source x86 virtualisation software.",
        category="Virtualization",
        icon="📦",
        website="https://www.virtualbox.org",
        install_specs={
            "apt": PackageSpec(
                packages=["virtualbox"],
                pre_commands=[
                    "curl -fsSL https://www.virtualbox.org/download/oracle_vbox_2016.asc | gpg --dearmor | tee /usr/share/keyrings/virtualbox.gpg > /dev/null",
                    'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/virtualbox.gpg] https://download.virtualbox.org/virtualbox/debian $(. /etc/os-release && echo $VERSION_CODENAME) contrib" | tee /etc/apt/sources.list.d/virtualbox.list',
                    "apt-get update",
                ],
            ),
            "dnf": PackageSpec(
                packages=["VirtualBox"],
                pre_commands=[
                    "dnf config-manager --add-repo https://download.virtualbox.org/virtualbox/rpm/fedora/virtualbox.repo",
                ],
            ),
            "pacman": _s("virtualbox"),
            "flatpak": _s("org.virtualbox.VirtualBox"),
        },
    ),
    SoftwareEntry(
        id="vmware",
        name="VMware Workstation Player",
        description="Free virtualisation platform for running multiple OSes (personal use).",
        category="Virtualization",
        icon="🖥️",
        website="https://www.vmware.com/products/workstation-player.html",
        install_specs={
            "script": PackageSpec(
                script_url="https://www.vmware.com/go/getplayer-linux",
                pre_commands=[
                    "curl -fsSL https://www.vmware.com/go/getplayer-linux -o /tmp/vmware-player.bundle",
                    "chmod +x /tmp/vmware-player.bundle",
                ],
                post_commands=["bash /tmp/vmware-player.bundle --eulas-agreed"],
            ),
        },
    ),
    SoftwareEntry(
        id="qemu",
        name="QEMU",
        description="Generic and open-source machine emulator and virtualiser. Often paired with KVM for near-native performance.",
        category="Virtualization",
        icon="🖥️",
        website="https://www.qemu.org",
        install_specs={
            "apt":    _s(["qemu-system", "qemu-utils", "virt-manager", "libvirt-daemon-system"]),
            "dnf":    _s(["qemu-kvm", "virt-manager", "libvirt", "virt-install"]),
            "pacman": _s(["qemu-full", "virt-manager", "libvirt", "dnsmasq"]),
            "zypper": _s(["qemu", "virt-manager", "libvirt"]),
        },
    ),

    # ── Java Distributions ────────────────────────────────────────────────
    SoftwareEntry(
        id="openjdk",
        name="OpenJDK",
        description="Free and open-source implementation of Java SE.",
        category="Java",
        icon="☕",
        website="https://openjdk.org",
        install_specs={
            "apt":    _s(["default-jdk"]),
            "dnf":    _s(["java-latest-openjdk"]),
            "pacman": _s(["jdk-openjdk"]),
            "zypper": _s(["java-21-openjdk"]),
        },
    ),
    SoftwareEntry(
        id="eclipse-temurin",
        name="Eclipse Temurin (AdoptOpenJDK)",
        description="High-quality, TCK-certified builds of OpenJDK by the Adoptium project.",
        category="Java",
        icon="☕",
        website="https://adoptium.net",
        install_specs={
            "apt": PackageSpec(
                packages=["temurin-21-jdk"],
                pre_commands=[
                    "apt-get install -y wget gnupg",
                    "mkdir -p /etc/apt/keyrings",
                    "wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/apt/keyrings/adoptium.gpg > /dev/null",
                    'echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | tee /etc/apt/sources.list.d/adoptium.list',
                    "apt-get update",
                ],
            ),
            "dnf": PackageSpec(
                packages=["temurin-21-jdk"],
                pre_commands=[
                    "curl -fsSL https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/pki/rpm-gpg/RPM-GPG-KEY-adoptium",
                    'cat > /etc/yum.repos.d/adoptium.repo <<EOF\n[Adoptium]\nname=Adoptium\nbaseurl=https://packages.adoptium.net/artifactory/rpm/$(. /etc/os-release && echo $ID)/$(. /etc/os-release && echo $VERSION_ID)/$(uname -m)\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.adoptium.net/artifactory/api/gpg/key/public\nEOF',
                ],
            ),
            "pacman": _s("jdk21-temurin"),  # from AUR
        },
    ),
    SoftwareEntry(
        id="amazon-corretto",
        name="Amazon Corretto",
        description="No-cost, production-ready distribution of OpenJDK by Amazon.",
        category="Java",
        icon="☕",
        website="https://aws.amazon.com/corretto",
        install_specs={
            "apt": PackageSpec(
                packages=["java-21-amazon-corretto-jdk"],
                pre_commands=[
                    "curl -fsSL https://apt.corretto.aws/corretto.key | gpg --dearmor | tee /usr/share/keyrings/corretto-keyring.gpg > /dev/null",
                    'echo "deb [signed-by=/usr/share/keyrings/corretto-keyring.gpg] https://apt.corretto.aws stable main" | tee /etc/apt/sources.list.d/corretto.list',
                    "apt-get update",
                ],
            ),
            "dnf": PackageSpec(
                packages=["java-21-amazon-corretto-devel"],
                pre_commands=[
                    "curl -fsSL https://yum.corretto.aws/corretto.key | gpg --dearmor | tee /etc/pki/rpm-gpg/RPM-GPG-KEY-corretto",
                    "curl -fsSL -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo",
                ],
            ),
        },
    ),
    SoftwareEntry(
        id="zulu-jdk",
        name="Zulu JDK",
        description="Certified builds of OpenJDK by Azul Systems.",
        category="Java",
        icon="☕",
        website="https://www.azul.com/downloads/",
        install_specs={
            "apt": PackageSpec(
                packages=["zulu21-jdk"],
                pre_commands=[
                    "curl -fsSL https://repos.azul.com/azul-repo.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/azul.gpg > /dev/null",
                    'echo "deb [signed-by=/etc/apt/trusted.gpg.d/azul.gpg] https://repos.azul.com/zulu/deb stable main" | tee /etc/apt/sources.list.d/zulu.list',
                    "apt-get update",
                ],
            ),
            "dnf": PackageSpec(
                packages=["zulu21-jdk"],
                pre_commands=[
                    "curl -fsSL https://repos.azul.com/azul-repo.key | gpg --dearmor | tee /etc/pki/rpm-gpg/RPM-GPG-KEY-azul",
                    "curl -fsSL -o /etc/yum.repos.d/zulu.repo https://repos.azul.com/zulu/deb/azul-repo.conf",
                ],
            ),
            "pacman": _s("zulu21-bin"),  # AUR
        },
    ),
    SoftwareEntry(
        id="oracle-jdk",
        name="Oracle JDK",
        description="Oracle's official JDK — free for personal development use.",
        category="Java",
        icon="☕",
        website="https://www.oracle.com/java/technologies/downloads/",
        install_specs={
            "script": PackageSpec(
                script_url="https://www.oracle.com/java/technologies/downloads/",
                pre_commands=[
                    "echo 'Oracle JDK requires manual download from https://www.oracle.com/java/technologies/downloads/ due to license terms.'",
                ],
            ),
        },
    ),

    # ── Security & Pentesting ─────────────────────────────────────────────
    SoftwareEntry(
        id="nmap",
        name="Nmap",
        description="Free and open-source network scanner used for security auditing.",
        category="Security",
        icon="🔍",
        website="https://nmap.org",
        install_specs={
            "apt":    _s("nmap"),
            "dnf":    _s("nmap"),
            "pacman": _s("nmap"),
            "zypper": _s("nmap"),
            "flatpak": _s("org.nmap.Zenmap"),
        },
    ),
    SoftwareEntry(
        id="zenmap",
        name="Zenmap",
        description="Official graphical front-end for Nmap.",
        category="Security",
        icon="🗺️",
        website="https://nmap.org/zenmap/",
        install_specs={
            "apt":    _s("zenmap"),
            "dnf":    _s("zenmap"),
            "pacman": _s("zenmap"),
            "flatpak": _s("org.nmap.Zenmap"),
        },
    ),
    SoftwareEntry(
        id="angryip",
        name="Angry IP Scanner",
        description="Fast and friendly network scanner for IP addresses and ports.",
        category="Security",
        icon="😡",
        website="https://angryip.org",
        install_specs={
            "apt": PackageSpec(
                packages=["ipscan"],
                pre_commands=[
                    "curl -fsSL https://github.com/angryip/ipscan/releases/latest/download/ipscan_3.9.1_amd64.deb -o /tmp/ipscan.deb",
                    "apt-get install -y /tmp/ipscan.deb",
                ],
            ),
            "flatpak": _s("com.angryip.ipscan"),
            "script": PackageSpec(
                script_url="https://github.com/angryip/ipscan/releases/latest",
            ),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="metasploit",
        name="Metasploit Framework",
        description="World's most widely used penetration testing framework.",
        category="Security",
        icon="💀",
        website="https://www.metasploit.com",
        install_specs={
            "apt": PackageSpec(
                packages=["metasploit-framework"],
                pre_commands=[
                    "curl -fsSL https://apt.metasploit.com/metasploit-framework.list -o /etc/apt/sources.list.d/metasploit-framework.list",
                    "curl -fsSL https://apt.metasploit.com/pubkey.gpg | gpg --dearmor | tee /etc/apt/trusted.gpg.d/metasploit.gpg > /dev/null",
                    "apt-get update",
                ],
                post_commands=["msfdb init"],
            ),
            "script": PackageSpec(
                script_url="https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb",
                pre_commands=[
                    "curl -fsSL https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb -o /tmp/msfinstall",
                    "chmod +x /tmp/msfinstall",
                    "bash /tmp/msfinstall",
                ],
            ),
        },
    ),
    SoftwareEntry(
        id="burpsuite",
        name="Burp Suite Community",
        description="Leading toolkit for web application security testing.",
        category="Security",
        icon="🕷️",
        website="https://portswigger.net/burp",
        install_specs={
            "flatpak": _s("net.portswigger.BurpSuite"),
            "script": PackageSpec(
                script_url="https://portswigger.net/burp/releases/community/latest",
                pre_commands=[
                    "curl -fsSL 'https://portswigger.net/burp/releases/community/latest' -o /tmp/burpsuite_installer.sh",
                    "chmod +x /tmp/burpsuite_installer.sh",
                    "bash /tmp/burpsuite_installer.sh",
                ],
            ),
        },
        preferred_pm="flatpak",
    ),
    SoftwareEntry(
        id="sqlmap",
        name="SQLMap",
        description="Automatic SQL injection and database takeover tool.",
        category="Security",
        icon="💉",
        website="https://sqlmap.org",
        install_specs={
            "apt":    _s("sqlmap"),
            "dnf":    _s("sqlmap"),
            "pacman": _s("sqlmap"),
            "universal": PackageSpec(
                pre_commands=[
                    "git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap",
                    "ln -sf /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap",
                ],
                packages=[],
            ),
        },
    ),
    SoftwareEntry(
        id="hydra",
        name="THC Hydra",
        description="Fast and flexible network login cracker supporting many protocols.",
        category="Security",
        icon="🐉",
        website="https://github.com/vanhauser-thc/thc-hydra",
        install_specs={
            "apt":    _s("hydra"),
            "dnf":    _s("hydra"),
            "pacman": _s("hydra"),
            "zypper": _s("hydra"),
        },
    ),
    SoftwareEntry(
        id="john",
        name="John the Ripper",
        description="Fast password cracker for many hash types.",
        category="Security",
        icon="🔓",
        website="https://www.openwall.com/john/",
        install_specs={
            "apt":    _s("john"),
            "dnf":    _s("john"),
            "pacman": _s("john"),
            "zypper": _s("john"),
        },
    ),
    SoftwareEntry(
        id="aircrack-ng",
        name="Aircrack-ng",
        description="Complete suite of tools for assessing Wi-Fi network security.",
        category="Security",
        icon="📡",
        website="https://www.aircrack-ng.org",
        install_specs={
            "apt":    _s("aircrack-ng"),
            "dnf":    _s("aircrack-ng"),
            "pacman": _s("aircrack-ng"),
            "zypper": _s("aircrack-ng"),
        },
    ),
    SoftwareEntry(
        id="hashcat",
        name="Hashcat",
        description="World's fastest and most advanced password recovery utility.",
        category="Security",
        icon="#️⃣",
        website="https://hashcat.net",
        install_specs={
            "apt":    _s("hashcat"),
            "dnf":    _s("hashcat"),
            "pacman": _s("hashcat"),
            "zypper": _s("hashcat"),
        },
    ),
]

# Quick lookup by id
CATALOG_MAP: Dict[str, SoftwareEntry] = {app.id: app for app in CATALOG}

CATEGORIES: List[str] = sorted(set(app.category for app in CATALOG))
