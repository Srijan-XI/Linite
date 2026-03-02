"""
Linite - Transaction Log Engine
================================
Persistent, structured audit log for every install, uninstall, update, and
system-tweak operation performed by Linite.

Storage layout
--------------
~/.config/linite/logs/
    YYYY-MM-DD.yaml      One file per calendar day (UTC).
    summary.yaml         Aggregated counters, updated on every write.

Record schema
-------------
Each YAML file holds a list of transaction dicts:

    transaction_id: a1b2c3d4
    session_id:     e5f6a7b8            # groups ops from one Linite run
    timestamp:      2026-03-02T11:18:24.123456
    action:         install             # install | uninstall | update
                                        # system_update | tweak | profile_apply
    status:         success             # success | failed | skipped
                                        # retried | fallback | cancelled
    app_id:         vlc                 # empty for system_update
    app_name:       VLC Media Player
    pm_used:        apt
    duration:       12.34               # seconds (0 if unknown)
    attempts:       1                   # >1 means retries occurred
    distro:         Ubuntu 24.04 (x86_64)
    output:         "…"                 # last 4096 chars of stdout+stderr
    error:          ""                  # non-empty on failure

Public API
----------
    from core.log_engine import tx_log

    tx_log.log("install", "success", app_id="vlc", ...)
    tx_log.query(action="install", status="failed")
    tx_log.get_stats()
    tx_log.export_text("/tmp/linite_log.txt")
"""

from __future__ import annotations

import logging as _logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

_log = _logging.getLogger(__name__)

_LOG_DIR   = Path.home() / ".config" / "linite" / "logs"
_MAX_OUTPUT = 4096   # characters stored per record


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TransactionRecord:
    transaction_id: str
    session_id:     str
    timestamp:      str        # ISO-8601 with microseconds
    action:         str        # install | uninstall | update | system_update
                               # tweak | profile_apply
    status:         str        # success | failed | skipped | retried
                               # fallback | cancelled
    app_id:         str  = ""
    app_name:       str  = ""
    pm_used:        str  = ""
    duration:       float = 0.0
    attempts:       int   = 1
    distro:         str  = ""
    output:         str  = ""
    error:          str  = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["duration"] = round(d["duration"], 3)
        # Truncate output to keep YAML files compact
        if len(d["output"]) > _MAX_OUTPUT:
            d["output"] = d["output"][-_MAX_OUTPUT:]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TransactionRecord":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.timestamp)

    @property
    def is_success(self) -> bool:
        return self.status in ("success", "retried", "fallback")


