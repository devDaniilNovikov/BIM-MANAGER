"""Tests for custom QC rules engine (check_with_custom_rules)."""

import json

from app.services.ifc_parser import ParsedElement
from app.services.quality_checker import check_with_custom_rules


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
        properties={"Pset_WallCommon": {"IsExternal": "True", "LoadBearing": "True"}},
    )
    defaults.update(kwargs)
    return ParsedElement(**defaults)


class TestRequiredProperty:
    def test_property_exists_no_issue(self):
        el = _make_element()
        rules = [{
            "name": "Check IsExternal",
            "ifc_class": "IfcWall",
            "check_type": "required_property",
            "check_config": json.dumps({"pset": "Pset_WallCommon", "property": "IsExternal"}),
            "severity": "warning",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert issues == []

    def test_property_missing(self):
        el = _make_element(properties={"Pset_WallCommon": {"LoadBearing": "True"}})
        rules = [{
            "name": "Check IsExternal",
            "ifc_class": "IfcWall",
            "check_type": "required_property",
            "check_config": json.dumps({"pset": "Pset_WallCommon", "property": "IsExternal"}),
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert issues[0].title == "Check IsExternal"

    def test_pset_missing(self):
        el = _make_element(properties={})
        rules = [{
            "name": "Check Prop",
            "ifc_class": "IfcWall",
            "check_type": "required_property",
            "check_config": json.dumps({"pset": "Pset_WallCommon", "property": "IsExternal"}),
            "severity": "warning",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1


class TestValueRange:
    def test_in_range_no_issue(self):
        el = _make_element(area=15.0)
        rules = [{
            "name": "Area check",
            "ifc_class": "IfcWall",
            "check_type": "value_range",
            "check_config": json.dumps({"attribute": "area", "min": 0.1, "max": 500}),
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert issues == []

    def test_below_min(self):
        el = _make_element(area=0.001)
        rules = [{
            "name": "Area check",
            "ifc_class": "IfcWall",
            "check_type": "value_range",
            "check_config": json.dumps({"attribute": "area", "min": 0.1, "max": 500}),
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1
        assert issues[0].issue_type == "invalid_value"

    def test_above_max(self):
        el = _make_element(area=999.0)
        rules = [{
            "name": "Area check",
            "ifc_class": "IfcWall",
            "check_type": "value_range",
            "check_config": json.dumps({"attribute": "area", "min": 0.1, "max": 500}),
            "severity": "warning",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1


class TestHasQuantity:
    def test_quantity_present_no_issue(self):
        el = _make_element(area=15.0)
        rules = [{
            "name": "Must have area",
            "ifc_class": "*",
            "check_type": "has_quantity",
            "check_config": json.dumps({"quantity": "area"}),
            "severity": "warning",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert issues == []

    def test_quantity_missing(self):
        el = _make_element(volume=None)
        rules = [{
            "name": "Must have volume",
            "ifc_class": "*",
            "check_type": "has_quantity",
            "check_config": json.dumps({"quantity": "volume"}),
            "severity": "warning",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1


class TestHasStorey:
    def test_storey_present_no_issue(self):
        el = _make_element(storey_name="Floor 1")
        rules = [{
            "name": "Must have storey",
            "ifc_class": "*",
            "check_type": "has_storey",
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert issues == []

    def test_storey_missing(self):
        el = _make_element(storey_name=None)
        rules = [{
            "name": "Must have storey",
            "ifc_class": "*",
            "check_type": "has_storey",
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([el], rules)
        assert len(issues) == 1
        assert issues[0].issue_type == "no_storey"


class TestClassFilter:
    def test_rule_applied_only_to_matching_class(self):
        wall = _make_element(global_id="W1", ifc_class="IfcWall", storey_name=None)
        door = _make_element(global_id="D1", ifc_class="IfcDoor", storey_name=None)
        rules = [{
            "name": "Walls need storey",
            "ifc_class": "IfcWall",
            "check_type": "has_storey",
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([wall, door], rules)
        assert len(issues) == 1
        assert issues[0].element_global_id == "W1"

    def test_wildcard_applies_to_all(self):
        wall = _make_element(global_id="W1", ifc_class="IfcWall", storey_name=None)
        door = _make_element(global_id="D1", ifc_class="IfcDoor", storey_name=None)
        rules = [{
            "name": "All need storey",
            "ifc_class": "*",
            "check_type": "has_storey",
            "severity": "error",
            "is_active": True,
        }]
        issues = check_with_custom_rules([wall, door], rules)
        assert len(issues) == 2


class TestInactiveRule:
    def test_inactive_rule_skipped(self):
        el = _make_element(storey_name=None)
        rules = [{
            "name": "Inactive",
            "ifc_class": "*",
            "check_type": "has_storey",
            "severity": "error",
            "is_active": False,
        }]
        issues = check_with_custom_rules([el], rules)
        assert issues == []

