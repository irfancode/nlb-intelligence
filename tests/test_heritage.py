"""Tests for Heritage Knowledge Graph module."""

from unittest.mock import MagicMock
import pytest

from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
from src.heritage.entity_extraction import HeritageEntityExtractor
from src.heritage.topic_modeling import TopicModelingEngine
from tests.fixtures import MOCK_SEARCH_RESULTS, MOCK_TITLE_DETAILS


@pytest.fixture
def kg_builder():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return HeritageKnowledgeGraphBuilder(mock_client)


@pytest.fixture
def extractor():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    mock_client.get_title_details.return_value = MOCK_TITLE_DETAILS
    return HeritageEntityExtractor(mock_client)


@pytest.fixture
def topic_engine():
    mock_client = MagicMock()
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS
    return TopicModelingEngine(mock_client)


class TestHeritageKnowledgeGraphBuilder:
    def test_extract_entities_from_titles(self, kg_builder):
        entities = kg_builder.extract_entities_from_titles(
            keywords=["singapore history"]
        )
        assert len(entities) > 0
        names = list(entities.keys())
        assert any("Singapore" in n for n in names)
        assert any("History" in n for n in names)

    def test_build_subject_clusters(self, kg_builder):
        clusters = kg_builder.build_subject_clusters(
            seed_subjects=["History", "Art"]
        )
        assert "History" in clusters or "Art" in clusters
        for seed, related in clusters.items():
            assert len(related) > 0

    def test_build_knowledge_graph(self, kg_builder):
        graph = kg_builder.build_knowledge_graph(
            seed_keywords=["singapore"]
        )
        assert len(graph.entities) > 0
        assert len(graph.relationships) >= 0

    def test_generate_topic_clusters(self, kg_builder):
        clusters = kg_builder.generate_topic_clusters(
            seed_keywords=["singapore", "history"]
        )
        assert len(clusters) > 0
        for c in clusters:
            assert c.name
            assert c.document_count > 0

    def test_temporal_narrative(self, kg_builder):
        narrative = kg_builder.temporal_narrative(subject="singapore")
        assert isinstance(narrative, list)
        for item in narrative:
            assert "year" in item
            assert "title" in item

    def test_extract_temporal_events(self, kg_builder):
        events = kg_builder.extract_temporal_events(
            year_from=2000, year_to=2020
        )
        assert isinstance(events, list)


class TestHeritageEntityExtractor:
    def test_extract_from_search(self, extractor):
        entities = extractor.extract_from_search(
            keywords=["singapore history"]
        )
        assert len(entities) > 0
        for e in entities:
            assert e.text
            assert e.label in ("LOC", "PER", "EVT", "MISC")
            assert e.confidence > 0

    def test_extract_relations(self, extractor):
        relations = extractor.extract_relations(
            seed_keywords=["singapore"]
        )
        assert isinstance(relations, list)


class TestTopicModelingEngine:
    def test_track_topic_over_time(self, topic_engine):
        trends = topic_engine.track_topic_over_time(
            topics=["hawker", "education"]
        )
        assert len(trends) > 0
        for t in trends:
            assert t.topic
            assert t.decade
            assert t.mention_count >= 0

    def test_detect_discursive_shifts(self, topic_engine):
        shifts = topic_engine.detect_discursive_shifts(
            topic="singapore identity"
        )
        assert len(shifts) > 0
        for s in shifts:
            assert s.period_start
            assert s.period_end
            assert s.narrative_description

    def test_cross_collection_topic_map(self, topic_engine):
        topic_map = topic_engine.cross_collection_topic_map(
            subject="singapore"
        )
        for fmt in ["books", "images", "newspapers", "maps", "sound recordings"]:
            assert fmt in topic_map
