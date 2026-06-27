"""
Entity Extraction for Singapore Cultural Heritage.

Specialised NLP pipeline to extract named entities (people, places, events,
organisations) from NLB catalogue metadata, linking them across collections
for cross-referenced discovery.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional
import re

from src.client import NLBClient, NLBApiError
from src.models import TitleDetail


@dataclass
class NamedEntity:
    text: str
    label: str
    confidence: float
    source_fields: list[str] = field(default_factory=list)
    frequency: int = 1


@dataclass
class EntityRelation:
    source: str
    target: str
    relation: str
    weight: float


class HeritageEntityExtractor:
    def __init__(self, client: NLBClient):
        self._client = client

    _singapore_places = [
        "Singapore River", "Marina Bay", "Sentosa", "Orchard Road",
        "Chinatown", "Little India", "Kampong Glam", "Geylang Serai",
        "Jurong", "Woodlands", "Tampines", "Ang Mo Kio",
        "Bishan", "Serangoon", "Bedok", "Clementi",
        "Queenstown", "Toa Payoh", "Bukit Timah", "Pasir Ris",
        "Punggol", "Sengkang", "Yishun", "Choa Chu Kang",
        "National Library", "Esplanade", "Merlion Park", "Gardens by the Bay",
        "Fort Canning", "Raffles Hotel", "Changi Airport", "Botanic Gardens",
    ]

    _historical_figures = [
        "Stamford Raffles", "Lee Kuan Yew", "Goh Chok Tong", "S. Rajaratnam",
        "Goh Keng Swee", "Toh Chin Chye", "Ong Teng Cheong", "Devan Nair",
        "Yusof Ishak", "Benjamin Sheares", "Wee Kim Wee",
        "Munshi Abdullah", "Tan Kim Seng", "Gan Eng Seng",
        "Lim Bo Seng", "Abdul Gani", "David Marshall", "Lim Yew Hock",
    ]

    def extract_from_search(
        self, keywords: list[str] | None = None
    ) -> list[NamedEntity]:
        if keywords is None:
            keywords = ["singapore", "history", "heritage", "culture"]
        entities: dict[str, NamedEntity] = {}

        for kw in keywords:
            try:
                titles = self._client.search_titles(keywords=kw, limit=40)
            except NLBApiError:
                continue
            for t in titles:
                if not t.brn:
                    continue
                try:
                    detail = self._client.get_title_details(brn=t.brn)
                except NLBApiError:
                    continue
                if not detail:
                    continue

                text_blob = " ".join([
                    t.title,
                    t.author or "",
                    " ".join(t.subjects),
                    detail.summary,
                    " ".join(detail.authors),
                ]).lower()

                for place in self._singapore_places:
                    if place.lower() in text_blob:
                        if place not in entities:
                            entities[place] = NamedEntity(text=place, label="LOC", confidence=0.9)
                        entities[place].frequency += 1
                        entities[place].source_fields.extend(["title", "subjects", "summary"])

                for person in self._historical_figures:
                    if person.lower() in text_blob:
                        if person not in entities:
                            entities[person] = NamedEntity(text=person, label="PER", confidence=0.85)
                        entities[person].frequency += 1
                        entities[person].source_fields.extend(["title", "author", "summary"])

                subjects = (detail.subjects or []) + (t.subjects or [])
                for subject in subjects:
                    subject_clean = subject.strip()
                    if len(subject_clean) > 3 and subject_clean not in entities:
                        entities[subject_clean] = NamedEntity(
                            text=subject_clean,
                            label=self._guess_label(subject_clean),
                            confidence=0.6,
                            source_fields=["subjects"],
                        )
                        entities[subject_clean].frequency += 1

        return list(entities.values())

    def _guess_label(self, text: str) -> str:
        text_lower = text.lower()
        person_indicators = ["person", "人物", "biography", "author", "writer", "artist"]
        loc_indicators = ["singapore", "place", "region", "country", "city", "island"]
        event_indicators = ["history", "war", "festival", "movement", "revolution", "day"]
        if any(i in text_lower for i in person_indicators):
            return "PER"
        if any(i in text_lower for i in loc_indicators):
            return "LOC"
        if any(i in text_lower for i in event_indicators):
            return "EVT"
        return "MISC"

    def extract_relations(
        self, seed_keywords: list[str] | None = None
    ) -> list[EntityRelation]:
        entities = self.extract_from_search(seed_keywords)
        entity_names = [e.text for e in entities]
        relations: list[EntityRelation] = []
        for i, e1 in enumerate(entity_names):
            for e2 in entity_names[i + 1:]:
                try:
                    titles = self._client.search_titles(keywords=f"{e1} {e2}", limit=5)
                    if titles:
                        score = len(titles) / 5.0
                        relations.append(
                            EntityRelation(
                                source=e1, target=e2,
                                relation="co_occurrence",
                                weight=round(score, 2),
                            )
                        )
                except NLBApiError:
                    continue
        return sorted(relations, key=lambda r: r.weight, reverse=True)[:100]
