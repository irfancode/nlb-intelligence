"""Tests for Geospatial Intelligence module."""

from unittest.mock import MagicMock
import pytest

from src.geospatial.catchment_analysis import GeospatialIntelligence
from tests.fixtures import MOCK_LIBRARIES


@pytest.fixture
def geo():
    mock_client = MagicMock()
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    return GeospatialIntelligence(mock_client)


class TestGeospatialIntelligence:
    def test_compute_catchment_areas(self, geo):
        areas = geo.compute_catchment_areas(radius_km=2.0)
        assert len(areas) == len(MOCK_LIBRARIES)
        for a in areas:
            assert a.branch_code
            assert a.distance_to_nearest > 0
            assert a.estimated_population_served > 0
            assert isinstance(a.overlapping_branches, list)

    def test_accessibility_audit(self, geo):
        scores = geo.accessibility_audit()
        assert len(scores) == len(MOCK_LIBRARIES)
        for s in scores:
            assert 0 <= s.overall_accessibility <= 1
            assert 0 <= s.walkability_index <= 1
            assert 0 <= s.public_transport_access <= 1

    def test_suggest_new_locations(self, geo):
        suggestions = geo.suggest_new_locations()
        assert len(suggestions) == 4
        for s in suggestions:
            assert s.proposed_area
            assert s.priority in ("High", "Medium", "Low")
            assert s.rationale

    def test_branch_clustering(self, geo):
        clusters = geo.branch_clustering()
        assert len(clusters) > 0
        for cluster_name, branches in clusters.items():
            assert len(branches) > 0

    def test_coverage_heatmap_data(self, geo):
        heatmap = geo.coverage_heatmap_data()
        assert len(heatmap) == len(MOCK_LIBRARIES)
        for h in heatmap:
            assert "lat" in h
            assert "lon" in h
            assert h["radius_covers_km"] == 2.0

    def test_no_libraries(self, geo):
        geo._client.get_libraries.return_value = []
        areas = geo.compute_catchment_areas()
        assert len(areas) == 0

    def test_haversine_same_point(self, geo):
        dist = geo._haversine(1.352, 103.945, 1.352, 103.945)
        assert dist == 0.0

    def test_haversine_known_distance(self, geo):
        # TRL to CEN approximate distance
        dist = geo._haversine(1.352, 103.945, 1.297, 103.853)
        assert 8 < dist < 15  # roughly 11km