@dataclass
class LogStats:
    total:          int   = 0
    successes:      int   = 0
    failures:       int   = 0
    skipped:        int   = 0
    by_action:      Dict[str, int] = field(default_factory=dict)
    by_status:      Dict[str, int] = field(default_factory=dict)
    by_pm:          Dict[str, int] = field(default_factory=dict)
    total_duration: float = 0.0
    sessions:       int   = 0
    # [(app_id, app_name, count)]
    top_installed:  List[Tuple[str, str, int]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return round(self.successes / self.total * 100, 1) if self.total else 0.0


# ---------------------------------------------------------------------------
# Log Engine
# ---------------------------------------------------------------------------

class TransactionLogEngine:
    """
    Manages the Linite structured transaction log.

    One instance should be used application-wide (see module-level `tx_log`).
    """

    def __init__(self, log_dir: Path = _LOG_DIR):
        self._dir        = log_dir
        self._session_id = uuid.uuid4().hex[:8]
        self._distro     = ""

    # ── Configuration ─────────────────────────────────────────────────────

    def set_distro(self, distro_display_name: str) -> None:
        """Call once at startup with the detected distro name."""
        self._distro = distro_display_name

    # ── Writing ───────────────────────────────────────────────────────────

    def log(
        self,
        action:   str,
        status:   str,
        app_id:   str   = "",
        app_name: str   = "",
        pm_used:  str   = "",
        duration: float = 0.0,
        attempts: int   = 1,
        output:   str   = "",
        error:    str   = "",
    ) -> TransactionRecord:
        """
        Append one transaction record to today's log file and update the
        running summary.  Thread-safe (YAML append is atomic per write).

        Returns the created TransactionRecord.
        """
        rec = TransactionRecord(
            transaction_id = uuid.uuid4().hex[:8],
            session_id     = self._session_id,
            timestamp      = datetime.now(timezone.utc).isoformat(),
            action         = action,
            status         = status,
            app_id         = app_id,
            app_name       = app_name,
            pm_used        = pm_used,
            duration       = duration,
            attempts       = attempts,
            distro         = self._distro,
            output         = output,
            error          = error,
        )
        self._append(rec)
        self._update_summary(rec)
        return rec

    def _daily_path(self, dt: Optional[datetime] = None) -> Path:
        d = dt or datetime.now(timezone.utc)
        return self._dir / f"{d.date().isoformat()}.yaml"

    def _append(self, rec: TransactionRecord) -> None:
        """Append one record dict to the current day's YAML file."""
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._daily_path()
        try:
            existing = _safe_load_list(path)
            existing.append(rec.to_dict())
            _safe_dump_list(path, existing)
        except Exception as exc:
            _log.error("Failed to write transaction log: %s", exc)

    def _update_summary(self, rec: TransactionRecord) -> None:
        """Increment running counters in summary.yaml."""
        path = self._dir / "summary.yaml"
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) \
                if path.exists() else {}
            if not isinstance(raw, dict):
                raw = {}

            raw["total"] = raw.get("total", 0) + 1

            # Use stable local refs so chained .get() always works
            by_action = raw.setdefault("by_action", {})
            by_action[rec.action] = by_action.get(rec.action, 0) + 1

            by_status = raw.setdefault("by_status", {})
            by_status[rec.status] = by_status.get(rec.status, 0) + 1

            if rec.pm_used:
                by_pm = raw.setdefault("by_pm", {})
                by_pm[rec.pm_used] = by_pm.get(rec.pm_used, 0) + 1

            raw["total_duration"] = \
                round(raw.get("total_duration", 0.0) + rec.duration, 3)

            # Track install counts per app_id
            if rec.action == "install" and rec.is_success and rec.app_id:
                ic = raw.setdefault("install_counts", {})
                ic[rec.app_id] = ic.get(rec.app_id, 0) + 1
            if rec.action == "uninstall" and rec.is_success and rec.app_id:
                ic = raw.get("install_counts", {})
                ic[rec.app_id] = max(ic.get(rec.app_id, 1) - 1, 0)
                raw["install_counts"] = ic

            path.write_text(
                yaml.dump(raw, default_flow_style=False, allow_unicode=True,
                          sort_keys=False),
                encoding="utf-8",
            )
        except Exception as exc:
            _log.warning("Failed to update summary.yaml: %s", exc)

    # ── Reading / Querying ────────────────────────────────────────────────

    def _load_all(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[TransactionRecord]:
        """
        Load and merge all daily log files within the given date range.
        Newest records last (chronological order).
        """
        if not self._dir.exists():
            return []

        daily_files = sorted(
            p for p in self._dir.glob("*.yaml")
            if p.name != "summary.yaml"
        )
        records: List[TransactionRecord] = []
        for path in daily_files:
            if path.name == "summary.yaml":
                continue
            for d in _safe_load_list(path):
                try:
                    rec = TransactionRecord.from_dict(d)
                    if since and rec.dt < since:
                        continue
                    if until and rec.dt > until:
                        continue
                    records.append(rec)
                except Exception:
                    pass  # skip malformed entries
        return records

    def query(
        self,
        action:   Optional[str]      = None,
        status:   Optional[str]      = None,
        app_id:   Optional[str]      = None,
        pm_used:  Optional[str]      = None,
        since:    Optional[datetime] = None,
        until:    Optional[datetime] = None,
        limit:    Optional[int]      = None,
        newest_first: bool           = True,
    ) -> List[TransactionRecord]:
        """
        Return filtered transaction records.

        Parameters
        ----------
        action        : e.g. "install" — exact match, None = all
        status        : e.g. "failed"  — exact match, None = all
        app_id        : app catalog ID — exact match, None = all
        pm_used       : e.g. "apt"     — exact match, None = all
        since / until : datetime bounds (timezone-aware recommended)
        limit         : max records to return (applied after filter + sort)
        newest_first  : sort order
        """
        records = self._load_all(since=since, until=until)

        if action:
            records = [r for r in records if r.action == action]
        if status:
            records = [r for r in records if r.status == status]
        if app_id:
            records = [r for r in records if r.app_id == app_id]
        if pm_used:
            records = [r for r in records if r.pm_used == pm_used]

        if newest_first:
            records = list(reversed(records))
        if limit:
            records = records[:limit]
        return records

    def get_stats(
        self,
        since: Optional[datetime] = None,
    ) -> LogStats:
        """Compute statistics over all (or recent) records."""
        records = self._load_all(since=since)
        stats = LogStats()
        session_ids: set = set()

        install_counts: Dict[str, Tuple[str, int]] = {}  # app_id → (name, count)

        for r in records:
            stats.total += 1
            stats.by_action[r.action]  = stats.by_action.get(r.action, 0) + 1
            stats.by_status[r.status]  = stats.by_status.get(r.status, 0) + 1
            if r.pm_used:
                stats.by_pm[r.pm_used] = stats.by_pm.get(r.pm_used, 0) + 1
            stats.total_duration += r.duration
            session_ids.add(r.session_id)

            if r.is_success:
                stats.successes += 1
            elif r.status in ("failed",):
                stats.failures += 1
            elif r.status in ("skipped", "cancelled"):
                stats.skipped += 1

            if r.action == "install" and r.is_success and r.app_id:
                aid = r.app_id
                _, cnt = install_counts.get(aid, (r.app_name, 0))
                install_counts[aid] = (r.app_name or aid, cnt + 1)

        stats.sessions = len(session_ids)
        stats.top_installed = sorted(
            [(aid, name, cnt) for aid, (name, cnt) in install_counts.items()],
            key=lambda x: -x[2],
        )[:10]

        return stats

    # ── Export ────────────────────────────────────────────────────────────

    def export_text(self, path: str, since: Optional[datetime] = None) -> int:
        """
        Write a human-readable plain-text log to *path*.
        Returns the number of records written.
        """
        records = self.query(since=since, newest_first=False)
        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║        Linite Transaction Log  —  Export               ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
        ]
        for r in records:
            icon = "✓" if r.is_success else "✗"
            lines.append(
                f"{icon} [{r.timestamp[:19]}]  "
                f"{r.action.upper():15s}  "
                f"{r.app_name or '(system)':25s}  "
                f"via {r.pm_used or '—':8s}  "
                f"{r.status:10s}  "
                f"{r.duration:.1f}s"
            )
            if r.error:
                lines.append(f"    ERROR: {r.error[:120]}")

        stats = self.get_stats(since=since)
        lines += [
            "",
            "─" * 70,
            f"Total: {stats.total}  |  "
            f"Success: {stats.successes}  |  "
            f"Failed: {stats.failures}  |  "
            f"Rate: {stats.success_rate}%  |  "
            f"Sessions: {stats.sessions}",
        ]

        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return len(records)

    def export_yaml(self, path: str, since: Optional[datetime] = None) -> int:
        """Export all records as a single YAML file.  Returns record count."""
        records = self.query(since=since, newest_first=False)
        data = [r.to_dict() for r in records]
        Path(path).write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        return len(records)

    # ── Maintenance ───────────────────────────────────────────────────────

    def clear_old_logs(self, keep_days: int = 30) -> int:
        """
        Delete daily log files older than *keep_days* days.
        Returns the number of files removed.
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=keep_days)
        removed = 0
        if not self._dir.exists():
            return 0
        for path in self._dir.glob("????.*.yaml"):
            if path.name == "summary.yaml":
                continue
            try:
                file_date_str = path.stem   # "YYYY-MM-DD"
                from datetime import date
                file_date = date.fromisoformat(file_date_str)
                if file_date < cutoff:
                    path.unlink()
                    removed += 1
            except Exception:
                pass
        _log.info("Pruned %d old log files (keep_days=%d)", removed, keep_days)
        return removed

    def clear_all(self) -> None:
        """Delete all log files.  Use with caution."""
        if not self._dir.exists():
            return
        for path in self._dir.glob("*.yaml"):
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_load_list(path: Path) -> list:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


def _safe_dump_list(path: Path, data: list) -> None:
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True,
                  sort_keys=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly:
#   from core.log_engine import tx_log
# ---------------------------------------------------------------------------
tx_log = TransactionLogEngine()
