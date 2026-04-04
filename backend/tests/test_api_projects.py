"""Tests for /api/projects endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class TestListProjects:
    async def test_empty_list(self, client: AsyncClient):
        resp = await client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_project(self, client: AsyncClient, sample_project: Project):
        resp = await client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"
        assert data[0]["file_name"] == "test_model.ifc"
        assert "element_count" in data[0]
        assert "issue_count" in data[0]


class TestGetProject:
    async def test_get_existing(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"
        assert "buildings" in data

    async def test_get_nonexistent(self, client: AsyncClient):
        resp = await client.get(f"/api/projects/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_get_includes_spatial_structure(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/projects/{sample_project.id}")
        data = resp.json()
        assert len(data["buildings"]) == 1
        building = data["buildings"][0]
        assert building["name"] == "Корпус А"
        assert len(building["storeys"]) == 3
        storey = building["storeys"][0]
        assert len(storey["spaces"]) == 3


class TestDeleteProject:
    async def test_delete_existing(self, client: AsyncClient, sample_project: Project):
        resp = await client.delete(f"/api/projects/{sample_project.id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        # Verify it's gone
        resp2 = await client.get(f"/api/projects/{sample_project.id}")
        assert resp2.status_code == 404

    async def test_delete_nonexistent(self, client: AsyncClient):
        resp = await client.delete(f"/api/projects/{uuid.uuid4()}")
        assert resp.status_code == 404
