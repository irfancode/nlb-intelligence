"""Example: Reading Trends & Analytics Demo.

Demonstrates branch trend analysis, genre popularity, and circulation metrics.
"""

from src.client import NLBClient
from src.analytics.reading_trends import ReadingTrendsAnalyzer
from src.analytics.collection_gaps import CollectionGapAnalyzer
from src.analytics.checkout_analysis import CirculationAnalyzer


def main():
    print("=" * 60)
    print("NLB Intelligence: Reading Trends & Analytics Demo")
    print("=" * 60)

    try:
        client = NLBClient()
    except Exception as e:
        print(f"\nError: {e}")
        print("Set NLB_APP_ID and NLB_API_KEY in .env or run without credentials for mock mode.")
        return

    trends = ReadingTrendsAnalyzer(client)
    gaps = CollectionGapAnalyzer(client)
    circulation = CirculationAnalyzer(client)

    print("\n1. Branch Trend Summaries (Tampines, Woodlands, Jurong)")
    print("-" * 40)
    summaries = trends.analyze_branch_trends(
        branch_codes=["TRL", "WRL", "JRL"]
    )
    for s in summaries:
        print(f"\n  {s.branch_name} ({s.branch_code}):")
        print(f"    Total checkouts (30d): {s.total_checkouts}")
        if s.top_titles:
            print(f"    Top title: {s.top_titles[0].title} ({s.top_titles[0].checkout_count} checkouts)")

    print("\n2. Collection Gap Analysis")
    print("-" * 40)
    gaps_found = gaps.identify_gaps(
        high_demand_keywords=[
            "artificial intelligence", "climate change",
            "mental health", "graphic novel",
        ],
    )
    for g in gaps_found[:4]:
        print(f"  {g.subject}: severity={g.gap_severity}, score={g.demand_score}")
        print(f"    -> {g.suggested_action}")

    print("\n3. Circulation Metrics (Regional Branches)")
    print("-" * 40)
    metrics = circulation.compute_circulation_metrics(
        branch_codes=["TRL", "WRL", "JRL", "CEN"]
    )
    print(f"  Total checkouts: {metrics.total_checkouts_period}")
    print(f"  Unique titles: {metrics.unique_titles_checked}")
    print(f"  Highest volume branch: {metrics.branch_with_highest_volume}")
    print(f"  Avg checkouts/title: {metrics.avg_checkouts_per_title}")

    print("\n4. Branch Comparison")
    print("-" * 40)
    comparisons = circulation.compare_branches(
        branch_codes=["TRL", "WRL", "JRL", "CEN", "SKG"]
    )
    for c in comparisons[:5]:
        print(f"  {c.branch_name}: {c.total_checkouts} checkouts, turnover={c.turnover_rate}%, genre={c.top_genre}")

    print("\n✅ Analytics demo complete!")
    client.close()


if __name__ == "__main__":
    main()
