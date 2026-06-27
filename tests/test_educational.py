"""Tests for Educational Tools module."""

from unittest.mock import MagicMock
import pytest

from src.educational.curriculum_mapper import CurriculumMapper, TimelineExplorer, CitationMiner
from tests.fixtures import MOCK_SEARCH_RESULTS, MOCK_TITLE_DETAILS


@pytest.fixture
def mapper():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return CurriculumMapper(mock_client)


@pytest.fixture
def timeline():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    return TimelineExplorer(mock_client)


@pytest.fixture
def miner():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return CitationMiner(mock_client)


class TestCurriculumMapper:
    def test_map_curriculum_topics_primary(self, mapper):
        topics = mapper.map_curriculum_topics(levels=["Primary"])
        assert len(topics) > 0
        for t in topics:
            assert t.level == "Primary"
            assert t.subject
            assert t.topic
            assert t.suggested_keywords
            assert t.resource_count >= 0

    def test_map_curriculum_topics_secondary(self, mapper):
        topics = mapper.map_curriculum_topics(levels=["Secondary"])
        assert len(topics) > 0
        subjects = set(t.subject for t in topics)
        assert "History" in subjects or "Geography" in subjects

    def test_map_curriculum_topics_default(self, mapper):
        topics = mapper.map_curriculum_topics()
        assert len(topics) > 0

    def test_search_for_lesson(self, mapper):
        results = mapper.search_for_lesson(topic="history", level="Secondary")
        assert len(results) > 0


class TestTimelineExplorer:
    def test_build_timeline(self, timeline):
        nodes = timeline.build_timeline(
            subject="singapore history",
            years=range(2000, 2021, 10),
        )
        assert len(nodes) > 0
        for n in nodes:
            assert n.year >= 2000
            assert n.title
            assert n.source_brn

    def test_event_density_analysis(self, timeline):
        density = timeline.event_density_analysis(subject="singapore")
        assert isinstance(density, list)
        for d in density:
            assert "decade" in d
            assert "publication_count" in d


class TestCitationMiner:
    def test_mine_citations(self, miner):
        citations = miner.mine_citations(keyword="singapore", limit=10)
        assert len(citations) > 0
        for c in citations:
            assert c.title
            assert c.author
            assert c.citation_text
            assert "(" in c.citation_text
            assert ")" in c.citation_text

    def test_citation_format(self, miner):
        citations = miner.mine_citations(keyword="singapore", limit=3)
        for c in citations:
            assert c.year
            assert c.publisher
