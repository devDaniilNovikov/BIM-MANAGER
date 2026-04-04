"""Shared fixtures for all tests.

Uses in-memory SQLite for fast, isolated DB testing.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.models.project import Building, Element, Issue, Project, QCRule, Space, Storey

# SQLite async engine for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)

    # Enable FK support for SQLite
    @event.listens_for(eng.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await eng.dispose()


@pytest.fixture()
async def db(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
async def client(engine):
    """AsyncClient that uses test DB."""
    from app.main import app

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Factory fixtures ────────────────────────────────────


@pytest.fixture()
async def sample_project(db: AsyncSession) -> Project:
    """Create a sample project with spatial structure and elements."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="Test description",
        file_name="test_model.ifc",
        file_path="/tmp/test_model.ifc",
        file_size=1024000,
        ifc_schema="IFC4",
    )
    db.add(project)
    await db.flush()

    building = Building(
        id=uuid.uuid4(),
        project_id=project.id,
        global_id="BUILDING_001",
        name="Корпус А",
        description="Основной корпус",
    )
    db.add(building)
    await db.flush()

    storeys = []
    for i, (name, elev) in enumerate([("Этаж 1", 0.0), ("Этаж 2", 3.3), ("Этаж 3", 6.6)]):
        storey = Storey(
            id=uuid.uuid4(),
            building_id=building.id,
            global_id=f"STOREY_{i+1:03d}",
            name=name,
            elevation=elev,
        )
        db.add(storey)
        storeys.append(storey)
    await db.flush()

    # Spaces on floor 1
    for j, (sname, area, vol) in enumerate([
        ("Прихожая", 12.5, 37.5),
        ("Кухня", 15.0, 45.0),
        ("Гостиная", 25.0, 75.0),
    ]):
        space = Space(
            id=uuid.uuid4(),
            storey_id=storeys[0].id,
            global_id=f"SPACE_{j+1:03d}",
            name=f"Помещение {j+1}",
            long_name=sname,
            area=area,
            volume=vol,
        )
        db.add(space)
    await db.flush()

    # Elements — walls, doors, windows, slabs
    elements_data = [
        ("IfcWall", "Стена наружная 1", "СТ-01", "Кирпич", storeys[0].name, 5.0, None, 3.0, 15.0, 3.75, None),
        ("IfcWall", "Стена наружная 2", "СТ-01", "Кирпич", storeys[0].name, 8.0, None, 3.0, 24.0, 6.0, None),
        ("IfcWall", None, None, None, None, None, None, None, None, None, None),  # problematic: no name, no storey
        ("IfcDoor", "Дверь Д-01", "ДВ-01", "Дерево", storeys[0].name, None, 0.9, 2.1, 1.89, None, None),
        ("IfcDoor", "Дверь Д-02", "ДВ-02", "Металл", storeys[1].name, None, 1.0, 2.1, 2.1, None, None),
        ("IfcWindow", "Окно О-01", "ОК-01", "ПВХ", storeys[0].name, None, 1.5, 1.5, 2.25, None, None),
        ("IfcWindow", "Окно О-02", "ОК-01", "ПВХ", storeys[1].name, None, 1.5, 1.5, 2.25, None, None),
        ("IfcSlab", "Перекрытие 1", "ПК-01", "Бетон", storeys[0].name, None, None, 0.22, 100.0, 22.0, None),
        ("IfcSlab", "Перекрытие 2", "ПК-01", "Бетон", storeys[1].name, None, None, 0.22, 100.0, 22.0, None),
        ("IfcColumn", "Колонна К-01", "КОЛ-01", "Бетон", storeys[0].name, 3.3, 0.4, 0.4, 0.64, 0.528, 1320.0),
        ("IfcBuildingElementProxy", "Неизвестный объект", None, None, storeys[0].name, None, None, None, None, None, None),
    ]

    props_sample = {"Pset_WallCommon": {"IsExternal": "True", "LoadBearing": "True"}}

    for idx, (cls, name, tname, mat, sname, length, width, height, area, volume, weight) in enumerate(elements_data):
        has_q = any(v is not None for v in [length, width, height, area, volume, weight])
        elem = Element(
            id=uuid.uuid4(),
            project_id=project.id,
            global_id=f"ELEM_{idx+1:03d}",
            ifc_class=cls,
            name=name,
            type_name=tname,
            material=mat,
            storey_name=sname,
            space_name=None,
            length=length,
            width=width,
            height=height,
            area=area,
            volume=volume,
            weight=weight,
            has_name=bool(name),
            has_type=bool(tname),
            has_storey=bool(sname),
            has_material=bool(mat),
            has_quantities=has_q,
            is_problematic=(name is None),
            properties_json=json.dumps(props_sample, ensure_ascii=False) if cls == "IfcWall" and name else None,
        )
        db.add(elem)
    await db.flush()

    # A few issues
    issues_data = [
        ("error", "no_storey", "missing_storey", "Элемент без этажа", "Элемент не привязан к этажу"),
        ("warning", "missing_property", "missing_name", "Элемент без имени", "Отсутствует наименование элемента"),
        ("warning", "missing_property", "missing_material", "Нет материала", "Не указан материал"),
        ("info", "anomaly", "anomaly", "Неопределённый тип", "IfcBuildingElementProxy — неопределённый тип"),
    ]
    for sev, itype, cat, title, msg in issues_data:
        issue = Issue(
            id=uuid.uuid4(),
            project_id=project.id,
            element_id=None,
            issue_type=itype,
            severity=sev,
            category=cat,
            title=title,
            message=msg,
            recommendation="Проверьте элемент в BIM-модели.",
            status="open",
        )
        db.add(issue)

    await db.flush()
    await db.commit()
    return project
