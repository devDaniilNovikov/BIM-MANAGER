"""Quality control service.

Checks elements for completeness and correctness, generates issues.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.services.ifc_parser import ParsedElement
from app.services.recommendation import get_recommendation


@dataclass
class QualityIssue:
    element_global_id: str
    severity: str  # error / warning / info
    category: str
    message: str
    issue_type: str = "missing_property"
    title: str | None = None
    recommendation: str | None = None


# Elements that must have quantities
REQUIRES_QUANTITIES = {
    "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn", "IfcBeam",
    "IfcDoor", "IfcWindow", "IfcRoof", "IfcStair",
}

# Elements that should have material
REQUIRES_MATERIAL = {
    "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn", "IfcBeam",
    "IfcRoof", "IfcCovering", "IfcPlate", "IfcMember",
}


def check_element(el: ParsedElement) -> list[QualityIssue]:
    """Run all quality checks on a single element."""
    issues: list[QualityIssue] = []
    gid = el.global_id

    # 1. Missing name
    if not el.name or not el.name.strip():
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="warning",
            category="missing_name",
            issue_type="missing_property",
            title="Элемент без имени",
            message=f"Element {el.ifc_class} ({gid}) has no name.",
            recommendation=get_recommendation("missing_name"),
        ))

    # 2. Missing type
    if not el.type_name:
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="warning",
            category="missing_type",
            issue_type="missing_property",
            title="Элемент без типа",
            message=f"Element '{el.name or gid}' has no type definition.",
            recommendation=get_recommendation("missing_type"),
        ))

    # 3. Missing storey assignment
    if not el.storey_name and el.ifc_class != "IfcSpace":
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="error",
            category="missing_storey",
            issue_type="no_storey",
            title="Элемент без этажа",
            message=f"Element '{el.name or gid}' ({el.ifc_class}) is not assigned to any storey.",
            recommendation=get_recommendation("missing_storey"),
        ))

    # 4. Missing material
    if el.ifc_class in REQUIRES_MATERIAL and not el.material:
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="warning",
            category="missing_material",
            issue_type="missing_property",
            title="Нет материала",
            message=f"Element '{el.name or gid}' ({el.ifc_class}) has no material assigned.",
            recommendation=get_recommendation("missing_material"),
        ))

    # 5. Missing quantities
    if el.ifc_class in REQUIRES_QUANTITIES:
        has_any = any([el.length, el.width, el.height, el.area, el.volume, el.weight])
        if not has_any:
            issues.append(QualityIssue(
                element_global_id=gid,
                severity="error",
                category="missing_quantities",
                issue_type="missing_property",
                title="Нет количеств",
                message=f"Element '{el.name or gid}' ({el.ifc_class}) has no quantity data.",
                recommendation=get_recommendation("missing_quantities"),
            ))

    # 6. Suspicious zero-area walls/slabs
    if el.ifc_class in ("IfcWall", "IfcWallStandardCase", "IfcSlab") and el.area is not None and el.area < 0.01:
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="warning",
            category="anomaly_area",
            issue_type="anomaly",
            title="Аномальная площадь",
            message=f"Element '{el.name or gid}' has suspiciously small area: {el.area}.",
            recommendation=get_recommendation("anomaly_area"),
        ))

    # 7. Anomalous volume
    if el.volume is not None and el.volume < 0:
        issues.append(QualityIssue(
            element_global_id=gid,
            severity="error",
            category="anomaly_volume",
            issue_type="anomaly",
            title="Отрицательный объём",
            message=f"Element '{el.name or gid}' has negative volume: {el.volume}.",
            recommendation=get_recommendation("anomaly_volume"),
        ))

    return issues


def check_with_custom_rules(elements: list[ParsedElement], rules: list[dict]) -> list[QualityIssue]:
    """Apply user-defined QC rules to elements.

    Each rule dict has: name, ifc_class ('*' = all), check_type, check_config (JSON), severity.
    Supported check_types:
      - required_property: check_config = {"pset": "Pset_WallCommon", "property": "IsExternal"}
      - value_range: check_config = {"attribute": "area", "min": 0.1, "max": 10000}
      - has_quantity: check_config = {"quantity": "area"}  (area/volume/length/width/height)
      - has_storey: no config needed
    """
    issues: list[QualityIssue] = []

    for rule in rules:
        if not rule.get("is_active", True):
            continue
        rule_ifc_class = rule.get("ifc_class", "*")
        check_type = rule.get("check_type")
        severity = rule.get("severity", "warning")
        config_raw = rule.get("check_config")
        config = json.loads(config_raw) if config_raw else {}

        for el in elements:
            if rule_ifc_class != "*" and el.ifc_class != rule_ifc_class:
                continue

            issue = _apply_custom_rule(el, rule, check_type, config, severity)
            if issue:
                issues.append(issue)

    return issues


def _apply_custom_rule(
    el: ParsedElement,
    rule: dict,
    check_type: str,
    config: dict,
    severity: str,
) -> QualityIssue | None:
    gid = el.global_id
    rule_name = rule.get("name", "Custom rule")

    if check_type == "required_property":
        pset = config.get("pset", "")
        prop = config.get("property", "")
        if pset and prop:
            pset_data = el.properties.get(pset, {})
            if prop not in pset_data or not pset_data[prop]:
                return QualityIssue(
                    element_global_id=gid,
                    severity=severity,
                    category="missing_property",
                    issue_type="missing_property",
                    title=rule_name,
                    message=f"Element '{el.name or gid}' missing property {pset}.{prop}.",
                    recommendation=f"Добавьте свойство {prop} в набор {pset}.",
                )

    elif check_type == "value_range":
        attr = config.get("attribute", "area")
        min_val = config.get("min")
        max_val = config.get("max")
        val = getattr(el, attr, None)
        if val is not None:
            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                return QualityIssue(
                    element_global_id=gid,
                    severity=severity,
                    category="invalid_value",
                    issue_type="invalid_value",
                    title=rule_name,
                    message=f"Element '{el.name or gid}' {attr}={val} outside range [{min_val}, {max_val}].",
                    recommendation=f"Проверьте значение {attr} элемента.",
                )

    elif check_type == "has_quantity":
        qty = config.get("quantity", "area")
        val = getattr(el, qty, None)
        if val is None:
            return QualityIssue(
                element_global_id=gid,
                severity=severity,
                category="missing_quantities",
                issue_type="missing_property",
                title=rule_name,
                message=f"Element '{el.name or gid}' has no {qty} quantity.",
                recommendation=f"Добавьте количественную характеристику {qty}.",
            )

    elif check_type == "has_storey":
        if not el.storey_name:
            return QualityIssue(
                element_global_id=gid,
                severity=severity,
                category="missing_storey",
                issue_type="no_storey",
                title=rule_name,
                message=f"Element '{el.name or gid}' is not assigned to a storey.",
                recommendation=get_recommendation("missing_storey"),
            )

    return None


def check_all(elements: list[ParsedElement]) -> list[QualityIssue]:
    """Run quality checks on all elements."""
    all_issues: list[QualityIssue] = []
    for el in elements:
        all_issues.extend(check_element(el))
    return all_issues
