"""BIM Document Manager — FastAPI application."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import projects, upload, structure, elements, reports, export, analytics, quality, issues, qc_rules

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(upload.router, prefix="/api/models", tags=["Upload"])
app.include_router(structure.router, prefix="/api/models", tags=["Structure"])
app.include_router(elements.router, prefix="/api/models", tags=["Elements"])
app.include_router(reports.router, prefix="/api/models", tags=["Reports"])
app.include_router(export.router, prefix="/api/models", tags=["Export"])
app.include_router(analytics.router, prefix="/api/models", tags=["Analytics"])
app.include_router(quality.router, prefix="/api/models", tags=["Quality"])
app.include_router(issues.router, prefix="/api/models", tags=["Issues"])
app.include_router(qc_rules.router, prefix="/api/qc-rules", tags=["QC Rules"])


@app.on_event("startup")
async def on_startup():
    from app.core.database import engine, Base
    from app.models.project import Project, Building, Storey, Space, Element, Issue, QCRule  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
