"""Tests for Checkout Analysis module."""

from unittest.mock import MagicMock
import pytest

from src.analytics.checkout_analysis import CirculationAnalyzer
from tests.fixtures import (
    MOCK_CHECKOUT_TRENDS, MOCK_LIBRARIES, MOCK_TITLE_DETAILS,
    MOCK_SEARCH_RESULTS,
)


@pytest.fixture
def analyzer():
    mock_client = MagicMock()
    mock_client.get_checkout_trends.return_value = MOCK_CHECKOUT_TRENDS
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS[:3]
    return CirculationAnalyzer(mock_client)


class TestCirculationAnalyzer:
    def test_compute_circulation_metrics(self, analyzer):
        metrics = analyzer.compute_circulation_metrics(
            branch_codes=["TRL", "WRL", "CEN"]
        )
        assert metrics.total_checkouts_period > 0
        assert metrics.unique_titles_checked > 0
        assert metrics.avg_checkouts_per_title > 0
        assert metrics.branch_with_highest_volume

    def test_compute_circulation_metrics_no_data(self, analyzer):
        analyzer._client.get_checkout_trends.return_value = []
        metrics = analyzer.compute_circulation_metrics(
            branch_codes=["NONEXIST"]
        )
        assert metrics.total_checkouts_period == 0

    def test_compare_branches(self, analyzer):
        comparisons = analyzer.compare_branches(
            branch_codes=["TRL", "WRL", "CEN"]
        )
        assert len(comparisons) > 0
        for c in comparisons:
            assert c.branch_code
            assert c.total_checkouts > 0
            assert c.collection_size_estimate > 0
            assert c.turnover_rate > 0
        # Should be sorted by checkouts descending
        assert comparisons[0].total_checkouts >= comparisons[-1].total_checkouts

    def test_seasonal_patterns(self, analyzer):
        patterns = analyzer.seasonal_patterns()
        assert len(patterns) == 4
        months = [p.month for p in patterns]
        assert "June" in months
        assert "December" in months
        for p in patterns:
            assert p.peak_genre
            assert p.holiday_spike > 0

    def test_reservation_heatmap(self, analyzer):
        analyzer._client.get_title_details.return_value = MOCK_TITLE_DETAILS
        hot_items = analyzer.reservation_heatmap(
            keywords=["bestseller", "popular"]
        )
        assert isinstance(hot_items, list)

    def test_reservation_heatmap_no_results(self, analyzer):
        analyzer._client.search_titles.return_value = []
        hot_items = analyzer.reservation_heatmap(
            keywords=["nonexistent"]
        )
        assert len(hot_items) == 0
