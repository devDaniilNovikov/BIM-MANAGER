"""Tests for /api/qc-rules endpoints."""

import json
import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestListRules:
    async def test_empty_list(self, client: AsyncClient):
        resp = await client.get("/api/qc-rules")
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateRule:
    async def test_create_basic_rule(self, client: AsyncClient):
        resp = await client.post("/api/qc-rules", json={
            "name": "Стены должны иметь IsExternal",
            "description": "Проверка наличия свойства IsExternal у стен",
            "ifc_class": "IfcWall",
            "check_type": "required_property",
            "check_config": json.dumps({"pset": "Pset_WallCommon", "property": "IsExternal"}),
            "severity": "warning",
            "is_active": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Стены должны иметь IsExternal"
        assert data["ifc_class"] == "IfcWall"
        assert data["check_type"] == "required_property"
        assert data["is_active"] is True
        assert data["id"] is not None

    async def test_create_value_range_rule(self, client: AsyncClient):
        resp = await client.post("/api/qc-rules", json={
            "name": "Площадь стены в допустимом диапазоне",
            "ifc_class": "IfcWall",
            "check_type": "value_range",
            "check_config": json.dumps({"attribute": "area", "min": 0.1, "max": 500}),
            "severity": "error",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["check_type"] == "value_range"
        assert data["severity"] == "error"

    async def test_create_has_storey_rule(self, client: AsyncClient):
        resp = await client.post("/api/qc-rules", json={
            "name": "Все элементы привязаны к этажу",
            "ifc_class": "*",
            "check_type": "has_storey",
            "severity": "warning",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ifc_class"] == "*"


class TestGetRule:
    async def test_get_existing(self, client: AsyncClient):
        # Create a rule first
        create_resp = await client.post("/api/qc-rules", json={
            "name": "Test Rule",
            "check_type": "has_storey",
        })
        rule_id = create_resp.json()["id"]

        resp = await client.get(f"/api/qc-rules/{rule_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Rule"

    async def test_get_nonexistent(self, client: AsyncClient):
        resp = await client.get(f"/api/qc-rules/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateRule:
    async def test_update_name(self, client: AsyncClient):
        create_resp = await client.post("/api/qc-rules", json={
            "name": "Old Name",
            "check_type": "has_storey",
        })
        rule_id = create_resp.json()["id"]

        resp = await client.put(f"/api/qc-rules/{rule_id}", json={
            "name": "New Name",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_deactivate_rule(self, client: AsyncClient):
        create_resp = await client.post("/api/qc-rules", json={
            "name": "Active Rule",
            "check_type": "has_storey",
            "is_active": True,
        })
        rule_id = create_resp.json()["id"]

        resp = await client.put(f"/api/qc-rules/{rule_id}", json={
            "is_active": False,
        })
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_update_nonexistent(self, client: AsyncClient):
        resp = await client.put(f"/api/qc-rules/{uuid.uuid4()}", json={"name": "X"})
        assert resp.status_code == 404


class TestDeleteRule:
    async def test_delete_existing(self, client: AsyncClient):
        create_resp = await client.post("/api/qc-rules", json={
            "name": "To Delete",
            "check_type": "has_storey",
        })
        rule_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/qc-rules/{rule_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        # Verify it's gone
        resp2 = await client.get(f"/api/qc-rules/{rule_id}")
        assert resp2.status_code == 404

    async def test_delete_nonexistent(self, client: AsyncClient):
        resp = await client.delete(f"/api/qc-rules/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestRulesListAfterCRUD:
    async def test_rules_appear_in_list(self, client: AsyncClient):
        await client.post("/api/qc-rules", json={
            "name": "Rule A",
            "check_type": "has_storey",
        })
        await client.post("/api/qc-rules", json={
            "name": "Rule B",
            "check_type": "value_range",
            "check_config": json.dumps({"attribute": "area", "min": 1}),
        })

        resp = await client.get("/api/qc-rules")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = {r["name"] for r in data}
        assert "Rule A" in names
        assert "Rule B" in names

