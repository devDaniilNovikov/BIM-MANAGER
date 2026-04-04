"""Tests for /api/models/{id}/issues endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project


class TestListIssues:
    async def test_list_all(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    async def test_filter_by_severity(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues?severity=error")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["severity"] == "error"

    async def test_filter_by_status(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues?status=open")
        data = resp.json()
        assert data["total"] == 4
        for item in data["items"]:
            assert item["status"] == "open"

    async def test_filter_by_category(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues?category=missing_name")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["category"] == "missing_name"

    async def test_filter_by_issue_type(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues?issue_type=anomaly")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["issue_type"] == "anomaly"

    async def test_pagination(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues?page=1&page_size=2")
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestCreateIssue:
    async def test_create_manual_issue(self, client: AsyncClient, sample_project: Project):
        resp = await client.post(
            f"/api/models/{sample_project.id}/issues",
            json={
                "issue_type": "manual",
                "severity": "warning",
                "category": "manual",
                "title": "Ручное замечание",
                "message": "Ручное замечание от пользователя",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "manual"
        assert data["issue_type"] == "manual"
        assert data["title"] == "Ручное замечание"
        assert data["message"] == "Ручное замечание от пользователя"
        assert data["recommendation"] is not None  # auto-filled
        assert data["status"] == "open"
        assert data["id"] is not None

    async def test_create_issue_with_element(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Element

        result = await db.execute(
            select(Element).where(Element.project_id == sample_project.id).limit(1)
        )
        elem = result.scalar_one()

        resp = await client.post(
            f"/api/models/{sample_project.id}/issues",
            json={
                "element_id": str(elem.id),
                "issue_type": "manual",
                "severity": "error",
                "category": "manual",
                "message": "Проблема с элементом",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["element_id"] == str(elem.id)


class TestGetIssue:
    async def test_get_existing(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Issue

        result = await db.execute(
            select(Issue).where(Issue.project_id == sample_project.id).limit(1)
        )
        issue = result.scalar_one()

        resp = await client.get(f"/api/models/{sample_project.id}/issues/{issue.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(issue.id)

    async def test_get_nonexistent(self, client: AsyncClient, sample_project: Project):
        resp = await client.get(f"/api/models/{sample_project.id}/issues/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateIssue:
    async def test_update_status(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Issue

        result = await db.execute(
            select(Issue).where(Issue.project_id == sample_project.id).limit(1)
        )
        issue = result.scalar_one()

        resp = await client.put(
            f"/api/models/{sample_project.id}/issues/{issue.id}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    async def test_update_message(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Issue

        result = await db.execute(
            select(Issue).where(Issue.project_id == sample_project.id).limit(1)
        )
        issue = result.scalar_one()

        resp = await client.put(
            f"/api/models/{sample_project.id}/issues/{issue.id}",
            json={"message": "Обновлённое описание"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Обновлённое описание"

    async def test_update_nonexistent(self, client: AsyncClient, sample_project: Project):
        resp = await client.put(
            f"/api/models/{sample_project.id}/issues/{uuid.uuid4()}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 404


class TestDeleteIssue:
    async def test_delete_existing(self, client: AsyncClient, sample_project: Project, db):
        from sqlalchemy import select
        from app.models.project import Issue

        result = await db.execute(
            select(Issue).where(Issue.project_id == sample_project.id).limit(1)
        )
        issue = result.scalar_one()

        resp = await client.delete(f"/api/models/{sample_project.id}/issues/{issue.id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    async def test_delete_nonexistent(self, client: AsyncClient, sample_project: Project):
        resp = await client.delete(f"/api/models/{sample_project.id}/issues/{uuid.uuid4()}")
        assert resp.status_code == 404
