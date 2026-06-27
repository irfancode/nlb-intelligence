from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class MaterialType(StrEnum):
    BOOK = "BOOK"
    DVD = "DVD"
    CD = "CD"
    BLURAY = "BLURAY"
    BRAILLE = "BRAILLE"
    EPHEMERA = "EPHEMERA"
    MAPS = "MAPS"
    MICROFILM = "MICROFILM"
    SERIALS = "SERIALS"
    THESIS = "THESIS"
    LARGE_PRINT = "LARGEPRINT"
    MUSIC_SCORE = "MUSICSCORE"
    KIT = "KIT"
    GAME = "GAME"


class Audience(StrEnum):
    ADULT = "adult"
    CHILDREN = "children"
    YOUTH = "youth"


class Availability(StrEnum):
    AVAILABLE = "On Shelf"
    CHECKED_OUT = "On Loan"
    IN_TRANSIT = "In-Transit"
    IN_PROCESS = "In-Process"
    RESERVED = "Reserved"
    LOST = "Lost"
    MISSING = "Missing"
    WITHDRAWN = "Withdrawn"


@dataclass
class LibraryBranch:
    code: str
    name: str
    address: str
    postal_code: str
    telephone: str
    latitude: float
    longitude: float
    weekday_hours: str
    saturday_hours: str
    sunday_hours: str
    has_event_space: bool = False
    has_meeting_room: bool = False
    has_exhibition_space: bool = False
    image_url: str = ""
    description: str = ""


@dataclass
class ItemAvailability:
    branch_code: str
    branch_name: str
    shelf_location: str
    call_number: str
    status_code: str
    status_desc: str
    collection: str


@dataclass
class TitleDetail:
    brn: str
    title: str
    authors: list[str] = field(default_factory=list)
    isbns: list[str] = field(default_factory=list)
    issns: list[str] = field(default_factory=list)
    format: str = ""
    edition: str = ""
    publisher: str = ""
    publish_date: str = ""
    subjects: list[str] = field(default_factory=list)
    summary: str = ""
    language: str = ""
    audience: str = ""
    physical_description: str = ""
    book_cover_small: str = ""
    book_cover_medium: str = ""
    book_cover_large: str = ""
    allow_reservation: bool = False
    is_restricted: bool = False
    active_reservations_count: int = 0


@dataclass
class TitleSearchResult:
    brn: str
    title: str
    author: str = ""
    isbn: str = ""
    format: str = ""
    publisher: str = ""
    publish_date: str = ""
    language: str = ""
    subjects: list[str] = field(default_factory=list)
    book_cover: str = ""
    availability: str = ""


@dataclass
class EResource:
    title: str
    content_type: str
    summary: str = ""
    creator: str = ""
    subject: str = ""
    source: str = ""
    url: str = ""
    date: str = ""


@dataclass
class Recommendation:
    brn: str
    title: str
    author: str = ""
    isbn: str = ""
    category: str = ""
    book_cover: str = ""


@dataclass
class CheckoutTrend:
    brn: str
    title: str
    checkout_count: int
    branch_code: str
    branch_name: str
    period: str


@dataclass
class CollectionRecord:
    title_english: str
    title_native: str = ""
    author_english: str = ""
    author_native: str = ""
    publisher: str = ""
    description: str = ""
    subjects: list[str] = field(default_factory=list)
    language: str = ""
    digital_id: str = ""
    url: str = ""
    resource_type: str = ""
    collection_hierarchy: list[str] = field(default_factory=list)
    date: str = ""
    rights: str = ""
