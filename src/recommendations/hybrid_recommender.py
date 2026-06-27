"""
Hybrid Book Recommendation Engine for Singapore Readers.

Combines NLB's official recommendation API with collaborative filtering
signals from checkout trends and content-based similarity from catalogue
metadata to produce personalised reading suggestions.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional

from src.client import NLBClient, NLBApiError
from src.models import Recommendation, TitleSearchResult, TitleDetail


@dataclass
class RecommendedTitle:
    title: str
    author: str
    brn: str
    isbn: str
    score: float
    reason: str
    source: str
    subjects: list[str] = field(default_factory=list)
    book_cover: str = ""


@dataclass
class UserPreferences:
    favourite_genres: list[str]
    favourite_authors: list[str]
    preferred_languages: list[str]
    preferred_formats: list[str]
    reading_level: str = "general"


class HybridRecommender:
    def __init__(self, client: NLBClient):
        self._client = client

    def recommend_by_keyword(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[RecommendedTitle]:
        try:
            recs = self._client.get_recommendations(keywords=keyword, limit=limit)
        except NLBApiError:
            recs = []

        try:
            catalogue_titles = self._client.search_titles(
                keywords=keyword, limit=limit, sort="relevancy"
            )
        except NLBApiError:
            catalogue_titles = []

        results: list[RecommendedTitle] = []
        seen_brns: set[str] = set()

        for rec in recs:
            if rec.brn in seen_brns:
                continue
            seen_brns.add(rec.brn)
            score = 0.8
            if rec.category:
                score += 0.1
            results.append(
                RecommendedTitle(
                    title=rec.title,
                    author=rec.author,
                    brn=rec.brn,
                    isbn=rec.isbn,
                    score=round(score, 2),
                    reason=f"Recommended by NLB for '{keyword}'",
                    source="NLB Recommendation API",
                    book_cover=rec.book_cover,
                )
            )

        for t in catalogue_titles:
            if t.brn in seen_brns:
                continue
            seen_brns.add(t.brn)
            score = 0.5
            if t.author:
                score += 0.1
            if t.subjects:
                score += 0.05 * min(len(t.subjects), 4)
            results.append(
                RecommendedTitle(
                    title=t.title,
                    author=t.author or "",
                    brn=t.brn or "",
                    isbn=t.isbn or "",
                    score=round(min(score, 1.0), 2),
                    reason=f"Found in catalogue matching '{keyword}'",
                    source="Catalogue Search API",
                    subjects=t.subjects,
                    book_cover=t.book_cover,
                )
            )

        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]

    def recommend_by_seed(
        self,
        seed_brn: str | None = None,
        seed_isbn: str | None = None,
        limit: int = 20,
    ) -> list[RecommendedTitle]:
        recommendations: list[RecommendedTitle] = []

        if seed_brn or seed_isbn:
            try:
                recs = self._client.get_recommendations(
                    brn=seed_brn, isbn=seed_isbn, limit=limit
                )
            except NLBApiError:
                recs = []
            seen: set[str] = set()
            for rec in recs:
                if rec.brn in seen:
                    continue
                seen.add(rec.brn)
                recommendations.append(
                    RecommendedTitle(
                        title=rec.title,
                        author=rec.author,
                        brn=rec.brn,
                        isbn=rec.isbn,
                        score=0.9,
                        reason="Based on NLB recommendation service",
                        source="NLB Recommendation API",
                        book_cover=rec.book_cover,
                    )
                )

        if seed_brn:
            try:
                detail = self._client.get_title_details(brn=seed_brn)
            except NLBApiError:
                detail = None
            if detail and detail.subjects:
                for subject in detail.subjects[:3]:
                    try:
                        similar = self._client.search_titles(
                            keywords=subject, limit=10
                        )
                    except NLBApiError:
                        continue
                    for t in similar:
                        if t.brn in seen or not t.brn:
                            continue
                        seen.add(t.brn)
                        recommendations.append(
                            RecommendedTitle(
                                title=t.title,
                                author=t.author or "",
                                brn=t.brn,
                                isbn=t.isbn or "",
                                score=0.7,
                                reason=f"Similar subject: {subject}",
                                source="Catalogue Content-Based",
                                subjects=t.subjects,
                                book_cover=t.book_cover,
                            )
                        )
        return sorted(recommendations, key=lambda r: r.score, reverse=True)[:limit]

    def trending_recommendations(
        self, branch_code: str | None = None
    ) -> list[RecommendedTitle]:
        if branch_code is None:
            branch_code = "TRL"
        try:
            trends = self._client.get_checkout_trends(branch_code)
        except NLBApiError:
            return []
        results: list[RecommendedTitle] = []
        for t in trends[:15]:
            score = min(t.checkout_count / 50, 1.0)
            results.append(
                RecommendedTitle(
                    title=t.title,
                    author="",
                    brn=t.brn,
                    isbn="",
                    score=round(score, 2),
                    reason=f"Trending at {branch_code} ({t.checkout_count} checkouts)",
                    source="Checkout Trends API",
                )
            )
        return results

    def personalized_for_user(
        self, preferences: UserPreferences, limit: int = 20
    ) -> list[RecommendedTitle]:
        results: list[RecommendedTitle] = []
        seen: set[str] = set()
        for genre in preferences.favourite_genres[:3]:
            try:
                titles = self._client.search_titles(
                    keywords=genre, limit=10,
                    languages=preferences.preferred_languages if preferences.preferred_languages else None,
                )
            except NLBApiError:
                continue
            for t in titles:
                if t.brn in seen or not t.brn:
                    continue
                seen.add(t.brn)
                score = 0.5
                if t.author and t.author in preferences.favourite_authors:
                    score += 0.3
                if t.language in preferences.preferred_languages:
                    score += 0.1
                results.append(
                    RecommendedTitle(
                        title=t.title,
                        author=t.author or "",
                        brn=t.brn,
                        isbn=t.isbn or "",
                        score=round(min(score, 1.0), 2),
                        reason=f"Matches your interest in {genre}",
                        source="Personalised CF + CBF",
                        subjects=t.subjects,
                        book_cover=t.book_cover,
                    )
                )
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]

    def diverse_discovery(
        self, limit: int = 20
    ) -> list[RecommendedTitle]:
        diverse_topics = [
            "singapore literature", "malay folklore", "tamil poetry",
            "chinese calligraphy", "peranakan culture", "science fiction",
            "cookbook", "travel writing", "architecture", "comics",
        ]
        results: list[RecommendedTitle] = []
        seen: set[str] = set()
        for topic in diverse_topics:
            try:
                titles = self._client.search_titles(keywords=topic, limit=5)
            except NLBApiError:
                continue
            for t in titles:
                if t.brn in seen:
                    continue
                seen.add(t.brn)
                results.append(
                    RecommendedTitle(
                        title=t.title,
                        author=t.author or "",
                        brn=t.brn,
                        isbn=t.isbn or "",
                        score=0.6,
                        reason=f"Explore {topic}",
                        source="Discovery / Serendipity",
                        subjects=t.subjects,
                        book_cover=t.book_cover,
                    )
                )
        return results[:limit]
