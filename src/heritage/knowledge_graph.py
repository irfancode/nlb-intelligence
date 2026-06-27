"""
Singapore Cultural Heritage Knowledge Graph.

Transforms NLB's 230K+ digitised records (books, images, maps, manuscripts,
newspapers, sound recordings) into an interconnected knowledge graph for
entity extraction, topic modeling, and temporal-spatial discovery.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional
import re

from src.client import NLBClient, NLBApiError
from src.models import TitleDetail, EResource, CollectionRecord


@dataclass
class Entity:
    name: str
    entity_type: str
    mentions: int = 0
    related_entities: list[str] = field(default_factory=list)
    source_brns: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class TemporalEvent:
    year: int
    title: str
    description: str
    related_subjects: list[str] = field(default_factory=list)
    source_digital_ids: list[str] = field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class KnowledgeGraph:
    entities: dict[str, Entity] = field(default_factory=dict)
    relationships: list[tuple[str, str, str]] = field(default_factory=list)
    temporal_events: list[TemporalEvent] = field(default_factory=list)
    subject_clusters: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class TopicCluster:
    name: str
    keywords: list[str]
    document_count: int
    avg_date: str
    related_clusters: list[str]


class HeritageKnowledgeGraphBuilder:
    def __init__(self, client: NLBClient):
        self._client = client
        self.graph = KnowledgeGraph()

    def extract_entities_from_titles(
        self, keywords: list[str] | None = None
    ) -> dict[str, Entity]:
        if keywords is None:
            keywords = [
                "singapore history", "singapore culture", "singapore人物",
                "singapura", "temasek", "lee kuan yew", "merdeka",
                "national day", "chinese migration", "malay heritage",
                "tamil literature", "peranakan", "kampong",
            ]

        entities: dict[str, Entity] = {}

        for kw in keywords:
            try:
                titles = self._client.search_titles(keywords=kw, limit=30)
                for t in titles:
                    if not t.brn:
                        continue
                    try:
                        detail = self._client.get_title_details(brn=t.brn)
                    except NLBApiError:
                        continue
                    if not detail:
                        continue

                    if detail.subjects:
                        for subject in detail.subjects:
                            clean = subject.strip()
                            if clean not in entities:
                                etype = self._classify_entity(clean)
                                entities[clean] = Entity(
                                    name=clean, entity_type=etype
                                )
                            entities[clean].mentions += 1
                            if t.brn not in entities[clean].source_brns:
                                entities[clean].source_brns.append(t.brn)

                    if detail.authors:
                        for author in detail.authors:
                            author_clean = author.strip()
                            if author_clean not in entities:
                                entities[author_clean] = Entity(
                                    name=author_clean,
                                    entity_type="Person",
                                )
                            entities[author_clean].mentions += 1
                            if t.brn not in entities[author_clean].source_brns:
                                entities[author_clean].source_brns.append(t.brn)
            except NLBApiError:
                continue

        return dict(sorted(entities.items(), key=lambda e: e[1].mentions, reverse=True)[:200])

    def _classify_entity(self, name: str) -> str:
        location_keywords = [
            "singapore", "malaysia", "asia", "island", "river", "street",
            "hill", "park", "garden", "harbour", "bay", "town", "village",
        ]
        person_keywords = [
            "people", "人物", "biography", "autobiography", "memoir",
        ]
        event_keywords = [
            "history", "war", "celebration", "festival", "day", "parade",
            "independence", "formation", "establishment",
        ]
        name_lower = name.lower()
        if any(kw in name_lower for kw in location_keywords):
            return "Location"
        if any(kw in name_lower for kw in person_keywords):
            return "Person"
        if any(kw in name_lower for kw in event_keywords):
            return "Event"
        return "Topic"

    def build_subject_clusters(
        self, seed_subjects: list[str] | None = None
    ) -> dict[str, list[str]]:
        if seed_subjects is None:
            seed_subjects = [
                "Art", "Architecture", "Music", "Literature", "Theatre",
                "History", "Politics", "Economics",
                "Science", "Technology", "Medicine",
                "Nature", "Environment", "Geography",
                "Religion", "Philosophy", "Education",
                "Cooking", "Sport", "Fashion",
            ]
        clusters: dict[str, list[str]] = {}
        for seed in seed_subjects:
            related: list[str] = []
            try:
                titles = self._client.search_titles(keywords=seed, limit=20)
                for t in titles:
                    if t.subjects:
                        for s in t.subjects:
                            if s.lower() != seed.lower() and s not in related:
                                related.append(s)
            except NLBApiError:
                continue
            clusters[seed] = related[:15]
        return clusters

    def extract_temporal_events(
        self, year_from: int = 1800, year_to: int = 2025
    ) -> list[TemporalEvent]:
        events: list[TemporalEvent] = []
        decades = list(range(year_from, year_to + 1, 10))
        for decade in decades:
            try:
                titles = self._client.search_titles(
                    keywords="singapore history",
                    date_from=str(decade),
                    date_to=str(min(decade + 9, year_to)),
                    limit=10,
                )
                for t in titles:
                    if t.subjects:
                        events.append(
                            TemporalEvent(
                                year=decade,
                                title=t.title,
                                description=" | ".join(t.subjects[:3]),
                                related_subjects=t.subjects,
                                source_digital_ids=[t.brn] if t.brn else [],
                            )
                        )
            except NLBApiError:
                continue
        return events

    def build_knowledge_graph(
        self,
        seed_keywords: list[str] | None = None,
    ) -> KnowledgeGraph:
        entities = self.extract_entities_from_titles(seed_keywords)
        self.graph.entities = entities

        subject_clusters = self.build_subject_clusters()
        self.graph.subject_clusters = subject_clusters

        relationships: list[tuple[str, str, str]] = []
        for subject, related in subject_clusters.items():
            for rel in related:
                relationships.append((subject, "related_to", rel))
        self.graph.relationships = relationships

        self.graph.temporal_events = self.extract_temporal_events()

        return self.graph

    def generate_topic_clusters(
        self, seed_keywords: list[str] | None = None
    ) -> list[TopicCluster]:
        if seed_keywords is None:
            seed_keywords = [
                "singapore", "history", "culture", "arts",
                "economy", "society", "heritage",
            ]
        clusters: list[TopicCluster] = []
        for kw in seed_keywords:
            try:
                titles = self._client.search_titles(keywords=kw, limit=30)
            except NLBApiError:
                continue
            if not titles:
                continue
            all_subjects: list[str] = []
            for t in titles:
                if t.subjects:
                    all_subjects.extend(t.subjects)
            top_keywords = [s for s, _ in Counter(all_subjects).most_common(8)]
            clusters.append(
                TopicCluster(
                    name=f"{kw.capitalize()} Collection",
                    keywords=top_keywords,
                    document_count=len(titles),
                    avg_date="Various",
                    related_clusters=[s for s in seed_keywords if s != kw][:3],
                )
            )
        return clusters

    def temporal_narrative(
        self, subject: str = "singapore"
    ) -> list[dict]:
        try:
            titles = self._client.search_titles(keywords=subject, limit=100)
        except NLBApiError:
            return []
        narrative: list[dict] = []
        for t in titles:
            year_match = re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", t.publish_date)
            if year_match:
                narrative.append({
                    "year": int(year_match.group(1)),
                    "title": t.title,
                    "author": t.author,
                    "subject": subject,
                })
        return sorted(narrative, key=lambda x: x["year"])[:50]
