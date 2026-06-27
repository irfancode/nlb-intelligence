"""Example: Heritage Knowledge Graph Demo.

Demonstrates entity extraction, topic modeling, and cultural heritage analysis.
"""

from src.client import NLBClient
from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
from src.heritage.entity_extraction import HeritageEntityExtractor
from src.heritage.topic_modeling import TopicModelingEngine


def main():
    print("=" * 60)
    print("NLB Intelligence: Singapore Heritage Knowledge Graph Demo")
    print("=" * 60)

    try:
        client = NLBClient()
    except Exception as e:
        print(f"\nError: {e}")
        return

    kg = HeritageKnowledgeGraphBuilder(client)
    extractor = HeritageEntityExtractor(client)
    topics = TopicModelingEngine(client)

    print("\n1. Building Knowledge Graph from NLB Catalogue")
    print("-" * 40)
    graph = kg.build_knowledge_graph(
        seed_keywords=["singapore history", "singapore culture"]
    )
    print(f"  Entities found: {len(graph.entities)}")
    top_entities = sorted(
        graph.entities.values(), key=lambda e: e.mentions, reverse=True
    )[:10]
    for e in top_entities:
        print(f"  - {e.name} ({e.entity_type}, {e.mentions} mentions)")

    print("\n2. Extracted Named Entities")
    print("-" * 40)
    entities = extractor.extract_from_search(
        keywords=["singapore", "history", "heritage"]
    )
    locs = [e for e in entities if e.label == "LOC"][:5]
    pers = [e for e in entities if e.label == "PER"][:5]
    print(f"  Locations: {', '.join(e.text for e in locs)}")
    print(f"  People: {', '.join(e.text for e in pers)}")

    print("\n3. Topic Trends Over Decades")
    print("-" * 40)
    trends = topics.track_topic_over_time(
        topics=["hawker", "education", "multiculturalism"]
    )
    for t in trends:
        print(f"  {t.topic} ({t.decade}s): {t.mention_count} mentions")

    print("\n4. Subject Clusters")
    print("-" * 40)
    clusters = kg.build_subject_clusters(
        seed_subjects=["Art", "History", "Science"]
    )
    for seed, related in clusters.items():
        print(f"  {seed}: {', '.join(related[:5])}")

    print("\n5. Discursive Shifts: 'Singapore Identity'")
    print("-" * 40)
    shifts = topics.detect_discursive_shifts(topic="singapore identity")
    for s in shifts:
        print(f"  {s.period_start}-{s.period_end}: {s.frequency_change:+.1f}%")
        print(f"    {s.narrative_description}")

    print("\n✅ Heritage analysis complete!")
    client.close()


if __name__ == "__main__":
    main()
