"""Tests for StudentProfile — PISA competency tracking and RGPD erasure."""

from __future__ import annotations

from src.student_profile import ProfileManager, StudentProfile


class TestStudentProfile:
    def test_create_profile(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        assert p.student_id == "s1"
        assert p.display_name == "Alice"
        assert p.level == "CE2"
        assert p.competencies == {}
        assert p.created_at is not None
        assert p.updated_at is not None

    def test_update_competency(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("addition", mastery=0.75, pisa_level=3)
        assert "addition" in p.competencies
        assert p.competencies["addition"]["mastery"] == 0.75
        assert p.competencies["addition"]["pisa_level"] == 3

    def test_update_competency_clamps_mastery(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("over", mastery=1.5, pisa_level=1)
        assert p.competencies["over"]["mastery"] == 1.0
        p.update_competency("under", mastery=-0.3, pisa_level=1)
        assert p.competencies["under"]["mastery"] == 0.0

    def test_update_competency_clamps_pisa_level(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("high", mastery=0.5, pisa_level=10)
        assert p.competencies["high"]["pisa_level"] == 6
        p.update_competency("low", mastery=0.5, pisa_level=0)
        assert p.competencies["low"]["pisa_level"] == 1

    def test_update_competency_rounds_mastery(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("trigo", mastery=1 / 3, pisa_level=2)
        assert p.competencies["trigo"]["mastery"] == round(1 / 3, 3)

    def test_get_zpd_returns_weak_competencies(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("weak", mastery=0.3, pisa_level=1)
        p.update_competency("strong", mastery=0.8, pisa_level=4)
        zpd = p.get_zpd(threshold=0.5)
        assert "weak" in zpd
        assert "strong" not in zpd

    def test_get_zpd_default_threshold(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("mid", mastery=0.49, pisa_level=2)
        p.update_competency("above", mastery=0.5, pisa_level=2)
        zpd = p.get_zpd()
        assert "mid" in zpd
        assert "above" not in zpd

    def test_to_dict_and_from_dict_roundtrip(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        p.update_competency("math", mastery=0.6, pisa_level=3)
        d = p.to_dict()
        p2 = StudentProfile.from_dict(d)
        assert p2.student_id == p.student_id
        assert p2.display_name == p.display_name
        assert p2.level == p.level
        assert p2.competencies == p.competencies

    def test_no_sensitive_data_in_dict(self):
        p = StudentProfile(student_id="s1", display_name="Alice", level="CE2")
        d = p.to_dict()
        forbidden = {"email", "address", "last_name", "phone", "birth_date"}
        assert not forbidden & set(d.keys())


class TestProfileManager:
    def test_save_and_load(self, tmp_data_dir):
        manager = ProfileManager(tmp_data_dir)
        p = StudentProfile(student_id="abc", display_name="Bob", level="6e")
        p.update_competency("lecture", mastery=0.7, pisa_level=3)
        manager.save(p)
        loaded = manager.load("abc")
        assert loaded is not None
        assert loaded.student_id == "abc"
        assert loaded.competencies["lecture"]["mastery"] == 0.7

    def test_load_nonexistent_returns_none(self, tmp_data_dir):
        manager = ProfileManager(tmp_data_dir)
        assert manager.load("does_not_exist") is None

    def test_delete_removes_file(self, tmp_data_dir):
        manager = ProfileManager(tmp_data_dir)
        p = StudentProfile(student_id="del1", display_name="Charlie", level="CM1")
        manager.save(p)
        assert manager.load("del1") is not None
        manager.delete("del1")
        assert manager.load("del1") is None
