"""Tests for Operational Intelligence module."""

from unittest.mock import MagicMock
import pytest

from src.operational.staffing_forecast import (
    StaffingOptimizer, CollectionTurnoverOptimizer, MeetingRoomAnalytics,
)
from tests.fixtures import MOCK_CHECKOUT_TRENDS, MOCK_LIBRARIES, MOCK_SEARCH_RESULTS


@pytest.fixture
def staffing():
    mock_client = MagicMock()
    mock_client.get_checkout_trends.return_value = MOCK_CHECKOUT_TRENDS
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    return StaffingOptimizer(mock_client)


@pytest.fixture
def turnover():
    mock_client = MagicMock()
    mock_client.get_checkout_trends.return_value = MOCK_CHECKOUT_TRENDS
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    mock_client.search_titles.return_value = MOCK_SEARCH_RESULTS[:2]
    return CollectionTurnoverOptimizer(mock_client)


@pytest.fixture
def rooms():
    mock_client = MagicMock()
    mock_client.get_libraries.return_value = MOCK_LIBRARIES
    return MeetingRoomAnalytics(mock_client)


class TestStaffingOptimizer:
    def test_forecast_staffing(self, staffing):
        forecasts = staffing.forecast_staffing(
            branch_codes=["TRL", "WRL", "CEN"]
        )
        assert len(forecasts) == 3
        for f in forecasts:
            assert f.branch_code
            assert f.recommended_staff_count > 0
            assert f.estimated_visitors_per_day > 0
            assert f.suggested_shift_pattern

    def test_forecast_staffing_sorted(self, staffing):
        forecasts = staffing.forecast_staffing(
            branch_codes=["TRL", "WRL"]
        )
        assert forecasts[0].estimated_visitors_per_day >= forecasts[-1].estimated_visitors_per_day

    def test_optimal_scheduling(self, staffing):
        schedule = staffing.optimal_scheduling(
            branch_codes=["TRL", "CEN"]
        )
        assert "TRL" in schedule
        assert "CEN" in schedule
        trl = schedule["TRL"]
        assert trl["opening_staff"] > 0
        assert trl["recommended_self_service_kiosks"] >= 0


class TestCollectionTurnoverOptimizer:
    def test_analyze_turnover(self, turnover):
        result = turnover.analyze_turnover(
            branch_codes=["TRL", "WRL"]
        )
        assert len(result) == 2
        for r in result:
            assert r.branch_code
            assert r.annual_checkouts > 0
            assert r.turnover_rate >= 0
            assert r.recommended_weeding_target > 0

    def test_weeding_recommendations(self, turnover):
        sample = turnover.analyze_turnover(branch_codes=["TRL"])[0]
        recs = turnover.weeding_recommendations(sample)
        assert len(recs) > 0
        assert any("weed" in r.lower() for r in recs)


class TestMeetingRoomAnalytics:
    def test_analyze_meeting_rooms(self, rooms):
        result = rooms.analyze_meeting_rooms()
        assert len(result) > 0
        for r in result:
            assert "branch" in r
            assert "estimated_utilisation" in r
            assert "recommendation" in r

    def test_analyse_no_rooms(self, rooms):
        mock_client = MagicMock()
        mock_client.get_libraries.return_value = []
        rooms._client = mock_client
        result = rooms.analyze_meeting_rooms()
        assert len(result) == 0

    def test_utilisation_optimization(self, rooms):
        sample_rooms = rooms.analyze_meeting_rooms()
        opts = rooms.utilisation_optimization(sample_rooms)
        assert len(opts) > 0
