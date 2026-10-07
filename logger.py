"""
Robust, fail-safe JSON Lines logger for Flip7 Advisor.
Guarantees silent file-only persistence without console pollution or unhandled errors.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def get_default_log_path(log_dir: str = "logs") -> str:
    """Generate a datetime-based log file path in log_dir (e.g. logs/YYYYMMDD_HHMMSS.jsonl)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = os.path.join(log_dir, f"{timestamp}.jsonl")
    if not os.path.exists(candidate):
        return candidate
    counter = 1
    while os.path.exists(os.path.join(log_dir, f"{timestamp}_{counter}.jsonl")):
        counter += 1
    return os.path.join(log_dir, f"{timestamp}_{counter}.jsonl")


class Flip7Logger:
    """Best-effort JSON Lines logger that silently persists command events."""

    def __init__(self, file_path: Optional[str] = None):
        target_path = file_path or get_default_log_path()
        self.file_path = os.path.abspath(os.path.expanduser(target_path))
        self._is_closed = False
        self._records_written = 0
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        try:
            parent = os.path.dirname(self.file_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        except (OSError, ValueError):
            pass

    @property
    def records_written(self) -> int:
        return self._records_written

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    def log_command(
        self,
        raw_input: Optional[str],
        normalized_input: str,
        command: Optional[str],
        arguments: List[str],
        outcome: str,
        state: Dict[str, Any],
        stats: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if self._is_closed:
            return

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "command",
            "raw_input": raw_input,
            "normalized_input": normalized_input,
            "command": command,
            "arguments": arguments,
            "outcome": outcome,
            "state": state,
        }
        if stats is not None:
            record["stats"] = stats
        if error is not None:
            record["error"] = error

        self._write_record(record)

    def _write_record(self, record: Dict[str, Any]) -> None:
        try:
            line = json.dumps(record, default=str)
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            self._records_written += 1
        except (OSError, TypeError, ValueError):
            # Best-effort silent failure per specification
            pass

    def record(self, event: str, **fields: Any) -> None:
        """Compatibility method for legacy callers."""
        if self._is_closed:
            return
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        self._write_record(payload)

    def close(self) -> None:
        self._is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Backward compatibility alias
Flip7FileLogger = Flip7Logger
