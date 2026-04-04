"""Tests for anomaly_detector service."""

from app.services.anomaly_detector import detect_anomalies
from app.services.ifc_parser import ParsedElement


def _make_element(**kwargs) -> ParsedElement:
    defaults = dict(
        global_id="TEST_001",
        ifc_class="IfcWall",
        name="Wall",
        type_name="WT-01",
        description=None,
        material="Brick",
        storey_name="Floor 1",
        space_name=None,
        length=5.0,
        width=0.3,
        height=3.0,
        area=15.0,
        volume=4.5,
        weight=None,
        properties={},
    )
    defaults.update(kwargs)
    return ParsedElement(**defaults)


class TestDetectAnomalies:
    def test_no_anomalies_in_uniform_data(self):
        elements = [_make_element(global_id=f"E{i}", area=15.0) for i in range(10)]
        issues = detect_anomalies(elements)
        anomaly_issues = [i for i in issues if i.category == "anomaly" and "Аномальное" in i.message]
        assert anomaly_issues == []

    def test_detects_statistical_outlier(self):
        # 20 normal walls + 1 extreme outlier — ensures outlier exceeds 3σ
        elements = [_make_element(global_id=f"E{i}", area=15.0) for i in range(20)]
        elements.append(_make_element(global_id="OUTLIER", area=1500.0))
        issues = detect_anomalies(elements)
        outlier_issues = [i for i in issues if i.element_global_id == "OUTLIER" and "площади" in i.message]
        assert len(outlier_issues) == 1
        assert outlier_issues[0].severity == "warning"
        assert outlier_issues[0].issue_type == "anomaly"
        assert outlier_issues[0].recommendation is not None

    def test_detects_proxy_elements(self):
        elements = [
            _make_element(global_id="PROXY1", ifc_class="IfcBuildingElementProxy", name="Unknown"),
        ]
        issues = detect_anomalies(elements)
        proxy_issues = [i for i in issues if i.element_global_id == "PROXY1"]
        assert len(proxy_issues) >= 1
        assert any("IfcBuildingElementProxy" in i.message for i in proxy_issues)

    def test_empty_list(self):
        issues = detect_anomalies([])
        assert issues == []

    def test_skips_classes_with_few_elements(self):
        # Less than 5 elements — no statistical analysis
        elements = [_make_element(global_id=f"E{i}", area=15.0) for i in range(3)]
        elements.append(_make_element(global_id="BIG", area=999.0))
        issues = detect_anomalies(elements)
        stat_issues = [i for i in issues if "Аномальное" in i.message]
        assert stat_issues == []

    def test_multiple_attributes_checked(self):
        # Outlier in volume — 20 normal + 1 extreme
        elements = [_make_element(global_id=f"E{i}", volume=4.5) for i in range(20)]
        elements.append(_make_element(global_id="VOL_OUT", volume=500.0))
        issues = detect_anomalies(elements)
        vol_issues = [i for i in issues if i.element_global_id == "VOL_OUT" and "объёма" in i.message]
        assert len(vol_issues) == 1
        assert vol_issues[0].issue_type == "anomaly"
