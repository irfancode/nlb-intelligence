"""Example: Geospatial Intelligence Demo.

Demonstrates catchment analysis, accessibility scoring, and placement recommendations.
"""

from src.client import NLBClient
from src.geospatial.catchment_analysis import GeospatialIntelligence


def main():
    print("=" * 60)
    print("NLB Intelligence: Geospatial & Urban Intelligence Demo")
    print("=" * 60)

    try:
        client = NLBClient()
    except Exception as e:
        print(f"\nError: {e}")
        return

    geo = GeospatialIntelligence(client)

    print("\n1. Library Catchment Areas (2km radius)")
    print("-" * 40)
    areas = geo.compute_catchment_areas(radius_km=2.0)
    for a in areas[:5]:
        overlap = ", ".join(a.overlapping_branches[:3]) or "none"
        print(f"  {a.branch_name}: pop~{a.estimated_population_served:,}, "
              f"nearest={a.distance_to_nearest}km, overlap=[{overlap}]")

    print("\n2. Accessibility Audit")
    print("-" * 40)
    scores = geo.accessibility_audit()
    for s in scores[:5]:
        print(f"  {s.branch_name}: overall={s.overall_accessibility}, "
              f"walk={s.walkability_index}, transit={s.public_transport_access}")

    print("\n3. New Location Recommendations")
    print("-" * 40)
    for rec in geo.suggest_new_locations():
        print(f"  [{rec.priority}] {rec.proposed_area}")
        print(f"    Density: {rec.population_density}")
        print(f"    Nearest library: {rec.distance_to_nearest}km")
        print(f"    Why: {rec.rationale}")
        print()

    print("\n4. Branch Clusters")
    print("-" * 40)
    for cluster, branches in geo.branch_clustering().items():
        print(f"  {cluster}: {', '.join(branches)}")

    print("\n✅ Geospatial analysis complete!")
    client.close()


if __name__ == "__main__":
    main()
