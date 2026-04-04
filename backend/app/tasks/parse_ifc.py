"""Celery task for async IFC parsing."""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.tasks.celery_app import celery_app
from app.services.ifc_parser import parse_ifc
from app.services.quality_checker import check_all
from app.services.anomaly_detector import detect_anomalies

logger = logging.getLogger(__name__)


def _get_sync_session() -> Session:
    """Create a sync database session for Celery tasks."""
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://bim:bimpass@localhost:5432/bim_system")
    # Replace asyncpg with psycopg2 for sync access
    sync_url = db_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql+psycopg2")
    if "psycopg2" not in sync_url:
        sync_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, name="parse_ifc_task")
def parse_ifc_task(self, project_id: str, file_path: str):
    """Parse IFC file in background and store results in DB."""
    from app.models.project import Building, Element, Issue, Project, Space, Storey

    logger.info(f"Starting IFC parse for project {project_id}: {file_path}")
    self.update_state(state="PARSING", meta={"progress": 0})

    try:
        parsed = parse_ifc(file_path)
        self.update_state(state="PARSING", meta={"progress": 50})

        db = _get_sync_session()
        try:
            pid = uuid.UUID(project_id)
            project = db.get(Project, pid)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            project.ifc_schema = parsed.schema

            # Store spatial structure
            for pb in parsed.buildings:
                building = Building(
                    project_id=pid,
                    global_id=pb.global_id,
                    name=pb.name,
                    description=pb.description,
                )
                db.add(building)
                db.flush()

                for ps in pb.storeys:
                    storey = Storey(
                        building_id=building.id,
                        global_id=ps.global_id,
                        name=ps.name,
                        elevation=ps.elevation,
                    )
                    db.add(storey)
                    db.flush()

                    for psp in ps.spaces:
                        space = Space(
                            storey_id=storey.id,
                            global_id=psp.global_id,
                            name=psp.name,
                            long_name=psp.long_name,
                            area=psp.area,
                            volume=psp.volume,
                        )
                        db.add(space)

            self.update_state(state="PARSING", meta={"progress": 70})

            # Store elements
            gid_to_elem = {}
            for pe in parsed.elements:
                has_quantities = any([pe.length, pe.width, pe.height, pe.area, pe.volume, pe.weight])
                elem = Element(
                    project_id=pid,
                    global_id=pe.global_id,
                    ifc_class=pe.ifc_class,
                    name=pe.name,
                    type_name=pe.type_name,
                    description=pe.description,
                    material=pe.material,
                    storey_name=pe.storey_name,
                    space_name=pe.space_name,
                    length=pe.length,
                    width=pe.width,
                    height=pe.height,
                    area=pe.area,
                    volume=pe.volume,
                    weight=pe.weight,
                    has_name=bool(pe.name),
                    has_type=bool(pe.type_name),
                    has_storey=bool(pe.storey_name),
                    has_material=bool(pe.material),
                    has_quantities=has_quantities,
                    properties_json=json.dumps(pe.properties, ensure_ascii=False) if pe.properties else None,
                )
                db.add(elem)
                gid_to_elem[pe.global_id] = elem

            db.flush()
            self.update_state(state="PARSING", meta={"progress": 85})

            # Quality checks
            quality_issues = check_all(parsed.elements)
            anomaly_issues = detect_anomalies(parsed.elements)
            all_issues = quality_issues + anomaly_issues

            for qi in all_issues:
                elem = gid_to_elem.get(qi.element_global_id)
                if elem:
                    elem.is_problematic = True
                issue = Issue(
                    project_id=pid,
                    element_id=elem.id if elem else None,
                    issue_type=qi.issue_type,
                    severity=qi.severity,
                    category=qi.category,
                    title=qi.title,
                    message=qi.message,
                    recommendation=qi.recommendation,
                )
                db.add(issue)

            db.commit()
            self.update_state(state="PARSING", meta={"progress": 100})

            return {
                "status": "success",
                "elements": len(parsed.elements),
                "issues": len(all_issues),
            }

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Failed to parse IFC: {e}")
        raise
