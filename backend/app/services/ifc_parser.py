"""IFC file parser using ifcopenshell.

Extracts spatial structure, elements, properties and quantities from an IFC model.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as element_util

logger = logging.getLogger(__name__)

# IFC classes we consider "building elements"
ELEMENT_CLASSES = (
    "IfcWall", "IfcWallStandardCase",
    "IfcSlab", "IfcRoof",
    "IfcColumn", "IfcBeam",
    "IfcDoor", "IfcWindow",
    "IfcStair", "IfcStairFlight",
    "IfcRailing",
    "IfcCurtainWall",
    "IfcPlate",
    "IfcMember",
    "IfcCovering",
    "IfcFurnishingElement",
    "IfcBuildingElementProxy",
    "IfcOpeningElement",
    "IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting",
    "IfcDistributionElement",
    "IfcSpace",
)


@dataclass
class ParsedSpace:
    global_id: str
    name: str | None = None
    long_name: str | None = None
    area: float | None = None
    volume: float | None = None


@dataclass
class ParsedStorey:
    global_id: str
    name: str | None = None
    elevation: float | None = None
    spaces: list[ParsedSpace] = field(default_factory=list)


@dataclass
class ParsedBuilding:
    global_id: str
    name: str | None = None
    description: str | None = None
    storeys: list[ParsedStorey] = field(default_factory=list)


@dataclass
class ParsedElement:
    global_id: str
    ifc_class: str
    name: str | None = None
    type_name: str | None = None
    description: str | None = None
    material: str | None = None
    storey_name: str | None = None
    space_name: str | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    area: float | None = None
    volume: float | None = None
    weight: float | None = None
    properties: dict = field(default_factory=dict)


@dataclass
class ParsedModel:
    schema: str
    buildings: list[ParsedBuilding] = field(default_factory=list)
    elements: list[ParsedElement] = field(default_factory=list)


def _safe_float(value) -> float | None:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        v = float(value)
        return v if v != 0.0 else None
    except (ValueError, TypeError):
        return None


def _get_material_name(element) -> str | None:
    """Extract material name from an IFC element."""
    try:
        materials = element_util.get_material(element)
        if materials is None:
            return None
        # Single material
        if hasattr(materials, "Name"):
            return materials.Name
        # Material layer set
        if hasattr(materials, "MaterialLayers"):
            names = [ml.Material.Name for ml in materials.MaterialLayers if ml.Material and ml.Material.Name]
            return "; ".join(names) if names else None
        # Material list
        if hasattr(materials, "Materials"):
            names = [m.Name for m in materials.Materials if m.Name]
            return "; ".join(names) if names else None
        return str(materials) if materials else None
    except Exception:
        return None


def _get_quantities(element) -> dict[str, float | None]:
    """Extract BaseQuantities from element."""
    result = {"length": None, "width": None, "height": None, "area": None, "volume": None, "weight": None}
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcElementQuantity"):
                    for q in pset.Quantities:
                        qname = (q.Name or "").lower()
                        if "length" in qname:
                            result["length"] = result["length"] or _safe_float(getattr(q, "LengthValue", None))
                        elif "width" in qname:
                            result["width"] = result["width"] or _safe_float(getattr(q, "LengthValue", None))
                        elif "height" in qname:
                            result["height"] = result["height"] or _safe_float(getattr(q, "LengthValue", None))
                        elif "area" in qname or "surface" in qname:
                            result["area"] = result["area"] or _safe_float(getattr(q, "AreaValue", None))
                        elif "volume" in qname:
                            result["volume"] = result["volume"] or _safe_float(getattr(q, "VolumeValue", None))
                        elif "weight" in qname or "mass" in qname:
                            result["weight"] = result["weight"] or _safe_float(getattr(q, "WeightValue", None))
    except Exception as e:
        logger.debug(f"Error extracting quantities: {e}")
    return result


def _get_property_sets(element) -> dict:
    """Extract all property sets as a dict of dicts."""
    result = {}
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet"):
                    pset_name = pset.Name or "UnnamedPset"
                    props = {}
                    for prop in pset.HasProperties:
                        if prop.is_a("IfcPropertySingleValue"):
                            val = prop.NominalValue
                            props[prop.Name] = str(val.wrappedValue) if val else None
                    if props:
                        result[pset_name] = props
    except Exception as e:
        logger.debug(f"Error extracting properties: {e}")
    return result


def _get_storey_name(element) -> str | None:
    """Find the storey an element belongs to."""
    try:
        container = element_util.get_container(element)
        if container and container.is_a("IfcBuildingStorey"):
            return container.Name
        # Walk up
        for rel in getattr(element, "ContainedInStructure", []):
            if rel.RelatingStructure.is_a("IfcBuildingStorey"):
                return rel.RelatingStructure.Name
    except Exception:
        pass
    return None


def _get_space_name(element) -> str | None:
    """Find the space an element is in (if any)."""
    try:
        for rel in getattr(element, "ContainedInStructure", []):
            if rel.RelatingStructure.is_a("IfcSpace"):
                return rel.RelatingStructure.Name or rel.RelatingStructure.LongName
    except Exception:
        pass
    return None


def _get_type_name(element) -> str | None:
    """Get the type object name."""
    try:
        etype = element_util.get_type(element)
        if etype:
            return etype.Name
    except Exception:
        pass
    return None


def parse_ifc(file_path: str | Path) -> ParsedModel:
    """Parse an IFC file and extract all data needed by the system.

    Returns a ParsedModel with spatial structure and elements.
    """
    path = Path(file_path)
    logger.info(f"Parsing IFC file: {path}")
    ifc = ifcopenshell.open(str(path))
    schema = ifc.schema

    # ── Spatial structure ────────────────────────────
    buildings: list[ParsedBuilding] = []
    for bld in ifc.by_type("IfcBuilding"):
        pb = ParsedBuilding(
            global_id=bld.GlobalId,
            name=bld.Name,
            description=bld.Description,
        )
        for storey in ifc.by_type("IfcBuildingStorey"):
            # Check storey belongs to this building
            ps = ParsedStorey(
                global_id=storey.GlobalId,
                name=storey.Name,
                elevation=_safe_float(storey.Elevation),
            )
            # Spaces within storey
            for rel in getattr(storey, "IsDecomposedBy", []):
                for obj in rel.RelatedObjects:
                    if obj.is_a("IfcSpace"):
                        area = None
                        volume = None
                        qts = _get_quantities(obj)
                        area = qts.get("area")
                        volume = qts.get("volume")
                        ps.spaces.append(ParsedSpace(
                            global_id=obj.GlobalId,
                            name=obj.Name,
                            long_name=getattr(obj, "LongName", None),
                            area=area,
                            volume=volume,
                        ))
            pb.storeys.append(ps)
        buildings.append(pb)

    # ── Elements ─────────────────────────────────────
    elements: list[ParsedElement] = []
    processed_ids: set[str] = set()

    for cls in ELEMENT_CLASSES:
        for el in ifc.by_type(cls):
            gid = el.GlobalId
            if gid in processed_ids:
                continue
            processed_ids.add(gid)

            quantities = _get_quantities(el)
            props = _get_property_sets(el)

            pe = ParsedElement(
                global_id=gid,
                ifc_class=el.is_a(),
                name=el.Name,
                type_name=_get_type_name(el),
                description=el.Description,
                material=_get_material_name(el),
                storey_name=_get_storey_name(el),
                space_name=_get_space_name(el),
                length=quantities["length"],
                width=quantities["width"],
                height=quantities["height"],
                area=quantities["area"],
                volume=quantities["volume"],
                weight=quantities["weight"],
                properties=props,
            )
            elements.append(pe)

    logger.info(f"Parsed {len(buildings)} buildings, {len(elements)} elements")
    return ParsedModel(schema=schema, buildings=buildings, elements=elements)
