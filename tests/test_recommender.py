"""Tests for Hybrid Recommendation Engine module."""

from unittest.mock import MagicMock
import pytest

from src.recommendations.hybrid_recommender import HybridRecommender, UserPreferences
from tests.fixtures import MOCK_SEARCH_RESULTS, MOCK_RECOMMENDATIONS, MOCK_TITLE_DETAILS


@pytest.fixture
def recommender():
    mock_client = MagicMock()
    mock_client.get_recommendations.return_value = MOCK_RECOMMENDATIONS
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return HybridRecommender(mock_client)


class TestHybridRecommender:
    def test_recommend_by_keyword(self, recommender):
        recs = recommender.recommend_by_keyword(keyword="singapore", limit=10)
        assert len(recs) > 0
        for r in recs:
            assert r.title
            assert r.score > 0
            assert r.source in ("NLB Recommendation API", "Catalogue Search API")

    def test_recommend_by_keyword_deduplicates(self, recommender):
        same_rec = MOCK_RECOMMENDATIONS[0]
        recommender._client.get_recommendations.return_value = [same_rec] * 3
        recs = recommender.recommend_by_keyword(keyword="test")
        brns = [r.brn for r in recs]
        assert len(set(brns)) == len(brns)

    def test_recommend_by_seed_brn(self, recommender):
        recs = recommender.recommend_by_seed(seed_brn="BRN123456", limit=10)
        assert len(recs) > 0
        for r in recs:
            assert r.score > 0

    def test_recommend_by_seed_isbn(self, recommender):
        recs = recommender.recommend_by_seed(seed_isbn="9789811234567", limit=10)
        assert isinstance(recs, list)

    def test_trending_recommendations(self, recommender):
        from src.client import CheckoutTrend
        recommender._client.get_checkout_trends.return_value = [
            CheckoutTrend(brn="BRN123", title="Trending Book",
                          checkout_count=50, branch_code="TRL",
                          branch_name="Tampines", period="past30days"),
        ]
        recs = recommender.trending_recommendations(branch_code="TRL")
        assert len(recs) > 0
        assert recs[0].score > 0

    def test_personalized_for_user(self, recommender):
        prefs = UserPreferences(
            favourite_genres=["History", "Singapore"],
            favourite_authors=["Mark Frost"],
            preferred_languages=["English"],
            preferred_formats=["BOOK"],
        )
        recs = recommender.personalized_for_user(preferences=prefs, limit=10)
        assert len(recs) > 0

    def test_diverse_discovery(self, recommender):
        recs = recommender.diverse_discovery(limit=10)
        assert len(recs) > 0
        topics_found = set(r.reason for r in recs)
        assert len(topics_found) > 0
