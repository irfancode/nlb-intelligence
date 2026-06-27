"""Tests for Collection Gap Analysis module."""

from unittest.mock import patch, MagicMock
import pytest

from src.analytics.collection_gaps import CollectionGapAnalyzer
from src.client import NLBApiError
from tests.fixtures import MOCK_SEARCH_RESULTS


@pytest.fixture
def analyzer():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS[:3]
    return CollectionGapAnalyzer(mock_client)


class TestCollectionGapAnalyzer:
    def test_identify_gaps(self, analyzer):
        gaps = analyzer.identify_gaps(
            high_demand_keywords=["artificial intelligence", "history"],
            branches=["TRL", "WRL"],
        )
        assert len(gaps) == 2
        assert any(g.subject == "artificial intelligence" for g in gaps)
        assert any(g.subject == "history" for g in gaps)
        for g in gaps:
            assert g.gap_severity in ("high", "medium", "low")
            assert g.suggested_action

    def test_identify_gaps_all_high_demand(self, analyzer):
        analyzer._client.search_titles.return_value = []
        gaps = analyzer.identify_gaps(
            high_demand_keywords=["rare topic", "obscure subject"],
        )
        assert len(gaps) == 2
        for g in gaps:
            assert g.demand_score > 0.5
            assert g.gap_severity == "high"

    def test_language_distribution_analysis(self, analyzer):
        analyzer._client.search_titles.return_value = MOCK_SEARCH_RESULTS
        dist = analyzer.language_distribution_analysis(
            branches=["TRL", "WRL"],
            sample_keywords=["fiction", "history"],
        )
        assert len(dist) > 0
        assert any(d.language == "English" for d in dist)
        assert any(d.language == "Malay" for d in dist)

    def test_format_trend_analysis(self, analyzer):
        analyzer._client.search_titles.return_value = MOCK_SEARCH_RESULTS
        trends = analyzer.format_trend_analysis(
            sample_keywords=["popular", "new"]
        )
        assert len(trends) > 0
        assert all(t.material_type for t in trends)
        assert all(t.turnover_rate > 0 for t in trends)

    def test_underserved_demographics_report(self, analyzer):
        report = analyzer.underserved_demographics_report()
        assert "under_represented_subjects" in report
        assert "suggestions" in report
        assert "format_opportunities" in report
        assert len(report["under_represented_subjects"]) > 0
        assert len(report["suggestions"]) > 0
