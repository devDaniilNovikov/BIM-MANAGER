"""Tests for /api/models/{id}/analytics endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestAnalyticsOverview:
    async def test_overview(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_elements"] == 11
        assert data["total_buildings"] == 1
        assert data["total_storeys"] == 3
        assert data["total_spaces"] == 3
        assert data["total_issues"] == 4
        assert isinstance(data["total_area"], float)
        assert isinstance(data["total_volume"], float)

    async def test_overview_nonexistent(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/analytics/overview")
        assert resp.status_code == 404


class TestAnalyticsByClass:
    async def test_by_class(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/by-class")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        classes = {d["ifc_class"] for d in data}
        assert "IfcWall" in classes
        for item in data:
            assert "count" in item
            assert "total_area" in item
            assert "total_volume" in item

    async def test_sorted_by_count(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/by-class")
        data = resp.json()
        counts = [d["count"] for d in data]
        assert counts == sorted(counts, reverse=True)


class TestAnalyticsByStorey:
    async def test_by_storey(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/by-storey")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for item in data:
            assert "storey_name" in item
            assert "element_count" in item
            assert "problematic_count" in item


class TestAnalyticsIssuesSummary:
    async def test_issues_summary(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/issues-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_severity" in data
        assert "by_status" in data
        assert data["by_severity"].get("error", 0) >= 1
        assert data["by_severity"].get("warning", 0) >= 1


class TestAnalyticsCompleteness:
    async def test_completeness(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/analytics/completeness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 11
        assert "with_name" in data
        assert "with_type" in data
        assert "with_storey" in data
        assert "with_material" in data
        assert "with_quantities" in data
        assert "pct_name" in data
        assert 0 <= data["pct_name"] <= 100

    async def test_completeness_empty_project(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/analytics/completeness")
        data = resp.json()
        assert data["total"] == 0
