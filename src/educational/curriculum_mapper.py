"""
Educational & Research Tools.

Maps NLB catalogue subjects to Singapore MOE curriculum topics for
lesson-plan-aligned resource discovery, provides a timeline explorer for
digital humanities research, and enables citation mining across collections.
"""

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

from src.client import NLBClient, NLBApiError
from src.models import TitleSearchResult


@dataclass
class CurriculumTopic:
    level: str
    subject: str
    topic: str
    suggested_keywords: list[str]
    recommended_titles: list[TitleSearchResult] = field(default_factory=list)
    resource_count: int = 0


@dataclass
class TimelineNode:
    year: int
    title: str
    event_type: str
    description: str
    source_brn: str
    related_subjects: list[str]


@dataclass
class Citation:
    title: str
    author: str
    publisher: str
    year: str
    subjects: list[str]
    citation_text: str
    source_url: str


class CurriculumMapper:
    def __init__(self, client: NLBClient):
        self._client = client

    _curriculum_map: dict[str, list[dict]] = {
        "Primary": [
            {"subject": "English", "topics": ["storytelling", "children's literature", "poetry for children"]},
            {"subject": "Mathematics", "topics": ["mathematics", "counting", "shapes", "puzzles"]},
            {"subject": "Science", "topics": ["science for children", "nature", "animals", "plants"]},
            {"subject": "Social Studies", "topics": ["singapore", "community", "family", "maps for children"]},
            {"subject": "Mother Tongue", "topics": ["chinese children", "malay children", "tamil children"]},
        ],
        "Secondary": [
            {"subject": "English Literature", "topics": ["fiction", "drama", "poetry", "short stories"]},
            {"subject": "History", "topics": ["singapore history", "world war ii", "southeast asia"]},
            {"subject": "Geography", "topics": ["geography", "climate", "environment", "urban planning"]},
            {"subject": "Science", "topics": ["biology", "chemistry", "physics", "science experiments"]},
        ],
        "Junior College": [
            {"subject": "General Paper", "topics": ["current affairs", "social issues", "economics", "politics"]},
            {"subject": "Literature", "topics": ["literary criticism", "world literature", "postcolonial"]},
            {"subject": "History", "topics": ["international history", "cold war", "globalisation"]},
        ],
    }

    def map_curriculum_topics(
        self, levels: list[str] | None = None
    ) -> list[CurriculumTopic]:
        if levels is None:
            levels = ["Primary", "Secondary"]
        results: list[CurriculumTopic] = []
        for level in levels:
            for entry in self._curriculum_map.get(level, []):
                subject = entry["subject"]
                for topic_kw in entry["topics"]:
                    try:
                        titles = self._client.search_titles(
                            keywords=topic_kw,
                            audiences=["children"] if level == "Primary" else ["youth", "adult"],
                            limit=10,
                        )
                    except NLBApiError:
                        titles = []
                    results.append(
                        CurriculumTopic(
                            level=level,
                            subject=subject,
                            topic=topic_kw.capitalize(),
                            suggested_keywords=[topic_kw, f"{topic_kw} {level.lower()}", f"learn {topic_kw}"],
                            recommended_titles=titles,
                            resource_count=len(titles),
                        )
                    )
        return results

    def search_for_lesson(
        self, topic: str, level: str = "Secondary"
    ) -> list[TitleSearchResult]:
        audience = "children" if level == "Primary" else "youth"
        try:
            return self._client.search_titles(
                keywords=topic,
                audiences=[audience],
                limit=20,
            )
        except NLBApiError:
            return []


class TimelineExplorer:
    def __init__(self, client: NLBClient):
        self._client = client

    def build_timeline(
        self, subject: str = "singapore history", years: range | None = None
    ) -> list[TimelineNode]:
        if years is None:
            years = range(1800, 2025, 10)
        nodes: list[TimelineNode] = []
        for year in years:
            try:
                titles = self._client.search_titles(
                    keywords=subject,
                    date_from=str(year),
                    date_to=str(min(year + 9, 2025)),
                    limit=5,
                )
            except NLBApiError:
                continue
            for t in titles:
                if t.title and t.brn:
                    nodes.append(
                        TimelineNode(
                            year=year,
                            title=t.title,
                            event_type="Publication",
                            description=" | ".join(t.subjects[:3]) if t.subjects else subject,
                            source_brn=t.brn,
                            related_subjects=t.subjects,
                        )
                    )
        return nodes

    def event_density_analysis(
        self, subject: str = "singapore"
    ) -> list[dict]:
        try:
            titles = self._client.search_titles(keywords=subject, limit=100)
        except NLBApiError:
            return []
        decade_counts: defaultdict = defaultdict(int)
        for t in titles:
            for y in range(1800, 2030, 10):
                if str(y) in t.publish_date:
                    decade_counts[y] += 1
                    break
        return [
            {"decade": decade, "publication_count": count}
            for decade, count in sorted(decade_counts.items())
        ]


class CitationMiner:
    def __init__(self, client: NLBClient):
        self._client = client

    def mine_citations(
        self, keyword: str, limit: int = 20
    ) -> list[Citation]:
        try:
            titles = self._client.search_titles(keywords=keyword, limit=limit)
        except NLBApiError:
            return []
        citations: list[Citation] = []
        for t in titles:
            if not t.brn:
                continue
            try:
                detail = self._client.get_title_details(brn=t.brn)
            except NLBApiError:
                detail = None
            author = t.author or (detail.authors[0] if detail and detail.authors else "Unknown")
            year = t.publish_date or (detail.publish_date if detail else "")
            publisher = detail.publisher if detail else ""
            subjects = t.subjects or (detail.subjects if detail else [])

            citation_text = f"{author} ({year}). {t.title}. {publisher}."

            citations.append(
                Citation(
                    title=t.title,
                    author=author,
                    publisher=publisher,
                    year=year,
                    subjects=subjects,
                    citation_text=citation_text,
                    source_url=f"https://catalogue.nlb.gov.sg/search/{t.brn}" if t.brn else "",
                )
            )
        return citations
