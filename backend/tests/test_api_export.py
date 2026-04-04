"""Tests for /api/models/{id}/export endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestExportData:
    async def test_export_xlsx(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/spaces?format=xlsx")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]
        assert resp.content[:2] == b"PK"

    async def test_export_csv(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/spaces?format=csv")
        assert resp.status_code == 200
        assert "csv" in resp.headers["content-type"]
        text = resp.content.decode("utf-8-sig")
        assert "Этаж" in text

    async def test_export_pdf(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/spaces?format=pdf")
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    async def test_export_walls(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/walls?format=xlsx")
        assert resp.status_code == 200

    async def test_export_issues(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/issues?format=xlsx")
        assert resp.status_code == 200

    async def test_export_invalid_type(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/invalid?format=xlsx")
        assert resp.status_code == 400

    async def test_export_invalid_format(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/spaces?format=docx")
        assert resp.status_code == 400

    async def test_export_nonexistent(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/export/spaces?format=xlsx")
        assert resp.status_code == 404

    async def test_content_disposition_header(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/export/spaces?format=xlsx")
        assert "content-disposition" in resp.headers
        assert "spaces.xlsx" in resp.headers["content-disposition"]
