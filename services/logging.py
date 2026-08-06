from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from config.settings import get_settings
from utils.validation import sanitize_for_log


def _serialize_for_json(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_json(v) for v in obj]
    if hasattr(obj, "model_dump"):
        return _serialize_for_json(obj.model_dump())
    return obj


class LoggingService:
    def __init__(self, log_file: str | None = None):
        settings = get_settings()
        self._log_file = Path(log_file or settings.log_file)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._logger = structlog.get_logger("negotiation")

    def log(self, entry: dict[str, Any]) -> None:
        sanitized = sanitize_for_log(entry)
        sanitized = _serialize_for_json(sanitized)
        sanitized["timestamp"] = datetime.now(UTC).isoformat()

        self._logger.info("negotiation_complete", **sanitized)

        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitized, ensure_ascii=False) + "\n")
        except OSError as e:
            self._logger.exception("log_write_failed", error=str(e), path=str(self._log_file))

    def log_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        entry = {
            "error": type(error).__name__,
            "message": str(error),
            "context": sanitize_for_log(context or {}),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        entry = _serialize_for_json(entry)
        self._logger.error("negotiation_error", **entry)
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def get_recent_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self._log_file.exists():
            return []
        try:
            with self._log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
            return [json.loads(line) for line in lines[-limit:]]
        except (OSError, json.JSONDecodeError):
            return []
