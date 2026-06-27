"""Tests for NLB client module."""

from unittest.mock import patch, MagicMock
import pytest
import httpx

from src.client import NLBClient, NLBApiError
from tests.fixtures import (
    MOCK_LIBRARIES, MOCK_SEARCH_RESULTS, MOCK_TITLE_DETAILS,
    MOCK_AVAILABILITY, MOCK_CHECKOUT_TRENDS, MOCK_RECOMMENDATIONS,
    MOCK_ERESOURCES,
)


@pytest.fixture
def client():
    with patch.dict("os.environ", {"NLB_APP_ID": "test_app", "NLB_API_KEY": "test_key"}):
        from src.config import get_settings
        get_settings.cache_clear()
        from src.client import NLBClient
        c = NLBClient(app_id="test_app", api_key="test_key")
        yield c


class TestNLBClient:
    def test_init_missing_credentials(self):
        with pytest.raises(NLBApiError, match="NLB credentials required"):
            NLBClient(app_id="", api_key="")

    def test_search_titles(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "titles": [
                    {
                        "brn": "BRN123456", "title": "Test Book",
                        "author": "Author", "isbn": "978123",
                        "format": "BOOK", "publisher": "Pub",
                        "publishDate": "2020", "language": "English",
                        "subjects": ["Test"], "bookCover": "",
                        "availability": "On Shelf",
                    }
                ]
            }
            mock_request.return_value = mock_response

            results = client.search_titles(keywords="test")
            assert len(results) == 1
            assert results[0].title == "Test Book"
            assert results[0].brn == "BRN123456"

    def test_search_titles_with_filters(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"titles": []}
            mock_request.return_value = mock_response

            results = client.search_titles(
                keywords="history",
                material_types=["BOOK"],
                audiences=["adult"],
                locations=["TRL", "CEN"],
                languages=["English"],
                availability=True,
                fiction=False,
                limit=50,
            )
            assert len(results) == 0
            call_url = mock_request.call_args[0][1]
            assert "MaterialTypes=BOOK" in call_url or "materialTypes=BOOK" in call_url

    def test_get_title_details(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "brn": "BRN123456", "title": "Test Title",
                "authors": ["Author A"], "isbns": ["978123"],
                "format": "BOOK", "edition": "1st", "publisher": "Pub",
                "publishDate": "2020", "subjects": ["Subject"],
                "summary": "A test book", "language": "English",
                "audience": "adult", "physicalDescription": "100p",
                "bookCover": {"small": "", "medium": "", "large": ""},
                "allowReservation": True, "isRestricted": False,
                "activeReservationsCount": 3,
            }
            mock_request.return_value = mock_response

            detail = client.get_title_details(brn="BRN123456")
            assert detail is not None
            assert detail.title == "Test Title"
            assert detail.active_reservations_count == 3

    def test_get_title_details_no_brn_isbn(self, client):
        with pytest.raises(NLBApiError, match="Either BRN or ISBN is required"):
            client.get_title_details()

    def test_get_availability(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [
                    {
                        "branchCode": "TRL", "branchName": "Tampines",
                        "shelfLocation": "Adult", "callNumber": "959.57",
                        "statusCode": "AVAILABLE", "statusDesc": "On Shelf",
                        "collection": "Adult Lending",
                    }
                ]
            }
            mock_request.return_value = mock_response

            avail = client.get_availability(isbn="978123")
            assert len(avail) == 1
            assert avail[0].branch_code == "TRL"
            assert avail[0].status_desc == "On Shelf"

    def test_get_availability_no_identifier(self, client):
        with pytest.raises(NLBApiError, match="Either BRN or ISBN is required"):
            client.get_availability()

    def test_get_new_titles(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"titles": []}
            mock_request.return_value = mock_response

            results = client.get_new_titles(date_range="Monthly", limit=30)
            assert isinstance(results, list)

    def test_get_checkout_trends(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "titles": [
                    {
                        "brn": "BRN123", "title": "Popular Book",
                        "checkoutCount": 50, "branchName": "Tampines",
                    }
                ]
            }
            mock_request.return_value = mock_response

            trends = client.get_checkout_trends("TRL")
            assert len(trends) == 1
            assert trends[0].checkout_count == 50

    def test_get_libraries(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "libraries": [
                    {
                        "code": "TRL", "name": "Tampines Regional",
                        "address": "1 Tampines Walk", "postalCode": "529684",
                        "telephone": "6788 8828", "latitude": 1.352,
                        "longitude": 103.945, "weekdayHours": "10-9",
                        "saturdayHours": "10-9",
                        "sundayPublicHolidayHours": "10-9",
                        "hasEvent": True, "hasMeetingRoom": True,
                        "hasExhibition": False, "imageUrl": "",
                        "description": "Regional library",
                    }
                ]
            }
            mock_request.return_value = mock_response

            libs = client.get_libraries()
            assert len(libs) == 1
            assert libs[0].code == "TRL"

    def test_search_eresources(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "E-Book Title", "contentType": "ebooks",
                        "summary": "Digital book", "creator": "Author",
                        "subject": "History", "source": "NLB",
                        "url": "https://example.com", "date": "2024",
                    }
                ]
            }
            mock_request.return_value = mock_response

            results = client.search_eresources(keywords="history")
            assert len(results) == 1
            assert results[0].content_type == "ebooks"

    def test_get_recommendations(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "recommendations": [
                    {
                        "brn": "BRN789", "title": "Recommended Book",
                        "author": "Author", "isbn": "978789",
                        "category": "Fiction", "bookCover": "",
                    }
                ]
            }
            mock_request.return_value = mock_response

            recs = client.get_recommendations(keywords="fiction")
            assert len(recs) == 1
            assert recs[0].category == "Fiction"

    def test_rate_limit_handling(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_request.return_value = mock_response

            with pytest.raises(NLBApiError, match="Rate limit exceeded"):
                client.search_titles(keywords="test")

    def test_api_error_handling(self, client):
        with patch.object(client._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Internal server error"}
            mock_request.return_value = mock_response

            with pytest.raises(NLBApiError, match="API error: 500"):
                client.search_titles(keywords="test")

    def test_context_manager(self, client):
        with client as c:
            assert c is client
