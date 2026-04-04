"""Tests for recommendation service."""

from app.services.recommendation import get_recommendation, RECOMMENDATIONS


class TestGetRecommendation:
    def test_known_categories(self):
        for category in RECOMMENDATIONS:
            rec = get_recommendation(category)
            assert isinstance(rec, str)
            assert len(rec) > 10

    def test_missing_name(self):
        rec = get_recommendation("missing_name")
        assert "наименование" in rec.lower() or "name" in rec.lower()

    def test_missing_storey(self):
        rec = get_recommendation("missing_storey")
        assert "этаж" in rec.lower()

    def test_missing_material(self):
        rec = get_recommendation("missing_material")
        assert "материал" in rec.lower()

    def test_missing_quantities(self):
        rec = get_recommendation("missing_quantities")
        assert "BaseQuantities" in rec or "количеств" in rec.lower()

    def test_unknown_category_returns_default(self):
        rec = get_recommendation("unknown_category_xyz")
        assert isinstance(rec, str)
        assert len(rec) > 5

    def test_anomaly(self):
        rec = get_recommendation("anomaly")
        assert "отклонение" in rec.lower() or "проверьте" in rec.lower()
