"""Tests for quality_checker service."""

from app.services.ifc_parser import ParsedElement
from app.services.quality_checker import check_all, check_element


def _make_element(**kwargs) -> ParsedElement:
    defaults = dict(
        global_id="TEST_001",
        ifc_class="IfcWall",
        name="Test Wall",
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


class TestCheckElement:
    def test_valid_element_no_issues(self):
        el = _make_element()
        issues = check_element(el)
        assert issues == []

    def test_missing_name(self):
        el = _make_element(name=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_name" in categories

    def test_empty_name(self):
        el = _make_element(name="   ")
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_name" in categories

    def test_missing_type(self):
        el = _make_element(type_name=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_type" in categories

    def test_missing_storey(self):
        el = _make_element(storey_name=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_storey" in categories
        severities = [i.severity for i in issues if i.category == "missing_storey"]
        assert severities[0] == "error"

    def test_missing_storey_ignored_for_space(self):
        el = _make_element(ifc_class="IfcSpace", storey_name=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_storey" not in categories

    def test_missing_material_for_wall(self):
        el = _make_element(material=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_material" in categories

    def test_missing_material_ignored_for_door(self):
        el = _make_element(ifc_class="IfcDoor", material=None)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_material" not in categories

    def test_missing_quantities(self):
        el = _make_element(
            length=None, width=None, height=None,
            area=None, volume=None, weight=None,
        )
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "missing_quantities" in categories

    def test_anomaly_small_area(self):
        el = _make_element(area=0.001)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "anomaly_area" in categories

    def test_anomaly_negative_volume(self):
        el = _make_element(volume=-5.0)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "anomaly_volume" in categories

    def test_no_anomaly_for_normal_values(self):
        el = _make_element(area=15.0, volume=4.5)
        issues = check_element(el)
        categories = [i.category for i in issues]
        assert "anomaly_area" not in categories
        assert "anomaly_volume" not in categories


class TestCheckAll:
    def test_check_all_returns_combined_issues(self):
        elements = [
            _make_element(global_id="E1"),
            _make_element(global_id="E2", name=None),
            _make_element(global_id="E3", storey_name=None, material=None),
        ]
        issues = check_all(elements)
        assert len(issues) > 0
        gids = {i.element_global_id for i in issues}
        assert "E2" in gids
        assert "E3" in gids

    def test_check_all_empty_list(self):
        issues = check_all([])
        assert issues == []

    def test_all_valid_elements(self):
        elements = [_make_element(global_id=f"E{i}") for i in range(5)]
        issues = check_all(elements)
        assert issues == []
