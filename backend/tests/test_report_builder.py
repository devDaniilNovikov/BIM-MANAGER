"""Tests for report_builder service."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.report_builder import build_report


class TestBuildReport:
    async def test_spaces_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "spaces")
        assert result is not None
        assert result["title"] == "Ведомость помещений"
        assert "columns" in result
        assert "rows" in result
        assert len(result["rows"]) == 3  # 3 spaces in fixture
        assert "Этаж" in result["columns"]
        assert "Площадь" in result["columns"][4]

    async def test_doors_windows_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "doors-windows")
        assert result is not None
        assert result["title"] == "Ведомость дверей и окон"
        assert len(result["rows"]) == 4  # 2 doors + 2 windows

    async def test_walls_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "walls")
        assert result is not None
        assert result["title"] == "Ведомость стен"
        # 3 walls in fixture (2 named + 1 unnamed)
        assert len(result["rows"]) == 3

    async def test_slabs_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "slabs")
        assert result is not None
        assert result["title"] == "Ведомость перекрытий"
        assert len(result["rows"]) == 2  # 2 slabs

    async def test_quantities_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "quantities")
        assert result is not None
        assert result["title"] == "Сводная таблица количественных показателей"
        assert len(result["rows"]) > 0
        # Check it has correct columns
        assert "Категория" in result["columns"]
        assert "Количество" in result["columns"]

    async def test_summary_report(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "summary")
        assert result is not None
        assert result["title"] == "Сводный аналитический отчёт"
        assert "sections" in result
        assert len(result["sections"]) == 2

    async def test_nonexistent_project(self, db: AsyncSession):
        result = await build_report(db, uuid.uuid4(), "spaces")
        assert result is None

    async def test_quantities_report_has_numeric_values(self, db: AsyncSession, sample_project: Project):
        result = await build_report(db, sample_project.id, "quantities")
        for row in result["rows"]:
            assert isinstance(row[1], int)  # count
            assert isinstance(row[2], float)  # area
            assert isinstance(row[3], float)  # volume
