"""Tests for export_service."""

import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.export_service import _to_pdf, export_report


class TestExportReport:
    async def test_export_xlsx(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "spaces", "xlsx")
        assert result is not None
        assert isinstance(result, io.BytesIO)
        content = result.read()
        assert len(content) > 0
        # XLSX files start with PK (ZIP)
        assert content[:2] == b"PK"

    async def test_export_csv(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "spaces", "csv")
        assert result is not None
        content = result.read().decode("utf-8-sig")
        assert "Этаж" in content
        assert len(content.strip().split("\n")) >= 2  # header + data

    async def test_export_pdf(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "spaces", "pdf")
        assert result is not None
        content = result.read()
        assert len(content) > 0
        # PDF starts with %PDF
        assert content[:4] == b"%PDF"

    async def test_export_summary_pdf(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "summary", "pdf")
        assert result is not None
        content = result.read()
        assert len(content) > 0
        assert content[:4] == b"%PDF"

    def test_to_pdf_with_long_cyrillic_text(self):
        result = _to_pdf(
            "Тестовый отчёт",
            ["№", "Описание", "Статус"],
            [[
                1,
                "Очень длинное описание ошибки на русском языке, которое должно корректно переноситься внутри ячейки PDF-таблицы и не ломать вёрстку документа. " * 3,
                "Открыто",
            ]],
        )
        content = result.read()
        assert content[:4] == b"%PDF"
        assert len(content) > 1500

    async def test_export_walls_xlsx(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "walls", "xlsx")
        assert result is not None
        assert isinstance(result, io.BytesIO)

    async def test_export_issues(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "issues", "xlsx")
        assert result is not None
        content = result.read()
        assert content[:2] == b"PK"

    async def test_export_summary_xlsx(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "summary", "xlsx")
        assert result is not None

    async def test_export_nonexistent_project(self, db: AsyncSession):
        result = await export_report(db, uuid.uuid4(), "spaces", "xlsx")
        assert result is None

    async def test_export_quantities_csv(self, db: AsyncSession, sample_project: Project):
        result = await export_report(db, sample_project.id, "quantities", "csv")
        assert result is not None
        content = result.read().decode("utf-8-sig")
        assert "Категория" in content
