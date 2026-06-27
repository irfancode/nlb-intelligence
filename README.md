# NLB Intelligence

> **Unlock the full potential of Singapore's National Library Board (NLB) Labs APIs and open datasets.**  
> A comprehensive Python toolkit for building reading analytics, cultural heritage knowledge graphs, geospatial intelligence, hybrid recommendation engines, and operational dashboards.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![NLB Labs](https://img.shields.io/badge/NLB-Labs-orange)](https://www.nlb.gov.sg/main/partner-us/contribute-and-create-with-us/NLBLabs)

---

## 🧠 What You Can Build

| Intelligence Layer | What It Does | Data Source |
|---|---|---|
| **📊 Reading Trends** | Genre popularity by branch, checkout velocity, demographic profiles | Catalogue API + Checkout Trends |
| **🔍 Collection Gaps** | Underserved subjects, language gaps, format trends, weeding targets | Search + Trends APIs |
| **🏛️ Heritage KG** | Singapore cultural knowledge graph, entity extraction, temporal narratives | Catalogue + eResources APIs |
| **🗺️ Geospatial Intel** | Catchment areas, accessibility audits, new branch recommendations | Library API + geospatial datasets |
| **⭐ Hybrid Recommender** | Personalised + collaborative + trending recommendations | Rec API + Catalogue API |
| **📚 Educational Tools** | MOE curriculum mapping, timeline explorer, citation mining | Catalogue + eResources APIs |
| **🏢 Operations Intel** | Staffing forecasts, collection turnover, meeting room analytics | All APIs |

---

## 🚀 Quickstart

### 1. Get API Credentials

Fill out the [NLB Open Web Service Application Form](https://go.gov.sg/nlblabs-form) to receive your `NLB_APP_ID` and `NLB_API_KEY`.

### 2. Install

```bash
git clone https://github.com/irfancode/nlb-intelligence.git
cd nlb-intelligence
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your NLB credentials:
#   NLB_APP_ID=your_app_id
#   NLB_API_KEY=your_api_key
```

### 4. Run

```bash
# Search the catalogue
nlb-intel search "singapore history" --limit 10

# Check availability
nlb-intel availability --isbn 9789811234567

# See trending titles at a branch
nlb-intel trends TRL

# Run analytics
nlb-intel analytics summary
nlb-intel analytics gaps
nlb-intel analytics branches

# Explore heritage
nlb-intel heritage entities --subject "singapore culture"

# List all libraries
nlb-intel libraries
```

---

## 💻 Python Usage

```python
from src.client import NLBClient

client = NLBClient()

# Search titles
results = client.search_titles(
    keywords="artificial intelligence",
    material_types=["BOOK"],
    audiences=["adult"],
    limit=20,
)
for r in results:
    print(f"{r.title} by {r.author} - {r.availability}")

# Get detailed info
detail = client.get_title_details(isbn="9789811234567")
print(detail.summary)

# Check availability across branches
avail = client.get_availability(isbn="9789811234567")
for a in avail:
    print(f"{a.branch_name}: {a.status_desc}")

# Get checkout trends
trends = client.get_checkout_trends("TRL")
for t in trends[:5]:
    print(f"{t.title}: {t.checkout_count} checkouts")

# Get recommendations
recs = client.get_recommendations(keywords="singapore fiction")
for r in recs:
    print(f"{r.title} by {r.author}")

client.close()
```

### Analytics Modules

```python
from src.client import NLBClient
from src.analytics.reading_trends import ReadingTrendsAnalyzer
from src.analytics.collection_gaps import CollectionGapAnalyzer
from src.analytics.checkout_analysis import CirculationAnalyzer
from src.models import Audience

client = NLBClient()

# Reading trends
trends = ReadingTrendsAnalyzer(client)
summaries = trends.analyze_branch_trends(branch_codes=["TRL", "WRL"])
profile = trends.demographic_reading_profile(audience=Audience.ADULT)

# Collection gaps
gaps = CollectionGapAnalyzer(client)
gaps_found = gaps.identify_gaps()
lang_dist = gaps.language_distribution_analysis()

# Circulation metrics
circ = CirculationAnalyzer(client)
metrics = circ.compute_circulation_metrics()
comparisons = circ.compare_branches()

client.close()
```

### Heritage & Knowledge Graph

```python
from src.client import NLBClient
from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
from src.heritage.entity_extraction import HeritageEntityExtractor

client = NLBClient()

kg = HeritageKnowledgeGraphBuilder(client)
graph = kg.build_knowledge_graph(seed_keywords=["singapore history"])
print(f"Entities: {len(graph.entities)}")
print(f"Relationships: {len(graph.relationships)}")

extractor = HeritageEntityExtractor(client)
entities = extractor.extract_from_search(keywords=["singapore", "heritage"])
for e in entities[:10]:
    print(f"  {e.text} ({e.label}) - freq: {e.frequency}")

client.close()
```

### Geospatial Intelligence

```python
from src.client import NLBClient
from src.geospatial.catchment_analysis import GeospatialIntelligence

client = NLBClient()
geo = GeospatialIntelligence(client)

areas = geo.compute_catchment_areas(radius_km=2.0)
scores = geo.accessibility_audit()
suggestions = geo.suggest_new_locations()

client.close()
```

### Hybrid Recommender

```python
from src.client import NLBClient
from src.recommendations.hybrid_recommender import HybridRecommender, UserPreferences

client = NLBClient()
rec = HybridRecommender(client)

# By keyword
results = rec.recommend_by_keyword("singapore fiction", limit=10)

# By seed title
similar = rec.recommend_by_seed(seed_isbn="9789811234567")

# Trending
trending = rec.trending_recommendations(branch_code="TRL")

# Personalised
prefs = UserPreferences(
    favourite_genres=["Singapore History"],
    favourite_authors=["Lee Kuan Yew"],
    preferred_languages=["English"],
    preferred_formats=["BOOK"],
)
personalised = rec.personalized_for_user(prefs)

client.close()
```

### Educational Tools

```python
from src.client import NLBClient
from src.educational.curriculum_mapper import CurriculumMapper, TimelineExplorer, CitationMiner

client = NLBClient()

mapper = CurriculumMapper(client)
topics = mapper.map_curriculum_topics(levels=["Primary", "Secondary"])

timeline = TimelineExplorer(client)
nodes = timeline.build_timeline(subject="singapore", years=range(1965, 2025, 10))

miner = CitationMiner(client)
citations = miner.mine_citations(keyword="singapore history")

client.close()
```

### Operational Intelligence

```python
from src.client import NLBClient
from src.operational.staffing_forecast import (
    StaffingOptimizer, CollectionTurnoverOptimizer, MeetingRoomAnalytics
)

client = NLBClient()

staff = StaffingOptimizer(client)
forecasts = staff.forecast_staffing(branch_codes=["TRL", "WRL", "JRL"])

turnover = CollectionTurnoverOptimizer(client)
analysis = turnover.analyze_turnover()

rooms = MeetingRoomAnalytics(client)
room_data = rooms.analyze_meeting_rooms()

client.close()
```

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_client.py -v
```

---

## 📦 Project Structure

```
nlb-intelligence/
├── src/
│   ├── client.py              # Core NLB API client (all 4 APIs)
│   ├── config.py              # Settings & environment config
│   ├── models.py              # Data models / dataclasses
│   ├── cli.py                 # Typer CLI interface
│   ├── analytics/
│   │   ├── reading_trends.py  # Branch trends, genre popularity, profiles
│   │   ├── collection_gaps.py # Gap analysis, language/format distribution
│   │   └── checkout_analysis.py # Circulation metrics, seasonal patterns
│   ├── heritage/
│   │   ├── knowledge_graph.py # SG cultural KG, entity extraction, topic clusters
│   │   ├── entity_extraction.py # NER for people/places/events
│   │   └── topic_modeling.py # Temporal topic tracking, discursive shifts
│   ├── geospatial/
│   │   └── catchment_analysis.py # Catchment, accessibility, placement suggestions
│   ├── recommendations/
│   │   └── hybrid_recommender.py # Hybrid CF + CBF + trending recommender
│   ├── educational/
│   │   └── curriculum_mapper.py # Curriculum mapping, timeline, citation mining
│   └── operational/
│       └── staffing_forecast.py # Staffing, turnover, meeting room analytics
├── tests/
│   ├── fixtures.py           # Comprehensive mock data
│   ├── test_client.py        # 15+ client tests
│   ├── test_reading_trends.py
│   ├── test_collection_gaps.py
│   ├── test_checkout_analysis.py
│   ├── test_heritage.py
│   ├── test_geospatial.py
│   ├── test_recommender.py
│   ├── test_educational.py
│   └── test_operational.py
├── examples/
│   ├── reading_analytics_demo.py
│   ├── heritage_explorer_demo.py
│   ├── geospatial_demo.py
│   ├── recommender_demo.py
│   └── educational_demo.py
├── scripts/
│   └── download_datasets.py  # Download NLB CSV datasets from data.gov.sg
├── datasets/
│   └── README.md
├── README.md
├── BLOG.md
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## 📡 NLB APIs & Datasets Referenced

### APIs (require key via [go.gov.sg/nlblabs-form](https://go.gov.sg/nlblabs-form))

| API | Version | Base URL |
|---|---|---|
| Catalogue Search | v2 | `https://openweb.nlb.gov.sg/api/v2/Catalogue` |
| eResources Search | v1 | `https://openweb.nlb.gov.sg/api/v1/EResource` |
| Library | v1 | `https://openweb.nlb.gov.sg/api/v1/Library` |
| Title Recommendation | v1 | `https://openweb.nlb.gov.sg/api/v1/Recommendation` |

### Open Datasets (from [data.gov.sg](https://data.gov.sg/datasets?agencies=National%20Library%20Board%20(NLB)))

- Digitised Books & Magazines (37K records)
- Digitised Documents & Manuscripts (6.4K records)
- Archived Websites (88.8K records)
- Online Articles (3.6K records)
- Digitised Sound & Video (25.2K records)
- Digitised Images (76.5K records)
- Digitised Maps (467 records)
- Libraries Geospatial (KML)

---

## 📄 License

This project is licensed under the MIT License. NLB data is under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). National Library digital collection metadata datasets are for non-commercial use.

---

## 🙏 Acknowledgements

- [NLB Labs](https://www.nlb.gov.sg/main/partner-us/contribute-and-create-with-us/NLBLabs) for providing open APIs and datasets
- [data.gov.sg](https://data.gov.sg) for the open data platform
- [nlb_catalogue_client](https://github.com/kiritowu/nlb_catalogue_client) community SDK for inspiration
