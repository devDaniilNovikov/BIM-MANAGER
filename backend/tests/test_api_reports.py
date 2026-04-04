"""Tests for /api/models/{id}/reports endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestGetReport:
    async def test_spaces_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/spaces")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Ведомость помещений"
        assert len(data["columns"]) > 0
        assert len(data["rows"]) == 3

    async def test_doors_windows_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/doors-windows")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rows"]) == 4

    async def test_walls_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/walls")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rows"]) == 3

    async def test_slabs_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/slabs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rows"]) == 2

    async def test_quantities_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/quantities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rows"]) > 0

    async def test_summary_report(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "sections" in data

    async def test_invalid_report_type(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/reports/nonexistent")
        assert resp.status_code == 400

    async def test_nonexistent_project(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/reports/spaces")
        assert resp.status_code == 404
