"""
Linite - Profile Engine
=======================
Loads TOML-defined profiles from  data/profiles/<id>.toml, resolves each
profile's app list against the software catalog, and applies system tweaks
after a successful install.

Profile TOML schema  (data/profiles/developer.toml)
----------------------------------------------------
id          = "developer"
name        = "Developer"
icon        = "💻"
color       = "#7c6af7"
tagline     = "Full-stack & DevOps toolbox"
description = "Everything a software developer needs …"

packages = ["git", "vscode", "python3"]

[[system_tweaks]]
id                = "enable_docker"
description       = "Enable Docker daemon on startup"
command           = "systemctl enable --now docker"
requires_package  = "docker"
run_as_root       = true

User-created profiles are saved to  ~/.config/linite/profiles/<id>.toml.
Legacy YAML profiles are auto-migrated to TOML on first load.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set

import tomllib

logger = logging.getLogger(__name__)

_PROFILES_DIR = Path(__file__).resolve().parent.parent / "data" / "profiles"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SystemTweak:
    """A post-install shell command that configures the system."""
    id:               str
    description:      str
    command:          str
    requires_package: str = ""    # only execute if this package was installed
    run_as_root:      bool = True


@dataclass
class ProfileDef:
    """In-memory representation of a profile YAML file."""
    id:          str
    name:        str
    icon:        str  = "📦"
    color:       str  = "#7c6af7"
    tagline:     str  = ""
    description: str  = ""
    packages:    List[str]       = field(default_factory=list)
    system_tweaks: List[SystemTweak] = field(default_factory=list)

    def valid_packages(self, catalog_ids: Set[str]) -> List[str]:
        """Return only packages that exist in the catalog."""
        return [p for p in self.packages if p in catalog_ids]


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def _parse_profile(data: dict, source_path: Path) -> ProfileDef:
    """Convert raw YAML dict → ProfileDef."""
    tweaks = []
    for t in data.get("system_tweaks", []):
        tweaks.append(SystemTweak(
            id=str(t.get("id", "")),
            description=str(t.get("description", "")),
            command=str(t.get("command", "")),
            requires_package=str(t.get("requires_package", "")),
            run_as_root=bool(t.get("run_as_root", True)),
        ))
    return ProfileDef(
        id=str(data.get("id", source_path.stem)),
        name=str(data.get("name", source_path.stem.title())),
        icon=str(data.get("icon", "📦")),
        color=str(data.get("color", "#7c6af7")),
        tagline=str(data.get("tagline", "")),
        description=str(data.get("description", "")),
        packages=list(data.get("packages", [])),
        system_tweaks=tweaks,
    )


# ---------------------------------------------------------------------------
# TOML serialiser (tomllib is read-only; we hand-write TOML for user profiles)
# ---------------------------------------------------------------------------

def _profile_to_toml(profile: "ProfileDef") -> str:
    """Serialise a ProfileDef to a TOML string suitable for writing to disk."""

    def _esc(s: str) -> str:
        """Escape backslashes, double-quotes, and newlines for a TOML basic string."""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    lines: list[str] = [
        "# Linite user profile — auto-generated, safe to hand-edit",
        "",
        f'id          = "{_esc(profile.id)}"',
        f'name        = "{_esc(profile.name)}"',
        f'icon        = "{_esc(profile.icon)}"',
        f'color       = "{_esc(profile.color)}"',
        f'tagline     = "{_esc(profile.tagline)}"',
        f'description = "{_esc(profile.description)}"',
        "",
    ]

    # packages as a single-line TOML array
    if profile.packages:
        items = ", ".join(f'"{p}"' for p in profile.packages)
        lines.append(f"packages = [{items}]")
    else:
        lines.append("packages = []")

    for tweak in profile.system_tweaks:
        lines.append("")
        lines.append("[[system_tweaks]]")
        lines.append(f'id                = "{_esc(tweak.id)}"')
        lines.append(f'description       = "{_esc(tweak.description)}"')
        lines.append(f'command           = "{_esc(tweak.command)}"')
        lines.append(f'requires_package  = "{_esc(tweak.requires_package)}"')
        lines.append(f'run_as_root       = {"true" if tweak.run_as_root else "false"}')

    lines.append("")  # trailing newline
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ProfileEngine
# ---------------------------------------------------------------------------

class ProfileEngine:
    """
    Manages loading, saving and applying profiles.

    The engine merges YAML profiles from two locations:
      1. Built-in profiles  :  data/profiles/*.yaml     (read-only, shipped)
      2. User profiles      :  ~/.config/linite/profiles/*.yaml  (read-write)
    User profiles with the same id override built-ins.
    """

    def __init__(self):
        self._builtin_dir = _PROFILES_DIR
        self._user_dir    = Path.home() / ".config" / "linite" / "profiles"
        self._cache: Dict[str, ProfileDef] = {}

    # ── Loading ────────────────────────────────────────────────────────────

    def _load_file(self, path: Path) -> Optional[ProfileDef]:
        try:
            with path.open("rb") as fh:
                raw = tomllib.load(fh) or {}
            return _parse_profile(raw, path)
        except Exception as exc:
            logger.error("Cannot load profile %s: %s", path, exc)
            return None

    def _load_all(self) -> Dict[str, ProfileDef]:
        """Load built-ins then overlay user profiles."""
        # Migrate any legacy .yaml user profiles to .toml on first run
        if self._user_dir.exists():
            for yaml_path in list(self._user_dir.glob("*.yaml")):
                self._migrate_yaml_profile(yaml_path)

        profiles: Dict[str, ProfileDef] = {}
        for directory in (self._builtin_dir, self._user_dir):
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.toml")):
                p = self._load_file(path)
                if p:
                    profiles[p.id] = p
        return profiles

    def _migrate_yaml_profile(self, yaml_path: Path) -> None:
        """Convert a legacy YAML user profile to TOML and rename the original."""
        toml_path = yaml_path.with_suffix(".toml")
        if toml_path.exists():
            return  # already migrated
        try:
            import yaml as _yaml  # local import — only needed during migration
            raw = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            profile = _parse_profile(raw, yaml_path)
            toml_path.write_text(_profile_to_toml(profile), encoding="utf-8")
            yaml_path.rename(yaml_path.with_suffix(".yaml.bak"))
            logger.info("Migrated user profile %s → %s", yaml_path.name, toml_path.name)
        except Exception as exc:
            logger.warning("Could not migrate %s: %s", yaml_path, exc)

    def list_profiles(self, force_reload: bool = False) -> List[ProfileDef]:
        """Return all available profiles (built-in + user), sorted by name."""
        if not self._cache or force_reload:
            self._cache = self._load_all()
        return sorted(self._cache.values(), key=lambda p: p.name)

    def get(self, profile_id: str) -> Optional[ProfileDef]:
        """Return a single profile by ID or None."""
        if not self._cache:
            self._cache = self._load_all()
        return self._cache.get(profile_id)

    # ── Saving user profiles ───────────────────────────────────────────────

    def save_user_profile(self, profile: ProfileDef) -> Path:
        """Persist a ProfileDef as a TOML file in the user profiles dir."""
        self._user_dir.mkdir(parents=True, exist_ok=True)
        path = self._user_dir / f"{profile.id}.toml"
        path.write_text(_profile_to_toml(profile), encoding="utf-8")
        self._cache[profile.id] = profile
        logger.info("Saved profile '%s' → %s", profile.id, path)
        return path

    # ── Applying system tweaks ─────────────────────────────────────────────

    def apply_tweaks(
        self,
        profile: ProfileDef,
        installed_ids: Set[str],
        progress_cb=None,
    ) -> Dict[str, bool]:
        """
        Run eligible system tweaks for *profile*.

        A tweak is skipped if its `requires_package` was not in
        *installed_ids* (empty string means 'always run').

        Returns { tweak_id: success_bool }.
        """
        results: Dict[str, bool] = {}
        for tweak in profile.system_tweaks:
            # Skip if the required package was not installed
            if tweak.requires_package and tweak.requires_package not in installed_ids:
                logger.debug("Skipping tweak '%s' (package not installed)", tweak.id)
                continue

            if progress_cb:
                progress_cb("tweaks", f"[tweak] {tweak.description}")

            cmd = tweak.command
            if tweak.run_as_root and subprocess.os.geteuid() != 0:  # type: ignore
                cmd = f"sudo sh -c '{cmd}'"

            try:
                r = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=60
                )
                success = r.returncode == 0
                if progress_cb:
                    tag = "success" if success else "error"
                    progress_cb("tweaks", (r.stdout + r.stderr).strip() or tweak.description)
            except Exception as exc:
                success = False
                if progress_cb:
                    progress_cb("tweaks", f"[error] {exc}")

            results[tweak.id] = success
            logger.info(
                "Tweak '%s': %s", tweak.id, "OK" if success else "FAILED"
            )

        return results


# Module-level singleton
profile_engine = ProfileEngine()
