"""Tests for upload routes after removing Redis/Celery async flow."""

from httpx import AsyncClient


class TestUploadRoutes:
    async def test_upload_async_endpoint_removed(self, client: AsyncClient):
        response = await client.post("/api/models/upload-async")
        assert response.status_code == 404

    async def test_task_status_endpoint_removed(self, client: AsyncClient):
        response = await client.get("/api/models/task/some-task-id")
        assert response.status_code == 404

