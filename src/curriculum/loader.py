"""CurriculumLoader — loads built-in curriculum packs from JSON files."""

from __future__ import annotations

import json
from pathlib import Path


_BUILTIN_DIR = Path(__file__).parent


class CurriculumLoader:
    """Load and query curriculum packs stored as JSON in the curriculum package directory."""

    def _pack_path(self, country: str, subject: str, level: str) -> Path:
        filename = f"pack_{country}_{subject}_{level}.json"
        return _BUILTIN_DIR / filename

    def load(self, country: str, subject: str, level: str) -> dict:
        """Load a curriculum pack. Raises FileNotFoundError if not found."""
        path = self._pack_path(country, subject, level)
        if not path.exists():
            raise FileNotFoundError(
                f"Curriculum pack not found: {path.name}. "
                f"Available packs are in {_BUILTIN_DIR}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def list_competency_ids(self, country: str, subject: str, level: str) -> list[str]:
        """Return all competency IDs from the given pack."""
        pack = self.load(country, subject, level)
        ids: list[str] = []
        for chapter in pack.get("chapters", []):
            for comp in chapter.get("competencies", []):
                ids.append(comp["id"])
        return ids

    def get_competency(
        self, country: str, subject: str, level: str, competency_id: str
    ) -> dict | None:
        """Return the competency dict for the given ID, or None if not found."""
        pack = self.load(country, subject, level)
        for chapter in pack.get("chapters", []):
            for comp in chapter.get("competencies", []):
                if comp["id"] == competency_id:
                    return comp
        return None
