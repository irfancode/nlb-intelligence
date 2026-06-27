#!/usr/bin/env python3
"""NLB Intelligence CLI - Explore Singapore's Library Intelligence."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from src.config import get_settings

app = typer.Typer(help="NLB Intelligence Toolkit - Unlock insights from Singapore's National Library Board APIs & Datasets")
console = Console()


@app.callback()
def callback():
    """NLB Intelligence CLI"""
    settings = get_settings()
    if not settings.has_credentials:
        console.print(
            "[yellow]⚠ No NLB credentials found. Set NLB_APP_ID and NLB_API_KEY in .env[/yellow]\n"
            "  Request API access: https://go.gov.sg/nlblabs-form"
        )


@app.command()
def search(
    keywords: str = typer.Argument(..., help="Search keywords"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Filter by branch code (e.g. TRL, CEN)"),
):
    """Search NLB catalogue for books and media."""
    from src.client import NLBClient
    try:
        client = NLBClient()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    locations = [branch] if branch else None
    results = client.search_titles(keywords=keywords, limit=limit, locations=locations)
    client.close()

    if not results:
        console.print(f"[yellow]No results for '{keywords}'[/yellow]")
        return

    table = Table(title=f"Search Results: '{keywords}'")
    table.add_column("Title", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Year", style="yellow")
    table.add_column("Availability", style="magenta")

    for r in results:
        table.add_row(r.title, r.author or "-", r.publish_date, r.availability or "-")

    console.print(table)


@app.command()
def details(
    brn: Optional[str] = typer.Option(None, "--brn", help="Book Reference Number"),
    isbn: Optional[str] = typer.Option(None, "--isbn", help="ISBN"),
):
    """Get detailed information about a title."""
    from src.client import NLBClient
    if not brn and not isbn:
        console.print("[red]Provide either --brn or --isbn[/red]")
        raise typer.Exit(1)

    client = NLBClient()
    detail = client.get_title_details(brn=brn, isbn=isbn)
    client.close()

    if not detail:
        console.print("[yellow]Title not found[/yellow]")
        return

    md = Markdown(
        f"# {detail.title}\n\n"
        f"**Author(s):** {', '.join(detail.authors)}\n\n"
        f"**Publisher:** {detail.publisher} ({detail.publish_date})\n\n"
        f"**Format:** {detail.format} | **Edition:** {detail.edition}\n\n"
        f"**Language:** {detail.language} | **Audience:** {detail.audience}\n\n"
        f"**Subjects:** {', '.join(detail.subjects)}\n\n"
        f"**Summary:** {detail.summary}\n\n"
        f"**Reservations:** {detail.active_reservations_count} active\n"
    )
    console.print(md)


@app.command()
def availability(
    brn: Optional[str] = typer.Option(None, "--brn", help="Book Reference Number"),
    isbn: Optional[str] = typer.Option(None, "--isbn", help="ISBN"),
):
    """Check availability of a title across NLB branches."""
    from src.client import NLBClient
    if not brn and not isbn:
        console.print("[red]Provide either --brn or --isbn[/red]")
        raise typer.Exit(1)

    client = NLBClient()
    items = client.get_availability(brn=brn, isbn=isbn)
    client.close()

    if not items:
        console.print("[yellow]No availability data[/yellow]")
        return

    table = Table(title="Availability by Branch")
    table.add_column("Branch", style="cyan")
    table.add_column("Call Number", style="green")
    table.add_column("Shelf Location", style="yellow")
    table.add_column("Status", style="magenta")

    for i in items:
        table.add_row(i.branch_name, i.call_number, i.shelf_location, i.status_desc)
    console.print(table)


@app.command()
def trends(
    branch: str = typer.Argument("TRL", help="Branch code"),
    duration: str = typer.Option("past30days", "--duration", "-d", help="Duration"),
):
    """Show most checked-out titles at a branch."""
    from src.client import NLBClient
    client = NLBClient()
    trends = client.get_checkout_trends(branch, duration)
    client.close()

    if not trends:
        console.print(f"[yellow]No trends data for {branch}[/yellow]")
        return

    table = Table(title=f"Top Checkouts: {branch} ({duration})")
    table.add_column("Title", style="cyan")
    table.add_column("Checkouts", style="green", justify="right")

    for t in trends[:15]:
        table.add_row(t.title, str(t.checkout_count))
    console.print(table)


@app.command()
def libraries():
    """List all NLB library branches with details."""
    from src.client import NLBClient
    client = NLBClient()
    libs = client.get_libraries()
    client.close()

    table = Table(title="NLB Libraries")
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Address", style="white")
    table.add_column("Hours (Weekday)", style="yellow")

    for lib in libs:
        table.add_row(lib.code, lib.name, lib.address, lib.weekday_hours)
    console.print(table)


@app.command()
def recommend(
    keywords: str = typer.Argument("", help="Keywords for recommendations"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recommendations"),
):
    """Get title recommendations from NLB."""
    from src.client import NLBClient
    client = NLBClient()
    recs = client.get_recommendations(keywords=keywords, limit=limit)
    client.close()

    if not recs:
        console.print("[yellow]No recommendations found[/yellow]")
        return

    table = Table(title=f"Recommendations: '{keywords}'")
    table.add_column("Title", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Category", style="yellow")

    for r in recs:
        table.add_row(r.title, r.author, r.category or "-")
    console.print(table)


@app.command()
def eresources(
    keywords: str = typer.Argument(..., help="Search keywords"),
    content_type: Optional[str] = typer.Option(None, "--type", "-t", help="Content type (ebooks, images, etc.)"),
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """Search NLB eResources."""
    from src.client import NLBClient
    client = NLBClient()
    results = client.search_eresources(keywords=keywords, content_type=content_type, limit=limit)
    client.close()

    if not results:
        console.print(f"[yellow]No eResources for '{keywords}'[/yellow]")
        return

    table = Table(title=f"eResources: '{keywords}'")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Source", style="yellow")

    for r in results:
        table.add_row(r.title, r.content_type, r.source)
    console.print(table)


@app.command()
def analytics(
    command: str = typer.Argument("summary", help="Analytics command: summary | gaps | branches | seasonal"),
    branch: str = typer.Option("TRL", "--branch", "-b"),
):
    """Run analytics on NLB data."""
    from src.client import NLBClient
    from src.analytics.checkout_analysis import CirculationAnalyzer
    from src.analytics.collection_gaps import CollectionGapAnalyzer

    client = NLBClient()

    if command == "summary":
        analyzer = CirculationAnalyzer(client)
        metrics = analyzer.compute_circulation_metrics(
            branch_codes=["TRL", "WRL", "JRL", "CEN", "SKG"]
        )
        console.print(Panel(
            f"[bold]Circulation Summary[/bold]\n\n"
            f"Total Checkouts: {metrics.total_checkouts_period}\n"
            f"Unique Titles: {metrics.unique_titles_checked}\n"
            f"Avg/Titles: {metrics.avg_checkouts_per_title}\n"
            f"Top Branch: {metrics.branch_with_highest_volume}\n"
            f"Turnover Rate: {metrics.collection_turnover_rate}",
            title="📊 Analytics Summary",
        ))

    elif command == "gaps":
        analyzer = CollectionGapAnalyzer(client)
        gaps = analyzer.identify_gaps()
        table = Table(title="Collection Gaps")
        table.add_column("Subject", style="cyan")
        table.add_column("Demand", style="yellow", justify="right")
        table.add_column("Severity", style="red")
        for g in gaps[:10]:
            table.add_row(g.subject, str(g.demand_score), g.gap_severity)
        console.print(table)

    elif command == "branches":
        analyzer = CirculationAnalyzer(client)
        comparisons = analyzer.compare_branches()
        table = Table(title="Branch Comparison")
        table.add_column("Branch", style="cyan")
        table.add_column("Checkouts", style="green", justify="right")
        table.add_column("Top Genre", style="yellow")
        table.add_column("Turnover", style="magenta", justify="right")
        for c in comparisons:
            table.add_row(c.branch_name, str(c.total_checkouts), c.top_genre, f"{c.turnover_rate}%")
        console.print(table)

    elif command == "seasonal":
        analyzer = CirculationAnalyzer(client)
        patterns = analyzer.seasonal_patterns()
        table = Table(title="Seasonal Patterns")
        table.add_column("Month", style="cyan")
        table.add_column("Avg Checkouts", style="green", justify="right")
        table.add_column("Peak Genre", style="yellow")
        table.add_column("Spike", style="magenta", justify="right")
        for p in patterns:
            table.add_row(p.month, str(p.avg_checkouts), p.peak_genre, str(p.holiday_spike))
        console.print(table)

    client.close()


@app.command()
def heritage(
    command: str = typer.Argument("entities", help="Heritage command: entities | clusters | narrative"),
    subject: str = typer.Option("singapore", "--subject", "-s"),
):
    """Explore Singapore's cultural heritage through NLB collections."""
    from src.client import NLBClient
    from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
    from src.heritage.entity_extraction import HeritageEntityExtractor

    client = NLBClient()

    if command == "entities":
        extractor = HeritageEntityExtractor(client)
        entities = extractor.extract_from_search(keywords=[subject])
        table = Table(title=f"Entities in '{subject}' Collection")
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Frequency", style="yellow", justify="right")
        for e in sorted(entities, key=lambda x: x.frequency, reverse=True)[:20]:
            table.add_row(e.text, e.label, str(e.frequency))
        console.print(table)

    elif command == "clusters":
        kg = HeritageKnowledgeGraphBuilder(client)
        clusters = kg.build_subject_clusters(
            seed_subjects=[subject, "History", "Culture", "Art"]
        )
        for seed, related in clusters.items():
            console.print(f"\n[bold cyan]{seed}[/bold cyan]: {', '.join(related[:8])}")

    elif command == "narrative":
        kg = HeritageKnowledgeGraphBuilder(client)
        narrative = kg.temporal_narrative(subject=subject)
        if narrative:
            console.print(f"[bold]Temporal Narrative: '{subject}'[/bold]")
            for item in narrative[:15]:
                console.print(f"  {item['year']}: {item['title']}")

    client.close()


def main():
    app()


if __name__ == "__main__":
    app()
