"""Tests for /api/models/{id}/tree, buildings, storeys, spaces endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestGetTree:
    async def test_tree_structure(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/tree")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_name"] == "Test Project"
        assert len(data["buildings"]) == 1
        building = data["buildings"][0]
        assert building["name"] == "Корпус А"
        assert len(building["storeys"]) == 3
        assert len(building["storeys"][0]["spaces"]) == 3

    async def test_tree_nonexistent(self, client: AsyncClient):
        resp = await client.get(f"/api/models/{uuid.uuid4()}/tree")
        assert resp.status_code == 404


class TestListBuildings:
    async def test_list_buildings(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/buildings")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Корпус А"
        assert data[0]["global_id"] == "BUILDING_001"


class TestListStoreys:
    async def test_list_storeys(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/storeys")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # Ordered by elevation
        elevations = [s["elevation"] for s in data]
        assert elevations == sorted(elevations)

    async def test_storey_has_spaces(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/storeys")
        data = resp.json()
        floor1 = data[0]
        assert len(floor1["spaces"]) == 3


class TestListSpaces:
    async def test_list_spaces(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/spaces")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = {s["long_name"] for s in data}
        assert "Прихожая" in names
        assert "Кухня" in names
