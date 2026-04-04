"""Tests for /api/models/{id}/elements endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestListElements:
    async def test_list_all(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 11  # 11 elements in fixture
        assert data["page"] == 1
        assert len(data["items"]) == 11

    async def test_filter_by_class(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?ifc_class=IfcWall")
        data = resp.json()
        assert data["total"] == 3
        for item in data["items"]:
            assert item["ifc_class"] == "IfcWall"

    async def test_filter_by_storey(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?storey_name=Этаж 1")
        data = resp.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["storey_name"] == "Этаж 1"

    async def test_filter_has_issues(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?has_issues=true")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["is_problematic"] is True

    async def test_search(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?search=Дверь")
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert "Дверь" in item["name"]

    async def test_pagination(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?page=1&page_size=3")
        data = resp.json()
        assert data["total"] == 11
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["items"]) == 3

    async def test_pagination_page2(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements?page=2&page_size=5")
        data = resp.json()
        assert len(data["items"]) == 5

    async def test_empty_project(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/elements")
        data = resp.json()
        assert data["total"] == 0


class TestGetElement:
    async def test_get_existing(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Element

        result = await db.execute(
            select(Element).where(Element.project_id == sample_project.id).limit(1)
        )
        elem = result.scalar_one()

        resp = await client.get(f"/api/models/{sample_project.id}/elements/{elem.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["global_id"] == elem.global_id

    async def test_get_nonexistent(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/elements/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestElementClasses:
    async def test_element_classes(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/element-classes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        classes = {d["ifc_class"] for d in data}
        assert "IfcWall" in classes
        assert "IfcDoor" in classes
        # Check counts
        for item in data:
            assert item["count"] > 0

    async def test_element_classes_sorted_by_count(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/element-classes")
        data = resp.json()
        counts = [d["count"] for d in data]
        assert counts == sorted(counts, reverse=True)
