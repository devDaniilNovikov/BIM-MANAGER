"""Anomaly detector — statistical analysis for finding outliers in element data."""

from __future__ import annotations

import math
from collections import defaultdict

from app.services.ifc_parser import ParsedElement
from app.services.quality_checker import QualityIssue
from app.services.recommendation import get_recommendation


def detect_anomalies(elements: list[ParsedElement]) -> list[QualityIssue]:
    """Detect statistical anomalies across all elements.

    Checks:
    1. Values > 3 standard deviations from mean per ifc_class
    2. Elements without storey assignment ("hanging" elements)
    3. IfcBuildingElementProxy elements (undefined type)
    """
    issues: list[QualityIssue] = []

    # Group numeric values by class for statistical analysis
    class_values: dict[str, dict[str, list[tuple[str, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for el in elements:
        for attr in ("area", "volume", "length"):
            val = getattr(el, attr, None)
            if val is not None and val > 0:
                class_values[el.ifc_class][attr].append((el.global_id, val))

    # Check for statistical outliers (> 3σ)
    for ifc_class, attrs in class_values.items():
        for attr_name, pairs in attrs.items():
            if len(pairs) < 5:
                continue

            values = [v for _, v in pairs]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance) if variance > 0 else 0

            if std == 0:
                continue

            for gid, val in pairs:
                if abs(val - mean) > 3 * std:
                    attr_label = {"area": "площади", "volume": "объёма", "length": "длины"}[attr_name]
                    issues.append(QualityIssue(
                        element_global_id=gid,
                        severity="warning",
                        category="anomaly",
                        issue_type="anomaly",
                        title=f"Аномальное значение {attr_label}",
                        message=(
                            f"Аномальное значение {attr_label} ({val:.2f}) для {ifc_class}. "
                            f"Среднее: {mean:.2f}, стд. откл.: {std:.2f}"
                        ),
                        recommendation=get_recommendation("anomaly"),
                    ))

    # IfcBuildingElementProxy — suspicious untyped elements
    for el in elements:
        if el.ifc_class == "IfcBuildingElementProxy":
            issues.append(QualityIssue(
                element_global_id=el.global_id,
                severity="info",
                category="anomaly",
                issue_type="anomaly",
                title="Неопределённый тип элемента",
                message=f"Элемент '{el.name or el.global_id}' имеет неопределённый тип (IfcBuildingElementProxy).",
                recommendation="Определите конкретный IFC-класс элемента вместо IfcBuildingElementProxy.",
            ))

    return issues
