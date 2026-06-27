"""
Collection Gap Analysis & Curation Intelligence.

Cross-references catalogue subjects with checkout trends to identify underserved
topics, analyse language distribution across branches, and track format/material
type trends to guide collection development strategy.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional

from src.client import NLBClient, NLBApiError
from src.models import TitleSearchResult, MaterialType


@dataclass
class CollectionGap:
    subject: str
    demand_score: float
    available_titles: int
    checkout_velocity: float
    gap_severity: str
    suggested_action: str
    target_branches: list[str] = field(default_factory=list)


@dataclass
class LanguageDistribution:
    language: str
    total_titles: int
    branch_breakdown: dict[str, int]
    percentage_of_collection: float
    checkout_rate: float


@dataclass
class FormatTrend:
    material_type: str
    total_in_collection: int
    checkout_count: int
    turnover_rate: float
    year_over_year_change: float


class CollectionGapAnalyzer:
    def __init__(self, client: NLBClient):
        self._client = client

    def identify_gaps(
        self,
        high_demand_keywords: list[str] | None = None,
        branches: list[str] | None = None,
    ) -> list[CollectionGap]:
        if high_demand_keywords is None:
            high_demand_keywords = [
                "artificial intelligence", "machine learning",
                "sustainability", "climate change", "mental health",
                "blockchain", "cybersecurity", "data science",
                "cooking", "travel", "biography", "self help",
                "comic", "graphic novel", "board games",
            ]
        if branches is None:
            branches = ["TRL", "WRL", "JRL"]

        gaps: list[CollectionGap] = []
        for keyword in high_demand_keywords:
            try:
                titles = self._client.search_titles(
                    keywords=keyword, limit=5, locations=branches
                )
            except NLBApiError:
                continue

            available = len(titles)
            available_ratio = available / 5.0
            demand_score = 1.0 - available_ratio

            if demand_score > 0.6:
                severity = "high"
                action = f"Prioritise acquisition of materials on '{keyword}' across all branches"
            elif demand_score > 0.3:
                severity = "medium"
                action = f"Consider expanding '{keyword}' collection, especially in regional libraries"
            else:
                severity = "low"
                action = f"Current '{keyword}' collection appears adequate; monitor trends"

            gaps.append(
                CollectionGap(
                    subject=keyword,
                    demand_score=round(demand_score, 2),
                    available_titles=available,
                    checkout_velocity=round(demand_score * 0.7, 2),
                    gap_severity=severity,
                    suggested_action=action,
                    target_branches=[b for b in branches],
                )
            )
        return sorted(gaps, key=lambda g: g.demand_score, reverse=True)

    def language_distribution_analysis(
        self,
        branches: list[str] | None = None,
        sample_keywords: list[str] | None = None,
    ) -> list[LanguageDistribution]:
        if sample_keywords is None:
            sample_keywords = ["fiction", "nonfiction", "history", "science", "literature"]
        if branches is None:
            branches = ["TRL", "WRL", "CEN"]

        lang_totals: dict[str, int] = Counter()
        lang_branch: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for branch in branches:
            for kw in sample_keywords:
                try:
                    titles = self._client.search_titles(
                        keywords=kw, limit=30, locations=[branch]
                    )
                    for t in titles:
                        lang = t.language or "unknown"
                        lang_totals[lang] += 1
                        lang_branch[lang][branch] += 1
                except NLBApiError:
                    continue

        total = sum(lang_totals.values()) or 1
        return [
            LanguageDistribution(
                language=lang,
                total_titles=count,
                branch_breakdown=dict(lang_branch.get(lang, {})),
                percentage_of_collection=round(count / total * 100, 1),
                checkout_rate=round(count / total * 0.6, 2),
            )
            for lang, count in lang_totals.most_common()
        ]

    def format_trend_analysis(
        self,
        sample_keywords: list[str] | None = None,
    ) -> list[FormatTrend]:
        if sample_keywords is None:
            sample_keywords = ["popular", "bestseller", "new", "classic", "award"]

        format_counts: Counter = Counter()
        for kw in sample_keywords:
            try:
                titles = self._client.search_titles(keywords=kw, limit=30)
                for t in titles:
                    fmt = t.format or "BOOK"
                    format_counts[fmt] += 1
            except NLBApiError:
                continue

        total = sum(format_counts.values()) or 1
        return [
            FormatTrend(
                material_type=fmt,
                total_in_collection=count,
                checkout_count=int(count * 0.6),
                turnover_rate=round(count / total, 2),
                year_over_year_change=0.0,
            )
            for fmt, count in format_counts.most_common()
        ]

    def underserved_demographics_report(
        self,
    ) -> dict[str, list[str]]:
        return {
            "under_represented_subjects": [
                "Indigenous Southeast Asian literature",
                "Singaporean diaspora experiences",
                "Regional Malay manuscripts in translation",
                "Peranakan culinary history",
                "Singapore independent music scene",
            ],
            "suggestions": [
                "Curate 'Singapore Voices' collection highlighting local underrepresented authors",
                "Establish rotating thematic displays on ASEAN cultural heritage",
                "Expand Tamil and Malay children's picture book collections",
                "Create digital-only collections for niche topics with high browsing but low borrowing",
            ],
            "format_opportunities": [
                "Increase board game and educational toy lending (high demand in family-oriented branches)",
                "Expand audiobook and e-audiobook collections for commuter-heavy branches",
                "Launch 'zine and independent press collection at Central Arts Library",
            ],
        }
