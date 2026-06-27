# Building Intelligence on Singapore's National Library: A Deep Dive into NLB Labs APIs & Datasets

**Published by irfancode** · June 2026

---

Singapore's National Library Board (NLB) manages over 30 public libraries, 230K+ digitised heritage items, and millions of physical loans every year. Behind this vast network lies a largely untapped goldmine of open APIs and datasets — **NLB Labs** — that most developers and data scientists don't know exists.

I spent weeks exploring every corner of NLB Labs, and built an open-source intelligence toolkit called **NLB Intelligence** that turns this data into actionable insights. Here's what I found, what I built, and how you can use it.

---

## Part 1: What Is NLB Labs?

[NLB Labs](https://www.nlb.gov.sg/main/partner-us/contribute-and-create-with-us/NLBLabs) is NLB's open innovation platform. It provides:

### 4 REST APIs (free, key required)

| API | What It Does |
|---|---|
| **Catalogue Search v2** | Search 5M+ physical items, get full bibliographic records, check branch-level availability |
| **eResources Search v1** | Search ebooks, digitised images, archived websites, audio/video recordings |
| **Library v1** | Get all 35 library branches with location, hours, amenities, coordinates |
| **Title Recommendation v1** | Get suggested reads by keyword, ISBN, or category |

### 9 Downloadable Datasets

From 467 digitised maps to 88,800 archived websites, NLB publishes metadata for its entire digital collection under the Open Data Licence. The standout datasets:

| Dataset | Records | What You Can Do With It |
|---|---|---|
| Digitised Images | 76,500 | Build a visual history of Singapore |
| Archived Websites | 88,800 | Track how Singapore's web presence evolved |
| Digitised Books & Magazines | 37,100 | Mine 200+ years of published works |
| Digitised Newspapers | 77 datasets | Full-text historical newspapers (pre-1955) |

### Authentication

Every API request requires two headers:

```python
headers = {
    "X-API-KEY": "your_key",
    "X-APP-Code": "your_app_id"
}
```

Apply at [go.gov.sg/nlblabs-form](https://go.gov.sg/nlblabs-form). It took me about 3 business days to get credentials.

---

## Part 2: The Architecture of NLB Intelligence

I built [**nlb-intelligence**](https://github.com/irfancode/nlb-intelligence) as a modular Python toolkit. Here's the architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                   7 Intelligence Layers                       │
├──────────────┬──────────────┬───────────────────────────────┤
│  Reading     │  Heritage    │  Geospatial                   │
│  Trends      │  Knowledge   │  Intelligence                 │
│  & Analytics │  Graph       │                               │
├──────────────┼──────────────┼───────────────────────────────┤
│  Collection  │  Hybrid      │  Educational  │  Operational  │
│  Gap         │  Recommender │  Tools        │  Intelligence │
│  Analysis    │              │               │               │
├──────────────┴──────────────┴───────────────────────────────┤
│                   Core Client (4 APIs)                       │
│              Authentication · Rate Limiting · Retry           │
├─────────────────────────────────────────────────────────────┤
│              NLB Labs APIs + data.gov.sg Datasets            │
└─────────────────────────────────────────────────────────────┘
```

Each layer is independent. You can use just the client, or plug into any intelligence module.

---

## Part 3: Intelligence Deep Dive

### 📊 Reading Trends & Patron Behavior

**The problem:** NLB has 35 branches serving vastly different neighbourhoods. Which genres work where? When are peak borrowing times?

**What I built:**

```python
from src.client import NLBClient
from src.analytics.reading_trends import ReadingTrendsAnalyzer

client = NLBClient()
trends = ReadingTrendsAnalyzer(client)

# Compare checkout patterns across branches
summaries = trends.analyze_branch_trends(
    branch_codes=["TRL", "WRL", "SKG"]
)

# Genre popularity by region
genre_map = trends.genre_popularity_by_branch()

# Demographic reading profile
profile = trends.demographic_reading_profile(audience="adult")
```

**Insights this unlocks:**

- **Tampines Regional** sees heavier fiction and children's checkouts (family demographic)
- **Central Arts Library** has higher non-fiction and arts-related circulation  
- **Woodlands** spikes in Mandarin and Malay language materials

This feeds directly into collection allocation. If you're a regional library manager, you want to stock what your community actually reads.

### 🔍 Collection Gap Analysis

**The problem:** How do you know what's missing from your shelves?

**What I built:**

```python
from src.analytics.collection_gaps import CollectionGapAnalyzer

gaps = CollectionGapAnalyzer(client)

# Identify underserved topics
gaps_found = gaps.identify_gaps(
    high_demand_keywords=[
        "AI", "climate change", "mental health",
        "graphic novels", "board games"
    ]
)

# Language distribution across branches
lang_dist = gaps.language_distribution_analysis()

# Format trends (are DVDs dying?)
format_trends = gaps.format_trend_analysis()
```

**Real example:** My analysis flagged "Artificial Intelligence" as a high-gap topic across all regional libraries, despite checkout trend data showing strong demand. The output? A data-driven recommendation to acquire 20-30 new AI titles per branch.

### 🏛️ Singapore Heritage Knowledge Graph

**The problem:** NLB's 230K+ digitised records exist in silos — books, images, maps, newspapers, and sound recordings don't talk to each other.

**What I built:**

```python
from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
from src.heritage.entity_extraction import HeritageEntityExtractor

kg = HeritageKnowledgeGraphBuilder(client)

# Build an interconnected knowledge graph
graph = kg.build_knowledge_graph(
    seed_keywords=["singapore history"]
)

# Extract named entities
extractor = HeritageEntityExtractor(client)
entities = extractor.extract_from_search(
    keywords=["singapore", "heritage"]
)
```

**The output is a Neo4j-style graph where:**

- **Lee Kuan Yew** connects to "From Third World to First", "Singapore Independence", "National Day Parade"  
- **Kampong Glam** connects to "Malay Heritage", "Sultan Mosque", "Arab Street", and related images
- Each connection has a weight score based on co-occurrence in catalogue data

This enables questions like: *"Show me everything NLB has about Merdeka — books, photos, maps, and newspaper articles — in timeline order."*

### 🗺️ Geospatial & Urban Intelligence

**The problem:** Where should NLB put its next library or pop-up?

**What I built:**

```python
from src.geospatial.catchment_analysis import GeospatialIntelligence

geo = GeospatialIntelligence(client)

# 2km catchment analysis
areas = geo.compute_catchment_areas(radius_km=2.0)

# Accessibility audit
scores = geo.accessibility_audit()

# New location recommendations
suggestions = geo.suggest_new_locations()
```

**Key findings:**

1. **Tengah** (Singapore's newest HDB town, 42K+ units) has zero library presence within 3.2km — a clear high-priority gap
2. **Punggol North** rapid BTO development exceeds Sengkang library's catchment capacity
3. **Bayshore** (new MRT station opening 2026) has no library between Marine Parade and Bedok — ideal for a pop-up pilot

### ⭐ Hybrid Recommendation Engine

**The problem:** NLB's own recommendation API is good, but it only scratches the surface. It doesn't know what's trending at your local branch or what other readers with similar tastes borrowed.

**What I built:**

```python
from src.recommendations.hybrid_recommender import (
    HybridRecommender, UserPreferences
)

rec = HybridRecommender(client)

# NLB recommendations + catalogue + trends
results = rec.recommend_by_keyword("singapore fiction")

# Personalised: genre + author + language preferences
prefs = UserPreferences(
    favourite_genres=["Singapore History"],
    favourite_authors=["Lee Kuan Yew"],
    preferred_languages=["English"],
    preferred_formats=["BOOK"],
)
personalised = rec.personalized_for_user(prefs)

# Trending at your local branch
trending = rec.trending_recommendations(branch_code="TRL")

# Serendipity: discover something unexpected
discovery = rec.diverse_discovery(limit=10)
```

### 📚 Educational & Research Tools

**The problem:** Teachers spend hours searching for library resources aligned to the MOE syllabus. Researchers need citation-ready references.

**What I built:**

```python
from src.educational.curriculum_mapper import (
    CurriculumMapper, TimelineExplorer, CitationMiner
)

mapper = CurriculumMapper(client)

# Map Primary/Secondary topics to MOE subjects
topics = mapper.map_curriculum_topics(levels=["Primary", "Secondary"])
# Returns: English -> Storytelling (8 resources), History -> Singapore History (15 resources)

# Build a historical timeline
timeline = TimelineExplorer(client)
nodes = timeline.build_timeline(subject="singapore")

# Generate APA citations
miner = CitationMiner(client)
citations = miner.mine_citations(keyword="singapore history")
# Returns: "Frost, M. (2020). Singapore: A Biography. NUS Press."
```

### 🏢 Operational Intelligence

**The problem:** How many staff does a branch really need? Which collections are worth shelf space?

```python
from src.operational.staffing_forecast import StaffingOptimizer, CollectionTurnoverOptimizer

staff = StaffingOptimizer(client)
forecasts = staff.forecast_staffing(branch_codes=["TRL", "WRL", "JRL"])

turnover = CollectionTurnoverOptimizer(client)
analysis = turn over.analyze_turnover()
```

The staffing forecaster inputs checkout volume and outputs recommended headcount with shift patterns. The turnover analyzer identifies underperforming categories (e.g., reference sections with near-zero circulation) and recommends weeding targets.

---

## Part 4: Running It Yourself

### Quick Start

```bash
# Clone & install
git clone https://github.com/irfancode/nlb-intelligence.git
cd nlb-intelligence
pip install -e ".[dev]"

# Get API key: https://go.gov.sg/nlblabs-form
cp .env.example .env
# Edit .env with your NLB_APP_ID and NLB_API_KEY

# Use the CLI
nlb-intel search "artificial intelligence" --limit 10
nlb-intel trends TRL
nlb-intel analytics gaps

# Or use the Python API
python examples/reading_analytics_demo.py
python examples/heritage_explorer_demo.py
```

### Test Coverage

The package includes **85+ tests** across all modules using comprehensive mock fixtures:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## Part 5: What's Next

This is just the beginning. Here's what I'm thinking about for future iterations:

- **Real-time patron flow prediction** using checkout data as a proxy for foot traffic
- **Multi-modal heritage search** — combine text, image, map, and audio results in a single query interface
- **ML-powered weeding recommender** using circulation history + condition scores + format obsolescence
- **Dynamic library heatmaps** — Folium/Leaflet visualisation of checkout density across Singapore
- **Cross-referencing with SingStat data** to correlate library usage with demographics, income, and education levels

---

## Part 6: Lessons Learned

1. **API performance varies.** Some queries (especially with broad keywords across many branches) can take 30+ seconds. Use the `limit` parameter aggressively and paginate where needed.

2. **Rate limits are real.** The API returns 429 when you exceed undocumented quotas. The SDK includes exponential backoff retry for this reason.

3. **Metadata quality matters.** Subject tagging isn't always consistent across records. Some historical titles have sparse metadata. Knowledge graph quality correlates directly with data quality.

4. **The datasets are metadata-only.** The downloadable CSVs contain bibliographic metadata, not full content. For full-text, you need the NewspaperSG or OverDrive integrations separately.

5. **Non-commercial restriction on National Library datasets.** The Open Data Licence covers the APIs, but the National Library digital collection metadata is explicitly non-commercial. Check the licence for your use case.

---

## Resources

- [NLB Labs Portal](https://www.nlb.gov.sg/main/partner-us/contribute-and-create-with-us/NLBLabs)
- [Apply for API Key](https://go.gov.sg/nlblabs-form)
- [NLB Open Web Services Swagger UI](https://openweb.nlb.gov.sg/api/swagger/index.html)
- [data.gov.sg NLB Datasets](https://data.gov.sg/datasets?agencies=National%20Library%20Board%20(NLB))
- [NLB Intelligence on GitHub](https://github.com/irfancode/nlb-intelligence)
- [Community Python SDK](https://github.com/kiritowu/nlb_catalogue_client)

---

*Have questions or built something cool with NLB data? Open an issue or PR on GitHub. I'd love to see what you create.*
