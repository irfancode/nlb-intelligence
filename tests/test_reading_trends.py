"""Tests for Reading Trends & Analytics module."""

from unittest.mock import patch, MagicMock
import pytest

from src.analytics.reading_trends import ReadingTrendsAnalyzer
from src.client import NLBApiError
from tests.fixtures import (
    MOCK_CHECKOUT_TRENDS, MOCK_SEARCH_RESULTS, MOCK_LIBRARIES,
    MOCK_TITLE_DETAILS,
)


@pytest.fixture
def analyzer():
    mock_client = MagicMock()
    mock_client.get_checkout_trends.return_value = MOCK_CHECKOUT_TRENDS
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return ReadingTrendsAnalyzer(mock_client)


class TestReadingTrendsAnalyzer:
    def test_analyze_branch_trends(self, analyzer):
        summaries = analyzer.analyze_branch_trends(
            branch_codes=["TRL", "CEN"], duration="past30days"
        )
        assert len(summaries) == 2
        trl_summary = next(s for s in summaries if s.branch_code == "TRL")
        assert trl_summary.total_checkouts > 0
        assert len(trl_summary.top_titles) > 0

    def test_analyze_branch_trends_empty_branch(self, analyzer):
        analyzer._client.get_checkout_trends.side_effect = NLBApiError("No data")
        summaries = analyzer.analyze_branch_trends(branch_codes=["NONEXIST"])
        assert len(summaries) == 0

    def test_cross_branch_comparison(self, analyzer):
        analyzer._client.search_titles.return_value = MOCK_SEARCH_RESULTS[:3]
        result = analyzer.cross_branch_comparison(
            keyword="singapore", branches=["TRL", "CEN"]
        )
        assert "TRL" in result
        assert "CEN" in result
        assert len(result["TRL"]) > 0

    def test_genre_popularity_by_branch(self, analyzer):
        result = analyzer.genre_popularity_by_branch(
            duration="past30days", branches=["TRL"]
        )
        assert "TRL" in result
        genres = result["TRL"]
        assert len(genres) > 0
        assert genres[0].genre in MOCK_TITLE_DETAILS.subjects

    def test_demographic_reading_profile_adult(self, analyzer):
        analyzer._client.search_titles.return_value = MOCK_SEARCH_RESULTS[:4]
        from src.models import Audience
        profile = analyzer.demographic_reading_profile(
            audience=Audience.ADULT
        )
        assert profile.audience == Audience.ADULT
        assert len(profile.preferred_genres) > 0
        assert len(profile.format_preference) > 0
        assert len(profile.language_distribution) > 0

    def test_demographic_reading_profile_no_results(self, analyzer):
        analyzer._client.search_titles.side_effect = NLBApiError("No results")
        from src.models import Audience
        profile = analyzer.demographic_reading_profile(
            audience=Audience.CHILDREN
        )
        assert profile.audience == Audience.CHILDREN
