"""Example: Recommendation Engine Demo.

Demonstrates hybrid recommendations, trending titles, and personalised discovery.
"""

from src.client import NLBClient
from src.recommendations.hybrid_recommender import HybridRecommender, UserPreferences


def main():
    print("=" * 60)
    print("NLB Intelligence: Recommendation Engine Demo")
    print("=" * 60)

    try:
        client = NLBClient()
    except Exception as e:
        print(f"\nError: {e}")
        return

    rec = HybridRecommender(client)

    print("\n1. Keyword-Based Recommendations")
    print("-" * 40)
    keyword_recs = rec.recommend_by_keyword(keyword="singapore fiction", limit=5)
    for r in keyword_recs:
        print(f"  [{r.score:.2f}] {r.title} by {r.author}")
        print(f"    Reason: {r.reason}")

    print("\n2. Trending at Tampines Regional")
    print("-" * 40)
    trending = rec.trending_recommendations(branch_code="TRL")
    for t in trending[:5]:
        print(f"  [{t.score:.2f}] {t.title} ({t.reason})")

    print("\n3. Personalised Recommendations")
    print("-" * 40)
    prefs = UserPreferences(
        favourite_genres=["Singapore History", "Southeast Asian Literature"],
        favourite_authors=["Lee Kuan Yew", "Sonny Liew"],
        preferred_languages=["English"],
        preferred_formats=["BOOK"],
    )
    personal = rec.personalized_for_user(preferences=prefs, limit=5)
    for p in personal:
        print(f"  [{p.score:.2f}] {p.title} by {p.author}")

    print("\n4. Serendipity / Diverse Discovery")
    print("-" * 40)
    discovery = rec.diverse_discovery(limit=8)
    for d in discovery:
        print(f"  {d.title} by {d.author}")

    print("\n✅ Recommendation demo complete!")
    client.close()


if __name__ == "__main__":
    main()
