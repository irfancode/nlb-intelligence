"""
Topic Modeling across NLB's Digital Newspaper and Magazine Collections.

Analyses thematic patterns across decades using catalogue subject metadata,
tracking how topics like "hawker culture" or "national identity" evolved
in Singapore's published discourse.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional

from src.client import NLBClient, NLBApiError


@dataclass
class TopicTrend:
    topic: str
    decade: str
    mention_count: int
    related_subjects: list[str]
    sentiment_direction: str


@dataclass
class DiscursiveShift:
    topic: str
    period_start: str
    period_end: str
    frequency_change: float
    narrative_description: str


class TopicModelingEngine:
    def __init__(self, client: NLBClient):
        self._client = client

    def track_topic_over_time(
        self, topics: list[str] | None = None
    ) -> list[TopicTrend]:
        if topics is None:
            topics = [
                "hawker", "housing", "education", "transport",
                "multiculturalism", "national service", "economy",
                "environment", "heritage", "technology",
            ]
        trends: list[TopicTrend] = []
        decades = ["1960", "1970", "1980", "1990", "2000", "2010", "2020"]

        for topic in topics:
            for decade in decades:
                decade_end = str(int(decade) + 9)
                try:
                    titles = self._client.search_titles(
                        keywords=topic,
                        date_from=decade,
                        date_to=decade_end,
                        limit=20,
                    )
                except NLBApiError:
                    continue
                if titles:
                    all_subjects: list[str] = []
                    for t in titles:
                        if t.subjects:
                            all_subjects.extend(t.subjects)
                    trends.append(
                        TopicTrend(
                            topic=topic,
                            decade=decade,
                            mention_count=len(titles),
                            related_subjects=[s for s, _ in Counter(all_subjects).most_common(5)],
                            sentiment_direction=self._estimate_sentiment(topic, decade),
                        )
                    )
        return trends

    def _estimate_sentiment(self, topic: str, decade: str) -> str:
        positive_decades = {"2020": ["technology", "environment"], "2010": ["education", "multiculturalism"]}
        for d, topics in positive_decades.items():
            if decade == d and topic in topics:
                return "positive"
        if int(decade) < 1980:
            return "neutral"
        return "neutral"

    def detect_discursive_shifts(
        self, topic: str = "singapore identity"
    ) -> list[DiscursiveShift]:
        periods = [
            ("1965", "1975"), ("1976", "1985"), ("1986", "1995"),
            ("1996", "2005"), ("2006", "2015"), ("2016", "2025"),
        ]
        shifts: list[DiscursiveShift] = []
        prev_count = 0

        for start, end in periods:
            try:
                titles = self._client.search_titles(
                    keywords=topic,
                    date_from=start,
                    date_to=end,
                    limit=50,
                )
            except NLBApiError:
                continue
            count = len(titles)
            if prev_count > 0:
                change = round((count - prev_count) / prev_count * 100, 1)
            else:
                change = 0.0
            description = self._describe_shift(topic, start, change)
            shifts.append(
                DiscursiveShift(
                    topic=topic,
                    period_start=start,
                    period_end=end,
                    frequency_change=change,
                    narrative_description=description,
                )
            )
            prev_count = count

        return shifts

    def _describe_shift(self, topic: str, period: str, change: float) -> str:
        if change > 50:
            return f"Significant surge in discourse on '{topic}' during {period}, suggesting growing public attention"
        elif change > 20:
            return f"Moderate increase in '{topic}' coverage during {period}"
        elif change < -20:
            return f"Declining focus on '{topic}' during {period}, potentially displaced by emerging topics"
        else:
            return f"Stable level of discourse on '{topic}' during {period}"

    def cross_collection_topic_map(
        self, subject: str = "singapore"
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        formats = ["books", "images", "newspapers", "maps", "sound recordings"]
        for fmt in formats:
            try:
                titles = self._client.search_titles(keywords=f"{fmt} {subject}", limit=15)
                subjects_found: list[str] = []
                for t in titles:
                    if t.subjects:
                        subjects_found.extend(t.subjects)
                result[fmt] = list(set(subjects_found))[:10]
            except NLBApiError:
                result[fmt] = []
        return result
