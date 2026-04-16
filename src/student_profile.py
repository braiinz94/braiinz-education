"""StudentProfile — local JSON storage with PISA competency tracking and RGPD erasure."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StudentProfile:
    student_id: str
    display_name: str
    level: str
    competencies: dict[str, dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def update_competency(self, key: str, *, mastery: float, pisa_level: int) -> None:
        """Update or create a competency entry with clamped and rounded values."""
        mastery = round(max(0.0, min(1.0, mastery)), 3)
        pisa_level = max(1, min(6, pisa_level))
        self.competencies[key] = {"mastery": mastery, "pisa_level": pisa_level}
        self.updated_at = _now_iso()

    def get_zpd(self, threshold: float = 0.5) -> dict[str, dict[str, Any]]:
        """Return competencies with mastery strictly below threshold (Zone of Proximal Dev)."""
        return {k: v for k, v in self.competencies.items() if v["mastery"] < threshold}

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "display_name": self.display_name,
            "level": self.level,
            "competencies": self.competencies,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudentProfile":
        return cls(
            student_id=data["student_id"],
            display_name=data["display_name"],
            level=data["level"],
            competencies=data.get("competencies", {}),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class ProfileManager:
    """Manages persistence of StudentProfile objects as JSON files."""

    def __init__(self, data_dir: Path | str) -> None:
        self._profiles_dir = Path(data_dir) / "profiles"
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, student_id: str) -> Path:
        return self._profiles_dir / f"{student_id}.json"

    def save(self, profile: StudentProfile) -> None:
        """Atomic write via tmp file + os.replace."""
        target = self._path(profile.student_id)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, target)

    def load(self, student_id: str) -> StudentProfile | None:
        path = self._path(student_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return StudentProfile.from_dict(data)

    def delete(self, student_id: str) -> None:
        """RGPD Art. 17 — right to erasure."""
        path = self._path(student_id)
        if path.exists():
            path.unlink()
