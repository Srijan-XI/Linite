"""
Linite - Quick-Start Presets
Defines curated bundles of apps grouped by user role/workflow.

Each Preset holds:
  id          – unique slug
  name        – display name
  icon        – emoji
  tagline     – one-line summary shown under the name
  description – longer paragraph shown in the detail view
  color       – hex accent colour for the preset card
  app_ids     – ordered list of catalog IDs to pre-select
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Preset:
    id:          str
    name:        str
    icon:        str
    tagline:     str
    description: str
    color:       str          # hex, used as card accent
    app_ids:     List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

PRESETS: List[Preset] = [

    Preset(
        id="developer",
        name="Developer",
        icon="💻",
        tagline="Full-stack & DevOps toolbox",
        description=(
            "Everything a software developer needs: version control, "
            "runtimes, containers, a powerful editor, and the GitHub CLI. "
            "Covers web, backend, and infrastructure work."
        ),
        color="#7c6af7",   # purple
        app_ids=[
            "git",
            "vscode",
            "python3",
            "nodejs",
            "docker",
            "gh",
            "neovim",
            "curl",
            "wget",
            "htop",
            "firefox",
            "flatpak",
        ],
    ),

    Preset(
        id="student",
        name="Student",
        icon="🎓",
        tagline="Study, research & light coding",
        description=(
            "A balanced setup for students: an office suite for assignments, "
            "a PDF viewer, a web browser, basic coding tools, and a media "
            "player for lecture recordings."
        ),
        color="#50fa7b",   # green
        app_ids=[
            "firefox",
            "libreoffice",
            "thunderbird",
            "okular",
            "evince",
            "vlc",
            "git",
            "python3",
            "vscode",
            "flameshot",
            "telegram",
        ],
    ),

    Preset(
        id="gamer",
        name="Gamer",
        icon="🎮",
        tagline="Maximum frames, zero limits",
        description=(
            "The complete Linux gaming stack: Steam for your library, "
            "Lutris for legacy and Windows titles via Wine/Proton, "
            "Discord for party chat, and OBS for streaming or recording."
        ),
        color="#ff79c6",   # pink
        app_ids=[
            "steam",
            "lutris",
            "discord",
            "obs",
            "vlc",
            "spotify",
            "htop",
            "firefox",
            "flatpak",
        ],
    ),

    Preset(
        id="content_creator",
        name="Content Creator",
        icon="🎬",
        tagline="Create, edit & stream anything",
        description=(
            "A pro creative suite: OBS for streaming, GIMP and Inkscape "
            "for graphics, Blender for 3-D, Audacity for audio, HandBrake "
            "for video encoding, and Spotify to keep the vibe going."
        ),
        color="#f1fa8c",   # yellow
        app_ids=[
            "obs",
            "gimp",
            "inkscape",
            "blender",
            "audacity",
            "handbrake",
            "vlc",
            "spotify",
            "flameshot",
            "discord",
        ],
    ),

    Preset(
        id="daily_user",
        name="Daily User",
        icon="🏠",
        tagline="Everyday essentials, nothing more",
        description=(
            "The essentials for comfortable daily use: a browser, "
            "email client, office suite, media player, cloud storage, "
            "messaging apps, and a screenshot tool."
        ),
        color="#8be9fd",   # cyan
        app_ids=[
            "firefox",
            "chromium",
            "thunderbird",
            "libreoffice",
            "vlc",
            "spotify",
            "discord",
            "telegram",
            "dropbox",
            "flameshot",
            "htop",
        ],
    ),

    Preset(
        id="security",
        name="Security / Pentester",
        icon="🔐",
        tagline="Recon, scanning & analysis toolkit",
        description=(
            "Essential open-source security tools: Nmap for network "
            "discovery, Wireshark for packet analysis, Metasploit "
            "for penetration testing, and several password-auditing utilities."
        ),
        color="#ff5555",   # red
        app_ids=[
            "nmap",
            "wireshark",
            "metasploit",
            "hydra",
            "john",
            "aircrack-ng",
            "sqlmap",
            "burpsuite",
            "firefox",
            "curl",
            "wget",
            "htop",
        ],
    ),
]

# Quick lookup by id
PRESETS_MAP = {p.id: p for p in PRESETS}
