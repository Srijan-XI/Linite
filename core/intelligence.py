"""
Linite - Intelligence Engine
=============================
Analyses the current system profile and generates contextual, actionable
suggestions that appear in the GUI before/after installation.

Each Suggestion carries:
  priority    1 (low) – 10 (critical)
  category    "hardware" | "software" | "performance" | "security" | "compat"
  title       One-line summary
  body        Explanatory paragraph
  actions     List of SuggestionAction (label → what to do)

Checks performed
----------------
1. Low RAM           → recommend lightweight alternatives (Chromium→Falkon,
                        LibreOffice→AbiWord, VLC→MPV, etc.)
2. Very low RAM      → also flag heavy apps in the selection
3. NVIDIA GPU        → recommend nvidia-driver install if nouveau detected
4. NVIDIA GPU + Wayland → warn about session compatibility
5. Old Ubuntu LTS    → suggest snap/flatpak for newer app versions
6. Running in VM     → skip GPU-intensive suggestions; add VM additions hint
7. Running in container → strongly advise against GUI apps
8. No desktop env    → warn on GUI-only apps in selections
9. Architecture      → warn if app has no ARM/non-x86 package
10. Proprietary apps  → remind of licensing where relevant
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from core.detection import SystemInfo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SuggestionAction:
    label: str           # Button label, e.g. "Install nvidia-driver"
    action_id: str       # Machine-readable token consumed by the GUI handler
    payload: dict = field(default_factory=dict)   # extra data (app_ids, etc.)


@dataclass
class Suggestion:
    id:        str
    title:     str
    body:      str
    category:  str        # "hardware" | "software" | "performance" | "security" | "compat"
    priority:  int        # 1 (informational) … 10 (critical)
    icon:      str = "💡"
    actions:   List[SuggestionAction] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lightweight alternative map (heavy_app → lighter_alternative)
# ---------------------------------------------------------------------------

_LIGHTWEIGHT_ALTERNATIVES: Dict[str, str] = {
    "chromium":      "firefox",       # Chromium eats more RAM than Firefox
    "libreoffice":   "abiword",       # Abiword is much lighter
    "blender":       "inkscape",      # Inkscape at least runs on 1 GB
    "obs":           "simplescreenrecorder",
    "gimp":          "pinta",         # Pinta ≃ MS Paint, very lightweight
    "vlc":           "mpv",           # MPV has a simpler UI, lighter footprint
    "vscode":        "vim",           # Vim/Neovim on extremely low-RAM systems
    "discord":       "telegram",
    "thunderbird":   "mutt",
    "virtualbox":    "qemu",
}

# GPU-heavy apps (we warn on VM/low-RAM)
_GPU_HEAVY: Set[str] = {"blender", "obs", "steam", "lutris", "vmware"}

# GUI-only apps (warn on server/no-DE environment)
_GUI_ONLY: Set[str] = {
    "gimp", "inkscape", "blender", "libreoffice", "okular", "evince",
    "foxitreader", "obs", "audacity", "handbrake", "steam", "lutris",
    "discord", "telegram", "slack", "zoom", "spotify", "vlc",
    "vscode", "thunderbird", "firefox", "chromium", "brave",
    "google-chrome", "virtualbox", "zenmap",
}

# Apps that benefit from the very latest version (suggest flatpak/snap)
_BENEFITS_FROM_FLATPAK: Set[str] = {
    "vscode", "firefox", "chromium", "brave", "discord", "spotify",
    "telegram", "slack", "zoom", "obs", "libreoffice",
}

# Proprietary / license-reminder apps
_PROPRIETARY: Dict[str, str] = {
    "google-chrome": "Google Chrome is proprietary; Chromium is the open-source equivalent.",
    "spotify":       "Spotify is a proprietary service that requires an account.",
    "slack":         "Slack is proprietary; consider open-source alternatives like Element.",
    "zoom":          "Zoom is proprietary; consider Jitsi Meet or Signal for privacy.",
    "vmware":        "VMware Workstation Player is free for personal use only.",
    "oracle-jdk":    "Oracle JDK requires a paid subscription for commercial use.",
}


# ---------------------------------------------------------------------------
# Intelligence Engine
# ---------------------------------------------------------------------------

class IntelligenceEngine:
    """
    Analyses a SystemInfo and (optionally) the user's current app selection,
    returning a prioritised list of Suggestions.
    """

    def analyze(
        self,
        system: SystemInfo,
        selected_ids: Optional[Set[str]] = None,
    ) -> List[Suggestion]:
        """
        Run all checks and return suggestions sorted by priority (highest first).
        *selected_ids* is the set of app IDs the user is about to install; if
        omitted, only system-level checks are performed.
        """
        sel = selected_ids or set()
        suggestions: List[Suggestion] = []

        # System-level checks (always run)
        suggestions += self._check_low_ram(system, sel)
        suggestions += self._check_nvidia_gpu(system, sel)
        suggestions += self._check_vm(system, sel)
        suggestions += self._check_container(system)
        suggestions += self._check_no_desktop(system, sel)
        suggestions += self._check_old_ubuntu(system, sel)
        suggestions += self._check_arch_compat(system, sel)

        # Selection-level checks (only when apps chosen)
        if sel:
            suggestions += self._check_proprietary(sel)
            suggestions += self._check_gpu_heavy_on_vm(system, sel)

        # Deduplicate by id and sort
        seen: Set[str] = set()
        unique = []
        for s in suggestions:
            if s.id not in seen:
                seen.add(s.id)
                unique.append(s)

        return sorted(unique, key=lambda s: -s.priority)

    # ── Checkers ──────────────────────────────────────────────────────────

    def _check_low_ram(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        suggestions = []
        if not sys_info.is_linux:
            return []

        if sys_info.is_very_low_ram:
            alts_to_suggest = {
                app: alt
                for app, alt in _LIGHTWEIGHT_ALTERNATIVES.items()
                if app in sel
            }
            if alts_to_suggest:
                body = (
                    f"Your system has only {sys_info.ram_gb} GB RAM.  "
                    "Consider these lighter alternatives:\n"
                )
                body += "\n".join(
                    f"  • Replace **{a}** → **{b}**"
                    for a, b in alts_to_suggest.items()
                )
                suggestions.append(Suggestion(
                    id="very_low_ram_alts",
                    title=f"Very low RAM ({sys_info.ram_gb} GB) — lighter apps recommended",
                    body=body,
                    category="performance",
                    priority=8,
                    icon="🐏",
                    actions=[
                        SuggestionAction(
                            label=f"Swap to lighter apps",
                            action_id="swap_lightweight",
                            payload={"swaps": alts_to_suggest},
                        )
                    ],
                ))
            else:
                suggestions.append(Suggestion(
                    id="very_low_ram_general",
                    title=f"Very low RAM ({sys_info.ram_gb} GB)",
                    body=(
                        "Your system has less than 2 GB of RAM.  Installing "
                        "resource-heavy apps (browsers, editors, IDEs) may "
                        "cause significant slowdowns."
                    ),
                    category="performance",
                    priority=7,
                    icon="🐏",
                ))
        elif sys_info.is_low_ram:
            suggestions.append(Suggestion(
                id="low_ram_info",
                title=f"Limited RAM ({sys_info.ram_gb} GB) — some apps may be slow",
                body=(
                    "Your system has less than 4 GB of RAM.  Apps like Blender, "
                    "multiple browser tabs, or VMs may be sluggish.  Consider "
                    "MPV instead of VLC, or Vim/Neovim instead of VS Code."
                ),
                category="performance",
                priority=4,
                icon="🐏",
            ))
        return suggestions

    def _check_nvidia_gpu(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        if not sys_info.has_nvidia_gpu:
            return []
        suggestions = []

        # Nouveau (open-source) instead of proprietary driver
        if sys_info.gpu.driver in ("nouveau", "", "unknown"):
            suggestions.append(Suggestion(
                id="nvidia_proprietary_driver",
                title="NVIDIA GPU detected — proprietary driver not active",
                body=(
                    f"Your GPU ({sys_info.gpu.model or 'NVIDIA'}) is currently using "
                    f"the open-source 'nouveau' driver, which limits performance and "
                    f"lacks CUDA support.  Install the proprietary NVIDIA driver for "
                    f"full gaming and compute performance."
                ),
                category="hardware",
                priority=9,
                icon="🎮",
                actions=[
                    SuggestionAction(
                        label="Add nvidia-driver to selection",
                        action_id="add_app",
                        payload={"app_ids": ["nvidia-driver"]},
                    )
                ],
            ))

        # Wayland + NVIDIA historically problematic
        if sys_info.display_server == "wayland" and sys_info.gpu.driver == "nvidia":
            suggestions.append(Suggestion(
                id="nvidia_wayland_compat",
                title="NVIDIA + Wayland compatibility notice",
                body=(
                    "Some older NVIDIA drivers have issues with Wayland compositors.  "
                    "If you experience screen tearing or crashes, switch to an X11 "
                    "session, or ensure your driver version is ≥ 525."
                ),
                category="compat",
                priority=6,
                icon="⚠️",
            ))

        return suggestions

    def _check_vm(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        if not sys_info.is_vm:
            return []
        suggestions = [
            Suggestion(
                id="vm_detected",
                title="Running inside a virtual machine",
                body=(
                    "Linite detected a virtualised environment.  GPU-accelerated apps "
                    "(Steam, Blender, OBS) will have reduced performance or may not work "
                    "without proper GPU pass-through.  Consider installing VM guest "
                    "additions (open-vm-tools, VirtualBox Guest Additions) first."
                ),
                category="compat",
                priority=5,
                icon="🖥️",
            )
        ]
        return suggestions

    def _check_container(self, sys_info: SystemInfo) -> List[Suggestion]:
        if not sys_info.is_container:
            return []
        return [
            Suggestion(
                id="container_detected",
                title="Running inside a container — GUI apps will not work",
                body=(
                    "Linite detected a container environment (Docker / LXC).  "
                    "Graphical applications require a display server that is "
                    "typically not available inside containers.  Only install "
                    "CLI tools in this environment."
                ),
                category="compat",
                priority=10,
                icon="🐳",
            )
        ]

    def _check_no_desktop(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        if not sys_info.is_server or not sys_info.is_linux:
            return []
        gui_selected = sel & _GUI_ONLY
        if not gui_selected:
            return []
        names = ", ".join(sorted(gui_selected))
        return [
            Suggestion(
                id="no_desktop_gui_apps",
                title="No desktop environment detected — GUI apps selected",
                body=(
                    f"The following selected apps require a desktop environment to run: "
                    f"{names}.  On a server/headless system they will install but "
                    f"cannot launch without a display."
                ),
                category="compat",
                priority=7,
                icon="🖥️",
            )
        ]

    def _check_old_ubuntu(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        """For Ubuntu LTS versions ≤ 22.04, suggest Flatpak for freshness."""
        if not sys_info.is_linux:
            return []
        di = sys_info.distro
        if di.id not in ("ubuntu", "pop", "elementary", "linuxmint"):
            return []
        try:
            major = int(di.version.split(".")[0])
        except (ValueError, IndexError):
            return []
        if major > 22:
            return []

        snap_flatpak = sel & _BENEFITS_FROM_FLATPAK
        if not snap_flatpak:
            return []
        return [
            Suggestion(
                id="old_ubuntu_stale_repo",
                title=f"Ubuntu {di.version} repos may have older package versions",
                body=(
                    f"Ubuntu {di.version} LTS ships older versions of: "
                    f"{', '.join(sorted(snap_flatpak))}.  "
                    "For the latest versions, install via Flatpak (Flathub) or Snap."
                ),
                category="software",
                priority=5,
                icon="📦",
                actions=[
                    SuggestionAction(
                        label="Prefer Flatpak for these apps",
                        action_id="prefer_pm",
                        payload={"pm": "flatpak", "app_ids": list(snap_flatpak)},
                    )
                ],
            )
        ]

    def _check_arch_compat(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        """Warn if the CPU arch is not x86_64 (ARM, 32-bit, etc.)."""
        if sys_info.cpu_arch in ("x86_64", "unknown", ""):
            return []
        # Some apps are x86-only
        x86_only: Set[str] = {
            "steam", "lutris", "vmware", "google-chrome",
            "slack", "zoom", "spotify",
        }
        problematic = sel & x86_only
        if not problematic:
            return []
        return [
            Suggestion(
                id="arch_compat",
                title=f"Architecture {sys_info.cpu_arch} — some apps may not be available",
                body=(
                    f"Your CPU architecture is {sys_info.cpu_arch}.  The following "
                    f"selected apps may have no native package for this arch and could "
                    f"require x86 emulation or may simply be unavailable: "
                    f"{', '.join(sorted(problematic))}."
                ),
                category="compat",
                priority=6,
                icon="⚙️",
            )
        ]

    def _check_proprietary(self, sel: Set[str]) -> List[Suggestion]:
        suggestions = []
        for app_id, note in _PROPRIETARY.items():
            if app_id in sel:
                suggestions.append(Suggestion(
                    id=f"proprietary_{app_id}",
                    title=f"Proprietary software: {app_id}",
                    body=note,
                    category="security",
                    priority=3,
                    icon="🔒",
                ))
        return suggestions

    def _check_gpu_heavy_on_vm(self, sys_info: SystemInfo, sel: Set[str]) -> List[Suggestion]:
        if not (sys_info.is_vm or sys_info.is_low_ram):
            return []
        heavy = sel & _GPU_HEAVY
        if not heavy:
            return []
        return [
            Suggestion(
                id="gpu_heavy_vm_low_ram",
                title="GPU-intensive apps selected on constrained hardware",
                body=(
                    f"The following apps are GPU- or RAM-intensive and may perform "
                    f"poorly on this system: {', '.join(sorted(heavy))}.  "
                    "Consider whether you really need them in this environment."
                ),
                category="performance",
                priority=6,
                icon="⚡",
            )
        ]


# Module-level singleton
intelligence = IntelligenceEngine()
