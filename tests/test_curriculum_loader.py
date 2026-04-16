"""Tests for CurriculumLoader — pack_fr_maths_seconde."""

from __future__ import annotations

import pytest

from src.curriculum.loader import CurriculumLoader


@pytest.fixture
def loader() -> CurriculumLoader:
    return CurriculumLoader()


def test_load_builtin_pack(loader: CurriculumLoader) -> None:
    pack = loader.load("fr", "maths", "seconde")
    assert pack["country"] == "fr"
    assert pack["subject"] == "maths"
    assert pack["level"] == "seconde"


def test_pack_has_chapters(loader: CurriculumLoader) -> None:
    pack = loader.load("fr", "maths", "seconde")
    assert "chapters" in pack
    assert len(pack["chapters"]) == 5


def test_each_chapter_has_competencies(loader: CurriculumLoader) -> None:
    pack = loader.load("fr", "maths", "seconde")
    for chapter in pack["chapters"]:
        assert "competencies" in chapter
        assert len(chapter["competencies"]) > 0


def test_each_competency_has_bloom_level(loader: CurriculumLoader) -> None:
    pack = loader.load("fr", "maths", "seconde")
    for chapter in pack["chapters"]:
        for comp in chapter["competencies"]:
            assert "bloom_level" in comp
            assert 1 <= comp["bloom_level"] <= 6


def test_load_nonexistent_raises(loader: CurriculumLoader) -> None:
    with pytest.raises(FileNotFoundError):
        loader.load("xx", "unknown", "terminale")


def test_list_competency_ids(loader: CurriculumLoader) -> None:
    ids = loader.list_competency_ids("fr", "maths", "seconde")
    assert isinstance(ids, list)
    assert len(ids) > 0
    # Spot-check some known IDs
    assert "nombres.equations" in ids
    assert "fonctions.affines" in ids
    assert "algorithmique.boucles" in ids


def test_get_competency_by_id(loader: CurriculumLoader) -> None:
    comp = loader.get_competency("fr", "maths", "seconde", "geometrie.vecteurs")
    assert comp is not None
    assert comp["id"] == "geometrie.vecteurs"
    assert "bloom_level" in comp
    assert "pisa_domain" in comp

    missing = loader.get_competency("fr", "maths", "seconde", "inexistant.comp")
    assert missing is None
