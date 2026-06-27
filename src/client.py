import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Any
from urllib.parse import urlencode

from src.config import get_settings
from src.models import (
    TitleDetail, TitleSearchResult, ItemAvailability, LibraryBranch,
    EResource, Recommendation, CheckoutTrend, MaterialType, Audience,
)


class NLBApiError(Exception):
    def __init__(self, message: str, status_code: int = 0, response: Optional[dict] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class NLBClient:
    def __init__(self, app_id: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self._app_id = app_id or settings.nlb_app_id
        self._api_key = api_key or settings.nlb_api_key
        if not self._app_id or not self._api_key:
            raise NLBApiError(
                "NLB credentials required. Set NLB_APP_ID and NLB_API_KEY in .env "
                "or request at https://go.gov.sg/nlblabs-form"
            )
        self._headers = {
            "X-API-KEY": self._api_key,
            "X-APP-Code": self._app_id,
            "Accept": "application/json",
        }
        self._timeout = settings.request_timeout
        self._client = httpx.Client(timeout=self._timeout, headers=self._headers)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _build_url(self, base: str, path: str, params: dict[str, Any] | None = None) -> str:
        url = f"{base}{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += "?" + urlencode(filtered)
        return url

    def _request(self, method: str, url: str) -> dict:
        resp = self._client.request(method, url)
        if resp.status_code == 429:
            raise NLBApiError("Rate limit exceeded. Retry after backoff.", status_code=429)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = {"raw": resp.text}
            raise NLBApiError(
                f"API error: {resp.status_code}",
                status_code=resp.status_code,
                response=detail,
            )
        return resp.json()

    # ── Catalogue API v2 ──────────────────────────────────────────────

    def search_titles(
        self,
        keywords: str,
        limit: int = 20,
        offset: int = 0,
        material_types: list[MaterialType | str] | None = None,
        audiences: list[Audience | str] | None = None,
        locations: list[str] | None = None,
        languages: list[str] | None = None,
        availability: bool | None = None,
        fiction: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort: str | None = None,
    ) -> list[TitleSearchResult]:
        params = {
            "Keywords": keywords,
            "Limit": limit,
            "Offset": offset,
            "Source": "catalogue",
            "SortFields": sort,
            "Availability": availability,
            "Fiction": fiction,
            "DateFrom": date_from,
            "DateTo": date_to,
        }
        if material_types:
            params["MaterialTypes"] = ",".join(mt.value if isinstance(mt, MaterialType) else mt for mt in material_types)
        if audiences:
            params["IntendedAudiences"] = ",".join(a.value if isinstance(a, Audience) else a for a in audiences)
        if locations:
            params["Locations"] = ",".join(locations)
        if languages:
            params["Languages"] = ",".join(languages)

        url = self._build_url(get_settings().catalogue_base_url, "/SearchTitles", params)
        data = self._request("GET", url)
        titles = data.get("titles") or []
        return [
            TitleSearchResult(
                brn=t.get("brn", ""),
                title=t.get("title", ""),
                author=t.get("author", ""),
                isbn=t.get("isbn", ""),
                format=t.get("format", ""),
                publisher=t.get("publisher", ""),
                publish_date=t.get("publishDate", ""),
                language=t.get("language", ""),
                subjects=t.get("subjects", []),
                book_cover=t.get("bookCover", ""),
                availability=t.get("availability", ""),
            )
            for t in titles
        ]

    def get_title_details(self, brn: str | None = None, isbn: str | None = None) -> TitleDetail | None:
        if not brn and not isbn:
            raise NLBApiError("Either BRN or ISBN is required")
        params = {}
        if brn:
            params["BRN"] = brn
        if isbn:
            params["ISBN"] = isbn
        url = self._build_url(get_settings().catalogue_base_url, "/GetTitleDetails", params)
        data = self._request("GET", url)
        if not data:
            return None
        return TitleDetail(
            brn=data.get("brn", ""),
            title=data.get("title", ""),
            authors=data.get("authors", []),
            isbns=data.get("isbns", []),
            issns=data.get("issns", []),
            format=data.get("format", ""),
            edition=data.get("edition", ""),
            publisher=data.get("publisher", ""),
            publish_date=data.get("publishDate", ""),
            subjects=data.get("subjects", []),
            summary=data.get("summary", ""),
            language=data.get("language", ""),
            audience=data.get("audience", ""),
            physical_description=data.get("physicalDescription", ""),
            book_cover_small=data.get("bookCover", {}).get("small", ""),
            book_cover_medium=data.get("bookCover", {}).get("medium", ""),
            book_cover_large=data.get("bookCover", {}).get("large", ""),
            allow_reservation=data.get("allowReservation", False),
            is_restricted=data.get("isRestricted", False),
            active_reservations_count=data.get("activeReservationsCount", 0),
        )

    def get_availability(
        self,
        brn: str | None = None,
        isbn: str | None = None,
        location_code: str | None = None,
    ) -> list[ItemAvailability]:
        if not brn and not isbn:
            raise NLBApiError("Either BRN or ISBN is required")
        params = {}
        if brn:
            params["BRN"] = brn
        if isbn:
            params["ISBN"] = isbn
        if location_code:
            params["LocationCode"] = location_code
        url = self._build_url(get_settings().catalogue_base_url, "/GetAvailabilityInfo", params)
        data = self._request("GET", url)
        items = data.get("items") or []
        return [
            ItemAvailability(
                branch_code=i.get("branchCode", ""),
                branch_name=i.get("branchName", ""),
                shelf_location=i.get("shelfLocation", ""),
                call_number=i.get("callNumber", ""),
                status_code=i.get("statusCode", ""),
                status_desc=i.get("statusDesc", ""),
                collection=i.get("collection", ""),
            )
            for i in items
        ]

    def get_new_titles(
        self,
        date_range: str = "Weekly",
        limit: int = 50,
        material_types: list[MaterialType | str] | None = None,
        audiences: list[Audience | str] | None = None,
        locations: list[str] | None = None,
        languages: list[str] | None = None,
    ) -> list[TitleSearchResult]:
        params: dict[str, Any] = {"DateRange": date_range, "Limit": limit}
        if material_types:
            params["MaterialTypes"] = ",".join(mt.value if isinstance(mt, MaterialType) else mt for mt in material_types)
        if audiences:
            params["IntendedAudiences"] = ",".join(a.value if isinstance(a, Audience) else a for a in audiences)
        if locations:
            params["Locations"] = ",".join(locations)
        if languages:
            params["Languages"] = ",".join(languages)
        url = self._build_url(get_settings().catalogue_base_url, "/GetNewTitles", params)
        data = self._request("GET", url)
        titles = data.get("titles") or []
        return [
            TitleSearchResult(
                brn=t.get("brn", ""),
                title=t.get("title", ""),
                author=t.get("author", ""),
                isbn=t.get("isbn", ""),
                format=t.get("format", ""),
                publisher=t.get("publisher", ""),
                publish_date=t.get("publishDate", ""),
                language=t.get("language", ""),
                subjects=t.get("subjects", []),
                book_cover=t.get("bookCover", ""),
            )
            for t in titles
        ]

    def get_checkout_trends(
        self, location_code: str, duration: str = "past30days"
    ) -> list[CheckoutTrend]:
        params = {"LocationCode": location_code, "Duration": duration}
        url = self._build_url(
            get_settings().catalogue_base_url, "/GetMostCheckoutsTrendsTitles", params
        )
        data = self._request("GET", url)
        titles = data.get("titles") or []
        return [
            CheckoutTrend(
                brn=t.get("brn", ""),
                title=t.get("title", ""),
                checkout_count=t.get("checkoutCount", 0),
                branch_code=location_code,
                branch_name=t.get("branchName", ""),
                period=duration,
            )
            for t in titles
        ]

    # ── eResources API v1 ─────────────────────────────────────────────

    def search_eresources(
        self,
        keywords: str,
        content_type: str | None = None,
        subject: str | None = None,
        creator: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[EResource]:
        params: dict[str, Any] = {
            "Keywords": keywords,
            "Limit": limit,
            "Offset": offset,
        }
        if content_type:
            params["ContentType"] = content_type
        if subject:
            params["Subject"] = subject
        if creator:
            params["Creator"] = creator
        url = self._build_url(get_settings().eresource_base_url, "/SearchEResources", params)
        data = self._request("GET", url)
        results = data.get("results") or []
        return [
            EResource(
                title=r.get("title", ""),
                content_type=r.get("contentType", ""),
                summary=r.get("summary", ""),
                creator=r.get("creator", ""),
                subject=r.get("subject", ""),
                source=r.get("source", ""),
                url=r.get("url", ""),
                date=r.get("date", ""),
            )
            for r in results
        ]

    # ── Library API v1 ────────────────────────────────────────────────

    def get_libraries(self) -> list[LibraryBranch]:
        url = self._build_url(get_settings().library_base_url, "/GetLibraries")
        data = self._request("GET", url)
        libraries = data.get("libraries") or []
        return [
            LibraryBranch(
                code=lib.get("code", ""),
                name=lib.get("name", ""),
                address=lib.get("address", ""),
                postal_code=lib.get("postalCode", ""),
                telephone=lib.get("telephone", ""),
                latitude=lib.get("latitude", 0.0),
                longitude=lib.get("longitude", 0.0),
                weekday_hours=lib.get("weekdayHours", ""),
                saturday_hours=lib.get("saturdayHours", ""),
                sunday_hours=lib.get("sundayPublicHolidayHours", ""),
                has_event_space=lib.get("hasEvent", False),
                has_meeting_room=lib.get("hasMeetingRoom", False),
                has_exhibition_space=lib.get("hasExhibition", False),
                image_url=lib.get("imageUrl", ""),
                description=lib.get("description", ""),
            )
            for lib in libraries
        ]

    # ── Recommendation API v1 ─────────────────────────────────────────

    def get_recommendations(
        self,
        keywords: str | None = None,
        brn: str | None = None,
        isbn: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[Recommendation]:
        params: dict[str, Any] = {"Limit": limit}
        if keywords:
            params["Keywords"] = keywords
        if brn:
            params["BRN"] = brn
        if isbn:
            params["ISBN"] = isbn
        if category:
            params["Category"] = category
        url = self._build_url(
            get_settings().recommendation_base_url, "/GetRecommendations", params
        )
        data = self._request("GET", url)
        recs = data.get("recommendations") or []
        return [
            Recommendation(
                brn=r.get("brn", ""),
                title=r.get("title", ""),
                author=r.get("author", ""),
                isbn=r.get("isbn", ""),
                category=r.get("category", ""),
                book_cover=r.get("bookCover", ""),
            )
            for r in recs
        ]
