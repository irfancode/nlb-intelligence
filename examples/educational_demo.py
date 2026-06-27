"""Example: Educational & Research Tools Demo.

Demonstrates curriculum mapping, timeline exploration, and citation mining.
"""

from src.client import NLBClient
from src.educational.curriculum_mapper import CurriculumMapper, TimelineExplorer, CitationMiner


def main():
    print("=" * 60)
    print("NLB Intelligence: Educational & Research Tools Demo")
    print("=" * 60)

    try:
        client = NLBClient()
    except Exception as e:
        print(f"\nError: {e}")
        return

    mapper = CurriculumMapper(client)
    timeline = TimelineExplorer(client)
    miner = CitationMiner(client)

    print("\n1. Curriculum-Aligned Resource Mapping (Primary)")
    print("-" * 40)
    topics = mapper.map_curriculum_topics(levels=["Primary"])
    for t in topics[:6]:
        print(f"  [{t.level}] {t.subject}: {t.topic} ({t.resource_count} resources)")
        if t.suggested_keywords:
            print(f"    Keywords: {', '.join(t.suggested_keywords)}")

    print("\n2. Curriculum-Aligned Resource Mapping (Secondary)")
    print("-" * 40)
    sec_topics = mapper.map_curriculum_topics(levels=["Secondary"])
    for t in sec_topics[:6]:
        print(f"  [{t.level}] {t.subject}: {t.topic} ({t.resource_count} resources)")

    print("\n3. Historical Timeline Explorer (Singapore, decadal)")
    print("-" * 40)
    nodes = timeline.build_timeline(
        subject="singapore",
        years=range(1960, 2021, 20),
    )
    for n in nodes[:8]:
        desc = n.description[:60] + "..." if len(n.description) > 60 else n.description
        print(f"  {n.year}: {n.title}")
        print(f"    {desc}")

    print("\n4. Publication Density by Decade")
    print("-" * 40)
    density = timeline.event_density_analysis(subject="singapore")
    for d in density[:8]:
        print(f"  {d['decade']}s: {d['publication_count']} publications")

    print("\n5. Citation Mining")
    print("-" * 40)
    citations = miner.mine_citations(keyword="singapore history", limit=5)
    for c in citations:
        print(f"  - {c.citation_text}")

    print("\n✅ Educational tools demo complete!")
    client.close()


if __name__ == "__main__":
    main()
