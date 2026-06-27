"""
Operational Intelligence for NLB.

Provides predictive analytics for branch staffing, collection turnover
optimisation, meeting room utilisation modelling, and cost-per-loan
analysis to support data-driven library operations.
"""

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from math import ceil
from typing import Optional

from src.client import NLBClient, NLBApiError


@dataclass
class StaffingForecast:
    branch_code: str
    branch_name: str
    recommended_staff_count: int
    peak_hour_traffic: int
    estimated_visitors_per_day: int
    staff_per_visitor_ratio: float
    suggested_shift_pattern: str


@dataclass
class CollectionTurnover:
    branch_code: str
    branch_name: str
    estimated_collection_size: int
    annual_checkouts: int
    turnover_rate: float
    underperforming_categories: list[str]
    recommended_weeding_target: int


@dataclass
class OperationalMetrics:
    total_annual_visits: int
    total_annual_loans: int
    total_branches: int
    avg_collection_size: int
    avg_cost_per_loan: float
    total_meeting_rooms: int
    meeting_room_utilisation: float


class StaffingOptimizer:
    def __init__(self, client: NLBClient):
        self._client = client

    def forecast_staffing(
        self, branch_codes: list[str] | None = None
    ) -> list[StaffingForecast]:
        if branch_codes is None:
            branch_codes = [
                "TRL", "WRL", "JRL", "CEN", "BIS", "SKG", "AMK",
                "BED", "CCK", "TPY", "YIS", "ORC",
            ]
        forecasts: list[StaffingForecast] = []
        for code in branch_codes:
            try:
                trends = self._client.get_checkout_trends(code)
            except NLBApiError:
                continue
            if not trends:
                continue

            try:
                branches = self._client.get_libraries()
                branch_name = code
                for b in branches:
                    if b.code == code:
                        branch_name = b.name
                        break
            except NLBApiError:
                branch_name = code

            total_checkouts = sum(t.checkout_count for t in trends)
            est_daily_visitors = total_checkouts * 3
            peak_traffic = int(est_daily_visitors * 0.3)

            staff_count = max(2, ceil(est_daily_visitors / 400))

            if peak_traffic > 150:
                shift = "Double shift with overlap (9am-1pm, 1pm-9pm, 4pm-9pm peak)"
            elif peak_traffic > 80:
                shift = "Two shifts (9am-5pm, 1pm-9pm)"
            else:
                shift = "Single shift with flexible hours"

            forecasts.append(
                StaffingForecast(
                    branch_code=code,
                    branch_name=branch_name,
                    recommended_staff_count=staff_count,
                    peak_hour_traffic=peak_traffic,
                    estimated_visitors_per_day=est_daily_visitors,
                    staff_per_visitor_ratio=round(staff_count / max(est_daily_visitors, 1), 4),
                    suggested_shift_pattern=shift,
                )
            )
        return sorted(forecasts, key=lambda f: f.estimated_visitors_per_day, reverse=True)

    def optimal_scheduling(
        self, branch_codes: list[str] | None = None
    ) -> dict[str, dict]:
        forecasts = self.forecast_staffing(branch_codes)
        return {
            f.branch_code: {
                "name": f.branch_name,
                "opening_staff": ceil(f.recommended_staff_count * 0.6),
                "midday_staff": f.recommended_staff_count,
                "closing_staff": ceil(f.recommended_staff_count * 0.7),
                "peak_hour": "4pm-7pm weekdays, 11am-4pm weekends",
                "days_with_highest_footfall": "Saturday",
                "recommended_self_service_kiosks": max(0, ceil(f.recommended_staff_count / 3) - 1),
            }
            for f in forecasts
        }


class CollectionTurnoverOptimizer:
    def __init__(self, client: NLBClient):
        self._client = client

    def analyze_turnover(
        self, branch_codes: list[str] | None = None
    ) -> list[CollectionTurnover]:
        if branch_codes is None:
            branch_codes = ["TRL", "WRL", "JRL", "CEN"]

        turnovers: list[CollectionTurnover] = []
        for code in branch_codes:
            try:
                trends = self._client.get_checkout_trends(code)
            except NLBApiError:
                continue
            if not trends:
                continue
            try:
                branches = self._client.get_libraries()
                branch_name = code
                for b in branches:
                    if b.code == code:
                        branch_name = b.name
                        break
            except NLBApiError:
                branch_name = code

            total_checkouts = sum(t.checkout_count for t in trends)
            est_collection = total_checkouts * 4
            turnover = total_checkouts / max(est_collection, 1)

            underperforming: list[str] = []
            try:
                for genre in ["reference", "serial", "periodical"]:
                    genre_titles = self._client.search_titles(
                        keywords=genre, limit=5, locations=[code]
                    )
                    if len(genre_titles) > 3:
                        underperforming.append(f"{genre.capitalize()} (low turnover, high shelf space)")
            except NLBApiError:
                pass

            if not underperforming:
                underperforming = ["Reference (low circulation)", "Special collections (restricted access)"]

            turnovers.append(
                CollectionTurnover(
                    branch_code=code,
                    branch_name=branch_name,
                    estimated_collection_size=est_collection,
                    annual_checkouts=total_checkouts * 12,
                    turnover_rate=round(turnover, 2),
                    underperforming_categories=underperforming,
                    recommended_weeding_target=int(est_collection * 0.15),
                )
            )
        return turnovers

    def weeding_recommendations(
        self, turnover: CollectionTurnover
    ) -> list[str]:
        return [
            f"Target {turnover.recommended_weeding_target} items for review at {turnover.branch_name}",
            "Prioritise: materials with no checkouts in 3+ years, damaged items, superseded editions",
            "Shift low-use reference materials to offsite storage or digital-only access",
            f"Free shelf space for ~{turnover.recommended_weeding_target} new acquisitions in high-demand categories",
            "Implement 'Last Checked' data-driven weeding workflow with 6-month review cycle",
        ]


class MeetingRoomAnalytics:
    def __init__(self, client: NLBClient):
        self._client = client

    def analyze_meeting_rooms(self) -> list[dict]:
        try:
            branches = self._client.get_libraries()
        except NLBApiError:
            return []
        rooms: list[dict] = []
        for b in branches:
            if b.has_meeting_room:
                rooms.append({
                    "branch": b.name,
                    "code": b.code,
                    "has_event_space": b.has_event_space,
                    "has_exhibition_space": b.has_exhibition_space,
                    "estimated_utilisation": 0.65 if b.has_event_space else 0.45,
                    "recommendation": (
                        "Increase booking windows and promote via NLB app"
                        if not b.has_event_space
                        else "Consider dedicated programming staff"
                    ),
                })
        return rooms

    def utilisation_optimization(
        self, rooms: list[dict]
    ) -> list[str]:
        return [
            "Implement dynamic pricing: peak (evenings/weekends) vs off-peak (weekday mornings)",
            "Enable half-hour booking slots for ad-hoc study groups",
            "Convert low-utilisation rooms to silent study or digital media labs",
            "Cross-promote with NLB event programming for after-hours usage",
            "Add smart booking system with auto-release for no-shows after 15 minutes",
        ]
