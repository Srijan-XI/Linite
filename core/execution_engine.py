"""
Linite - Execution Engine
=========================
Smart installation orchestrator that wraps the existing installer with:

  • Dependency ordering  – topological sort ensures prerequisites install first
  • Parallel execution   – configurable worker pool
  • Retry logic          – exponential back-off (3 attempts)
  • Failure recovery     – if native PM fails, fall back to flatpak / snap
  • Rich progress events – fine-grained callback fed to the GUI progress panel

Architecture
------------
ExecutionPlan  – immutable description of what to install and in what order
ExecutionEngine – stateful orchestrator that carries out the plan
ExecutionResult – per-app outcome (status, pm used, stderr, duration)
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple

from data.software_catalog import SoftwareEntry, CATALOG_MAP
from core.distro import DistroInfo
from core.package_map import PackageMapLoader, package_map as _default_map
from core.installer import install_app, Status as _InstallStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Simple dependency graph  (app_id → set of app_id prerequisites)
# ---------------------------------------------------------------------------
# Keep this sparse — only add edges for real inter-app requirements.

_DEPS: Dict[str, List[str]] = {
    "docker":       ["curl"],
    "vscode":       ["curl", "wget"],
    "gh":           ["curl"],
    "brave":        ["curl"],
    "google-chrome": ["curl", "wget"],
    "metasploit":   ["curl"],
    "virtualbox":   ["curl"],
    "eclipse-temurin": ["curl", "wget"],
    "amazon-corretto": ["curl"],
    "zulu-jdk":     ["curl"],
}


def _topo_sort(app_ids: List[str]) -> List[List[str]]:
    """
    Topological sort of *app_ids* using the dependency graph.

    Returns a list of *waves*: apps in wave[0] have no deps, wave[1] depends
    on wave[0], etc.  Apps within the same wave can be installed in parallel.
    Apps not in app_ids are filtered from dependency edges.
    """
    id_set = set(app_ids)
    # Build adj list restricted to requested apps
    deps: Dict[str, Set[str]] = {
        a: {d for d in _DEPS.get(a, []) if d in id_set}
        for a in app_ids
    }
    in_degree: Dict[str, int] = {a: len(deps[a]) for a in app_ids}
    reverse: Dict[str, List[str]] = defaultdict(list)
    for a, ds in deps.items():
        for d in ds:
            reverse[d].append(a)

    waves: List[List[str]] = []
    ready = deque(a for a in app_ids if in_degree[a] == 0)
    while ready:
        wave = list(ready)
        ready.clear()
        waves.append(wave)
        for a in wave:
            for dependent in reverse[a]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready.append(dependent)

    # Any still unreachable (cycles) get appended at the end
    installed = {a for wave in waves for a in wave}
    remaining = [a for a in app_ids if a not in installed]
    if remaining:
        waves.append(remaining)

    return waves


# ---------------------------------------------------------------------------
# Result / Plan
# ---------------------------------------------------------------------------

class ExecStatus(Enum):
    SUCCESS  = auto()
    FAILED   = auto()
    RETRIED  = auto()   # succeeded after ≥1 retry
    SKIPPED  = auto()   # cancelled or not found
    FALLBACK = auto()   # succeeded but via fallback PM


@dataclass
class ExecutionResult:
    app_id:    str
    app_name:  str
    status:    ExecStatus
    pm_used:   str = ""
    error:     str = ""
    attempts:  int = 1
    duration:  float = 0.0     # seconds


@dataclass
class ExecutionPlan:
    """Resolved install plan: ordered waves + per-app PM assignments."""
    waves:      List[List[str]]          # install order
    pm_map:     Dict[str, str]           # app_id → pm
    spec_map:   Dict[str, object]        # app_id → PackageSpec
    entry_map:  Dict[str, SoftwareEntry] # app_id → SoftwareEntry
    unknown:    List[str]                # app_ids not in catalog


ProgressCallback = Callable[[str, str], None]   # (app_id, message)


# ---------------------------------------------------------------------------
# Execution Engine
# ---------------------------------------------------------------------------

class ExecutionEngine:
    """
    Orchestrates installation of a set of apps with dependency ordering,
    parallel workers, retry logic, and PM fallback.

    Parameters
    ----------
    distro          Current DistroInfo (from core.distro.detect())
    max_workers     Thread-pool size for parallel installs (default: 3)
    max_retries     Number of retry attempts on failure (default: 3)
    retry_delay     Base delay in seconds between retries (doubles each attempt)
    loader          PackageMapLoader to use (default: module-level singleton)
    """

    FALLBACK_PMS = ("flatpak", "snap")  # tried in this order on native PM failure

    def __init__(
        self,
        distro: DistroInfo,
        max_workers: int = 3,
        max_retries: int = 3,
        retry_delay:  float = 2.0,
        loader: Optional[PackageMapLoader] = None,
    ):
        self._distro      = distro
        self._max_workers = max(1, max_workers)
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._loader      = loader or _default_map
        self._cancel      = threading.Event()

    # ── Plan ───────────────────────────────────────────────────────────────

    def build_plan(
        self,
        app_ids: List[str],
        available_pms: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """Resolve dependency order and PM assignment for *app_ids*."""
        avail = available_pms or [self._distro.package_manager, "flatpak", "snap"]

        entry_map: Dict[str, SoftwareEntry] = {}
        pm_map:    Dict[str, str]           = {}
        spec_map:  Dict[str, object]        = {}
        unknown:   List[str]                = []
        valid:     List[str]                = []

        for aid in app_ids:
            entry = CATALOG_MAP.get(aid)
            if entry is None:
                unknown.append(aid)
                continue
            pm = self._loader.best_pm(
                aid, avail,
                preferred_pm=getattr(entry, "preferred_pm", None),
            )
            if pm is None:
                unknown.append(aid)
                continue
            spec = self._loader.get_spec(aid, pm)
            if spec is None:
                unknown.append(aid)
                continue
            entry_map[aid] = entry
            pm_map[aid]    = pm
            spec_map[aid]  = spec
            valid.append(aid)

        waves = _topo_sort(valid)
        return ExecutionPlan(
            waves=waves,
            pm_map=pm_map,
            spec_map=spec_map,
            entry_map=entry_map,
            unknown=unknown,
        )

    # ── Execution ──────────────────────────────────────────────────────────

    def execute(
        self,
        plan: ExecutionPlan,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> List[ExecutionResult]:
        """
        Execute *plan* wave by wave, each wave in parallel.
        Returns list of ExecutionResult (one per app, including SKIPPED entries
        for unknowns).
        """
        self._cancel.clear()
        results: List[ExecutionResult] = []

        # Report skipped / unknown entries first
        for aid in plan.unknown:
            entry = CATALOG_MAP.get(aid)
            name = entry.name if entry else aid
            results.append(ExecutionResult(
                app_id=aid, app_name=name,
                status=ExecStatus.SKIPPED,
                error="No suitable package manager found",
            ))
            if progress_cb:
                progress_cb(aid, f"⚠ Skipping {name}: no suitable PM found")

        # ── Disk space pre-check ───────────────────────────────────────────
        _free_mb = 0
        try:
            import shutil as _shutil
            _free_mb = _shutil.disk_usage("/").free // (1024 * 1024)
        except Exception:
            _free_mb = 0
        if _free_mb > 0:
            if _free_mb < 500:
                _msg = (
                    f"✗ Insufficient disk space: only {_free_mb} MB free "
                    f"(minimum 500 MB required). Installation blocked."
                )
                logger.error(_msg)
                if progress_cb:
                    progress_cb("__engine__", _msg)
                for _wave in plan.waves:
                    for _aid in _wave:
                        _entry = plan.entry_map.get(_aid)
                        results.append(ExecutionResult(
                            app_id=_aid,
                            app_name=_entry.name if _entry else _aid,
                            status=ExecStatus.SKIPPED,
                            error="Insufficient disk space",
                        ))
                return results
            elif _free_mb < 2048:
                _msg = (
                    f"⚠ Low disk space: {_free_mb} MB free. "
                    f"Installation may fail if packages are large."
                )
                logger.warning(_msg)
                if progress_cb:
                    progress_cb("__engine__", _msg)

        # Execute waves sequentially; apps within a wave run in parallel
        for wave_idx, wave in enumerate(plan.waves):
            if self._cancel.is_set():
                for aid in wave:
                    entry = plan.entry_map.get(aid)
                    results.append(ExecutionResult(
                        app_id=aid,
                        app_name=entry.name if entry else aid,
                        status=ExecStatus.SKIPPED,
                        error="Cancelled",
                    ))
                continue

            if progress_cb:
                progress_cb(
                    "__engine__",
                    f"── Wave {wave_idx + 1}/{len(plan.waves)}: "
                    f"{', '.join(plan.entry_map[a].name for a in wave)} ──",
                )

            wave_results = self._run_wave(wave, plan, progress_cb)
            results.extend(wave_results)

        return results

    def _run_wave(
        self,
        wave: List[str],
        plan: ExecutionPlan,
        progress_cb: Optional[ProgressCallback],
    ) -> List[ExecutionResult]:
        """Run one wave in parallel using a thread pool."""
        wave_results: List[ExecutionResult] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(self._install_with_retry, aid, plan, progress_cb): aid
                for aid in wave
            }
            for fut in as_completed(futures):
                try:
                    wave_results.append(fut.result())
                except Exception as exc:
                    aid = futures[fut]
                    entry = plan.entry_map.get(aid)
                    wave_results.append(ExecutionResult(
                        app_id=aid,
                        app_name=entry.name if entry else aid,
                        status=ExecStatus.FAILED,
                        error=str(exc),
                    ))
        return wave_results

    def _install_with_retry(
        self,
        app_id: str,
        plan: ExecutionPlan,
        progress_cb: Optional[ProgressCallback],
    ) -> ExecutionResult:
        """
        Attempt installation of a single app:
          1. Try native PM (up to max_retries)
          2. On total failure, try fallback PMs (flatpak, snap)
        """
        entry  = plan.entry_map[app_id]
        pm     = plan.pm_map[app_id]
        t0     = time.monotonic()
        last_error = ""

        # ── Retry loop ────────────────────────────────────────────────────
        for attempt in range(1, self._max_retries + 1):
            if self._cancel.is_set():
                return ExecutionResult(
                    app_id=app_id, app_name=entry.name,
                    status=ExecStatus.SKIPPED, pm_used=pm, error="Cancelled",
                    attempts=attempt,
                )

            if progress_cb:
                suffix = f" (attempt {attempt}/{self._max_retries})" if attempt > 1 else ""
                progress_cb(app_id, f"Installing {entry.name} via {pm}{suffix} …")

            result = install_app(entry, self._distro, progress_cb=progress_cb)
            duration = time.monotonic() - t0

            if result.status == _InstallStatus.OK:
                status = ExecStatus.RETRIED if attempt > 1 else ExecStatus.SUCCESS
                if progress_cb:
                    progress_cb(app_id, f"✓ {entry.name} installed successfully")
                return ExecutionResult(
                    app_id=app_id, app_name=entry.name,
                    status=status, pm_used=pm,
                    attempts=attempt, duration=duration,
                )

            last_error = result.error or "Unknown error"
            if progress_cb:
                progress_cb(app_id, f"✗ Attempt {attempt} failed: {last_error}")

            if attempt < self._max_retries:
                delay = self._retry_delay * (2 ** (attempt - 1))
                if progress_cb:
                    progress_cb(app_id, f"  Retrying in {delay:.0f}s …")
                time.sleep(delay)

        # ── Fallback PM ───────────────────────────────────────────────────
        for fb_pm in self.FALLBACK_PMS:
            if fb_pm == pm:
                continue
            fb_spec = self._loader.get_spec(app_id, fb_pm)
            if fb_spec is None:
                continue

            if progress_cb:
                progress_cb(app_id, f"  Trying fallback: {fb_pm} …")

            # Temporarily swap the PM assignment in the plan so install_app
            # uses the correct spec (install_app calls _pick_pm internally,
            # so we override via preferred_pm patching on a copy)
            import copy
            entry_copy = copy.copy(entry)
            object.__setattr__(entry_copy, "preferred_pm", fb_pm) \
                if hasattr(entry_copy, "__dataclass_fields__") else None

            fb_result = install_app(entry_copy, self._distro, progress_cb=progress_cb)
            if fb_result.status == _InstallStatus.OK:
                if progress_cb:
                    progress_cb(app_id, f"✓ {entry.name} installed via fallback ({fb_pm})")
                return ExecutionResult(
                    app_id=app_id, app_name=entry.name,
                    status=ExecStatus.FALLBACK, pm_used=fb_pm,
                    attempts=self._max_retries + 1,
                    duration=time.monotonic() - t0,
                )

        # ── Total failure ─────────────────────────────────────────────────
        return ExecutionResult(
            app_id=app_id, app_name=entry.name,
            status=ExecStatus.FAILED, pm_used=pm,
            error=last_error,
            attempts=self._max_retries,
            duration=time.monotonic() - t0,
        )

    # ── Cancellation ───────────────────────────────────────────────────────

    def cancel(self) -> None:
        """Signal the engine to stop after the current app finishes."""
        self._cancel.set()

    def reset(self) -> None:
        self._cancel.clear()
