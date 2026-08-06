from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileStorage:
    def __init__(self, base_path: str | Path = "data") -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save_negotiation(self, negotiation_id: str, data: dict[str, Any]) -> None:
        file_path = self._base_path / f"{negotiation_id}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_negotiation(self, negotiation_id: str) -> dict[str, Any] | None:
        file_path = self._base_path / f"{negotiation_id}.json"
        if not file_path.exists():
            return None
        with file_path.open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    def list_negotiations(self) -> list[str]:
        return [f.stem for f in self._base_path.glob("*.json")]

    def delete_negotiation(self, negotiation_id: str) -> bool:
        file_path = self._base_path / f"{negotiation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
