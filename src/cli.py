#!/usr/bin/env python3
"""NLB Intelligence CLI - Explore Singapore's Library Intelligence."""

from functools import wraps
from typing import Optional, Callable

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import get_settings
from src.client import NLBApiError

app = typer.Typer(
    help="NLB Intelligence Toolkit - Unlock insights from Singapore's National Library Board APIs & Datasets"
)
console = Console()


def handle_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NLBApiError as e:
            if e.status_code == 401:
                console.print("[red]Authentication failed. Check your NLB_APP_ID and NLB_API_KEY in .env[/red]")
                console.print("  Request access: https://go.gov.sg/nlblabs-form")
            elif e.status_code == 429:
                console.print("[yellow]Rate limit exceeded. Try again in a moment.[/yellow]")
            else:
                console.print(f"[red]API Error ({e.status_code}): {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    return wrapper


@app.callback()
def callback():
    if not get_settings().has_credentials:
        console.print(
            "[yellow]No NLB credentials found. Set NLB_APP_ID and NLB_API_KEY in .env[/yellow]\n"
            "  Request API access: https://go.gov.sg/nlblabs-form"
        )


def _client():
    from src.client import NLBClient
    return NLBClient()


@app.command()
@handle_errors
def search(
    keywords: str = typer.Argument(..., help="Search keywords"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Filter by branch code"),
):
    """Search NLB catalogue for books and media."""
    client = _client()
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
@handle_errors
def details(
    brn: Optional[str] = typer.Option(None, "--brn", help="Book Reference Number"),
    isbn: Optional[str] = typer.Option(None, "--isbn", help="ISBN"),
):
    """Get detailed information about a title."""
    if not brn and not isbn:
        console.print("[red]Provide either --brn or --isbn[/red]")
        raise typer.Exit(1)
    client = _client()
    detail = client.get_title_details(brn=brn, isbn=isbn)
    client.close()
    if not detail:
        console.print("[yellow]Title not found[/yellow]")
        return
    console.print(Panel(
        f"[bold]{detail.title}[/bold]\n\n"
        f"Author(s): {', '.join(detail.authors)}\n"
        f"Publisher: {detail.publisher} ({detail.publish_date})\n"
        f"Format: {detail.format} | Language: {detail.language}\n"
        f"Audience: {detail.audience}\n"
        f"Subjects: {', '.join(detail.subjects)}\n\n"
        f"{detail.summary}\n\n"
        f"[yellow]Reservations: {detail.active_reservations_count} active[/yellow]",
        title="Title Details",
    ))


@app.command()
@handle_errors
def availability(
    brn: Optional[str] = typer.Option(None, "--brn", help="Book Reference Number"),
    isbn: Optional[str] = typer.Option(None, "--isbn", help="ISBN"),
):
    """Check availability of a title across NLB branches."""
    if not brn and not isbn:
        console.print("[red]Provide either --brn or --isbn[/red]")
        raise typer.Exit(1)
    client = _client()
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
@handle_errors
def trends(
    branch: str = typer.Argument("TRL", help="Branch code"),
    duration: str = typer.Option("past30days", "--duration", "-d", help="Duration"),
):
    """Show most checked-out titles at a branch."""
    client = _client()
    data = client.get_checkout_trends(branch, duration)
    client.close()
    if not data:
        console.print(f"[yellow]No trends data for {branch}[/yellow]")
        return
    table = Table(title=f"Top Checkouts: {branch} ({duration})")
    table.add_column("Title", style="cyan")
    table.add_column("Checkouts", style="green", justify="right")
    for t in data[:15]:
        table.add_row(t.title, str(t.checkout_count))
    console.print(table)


@app.command()
@handle_errors
def libraries():
    """List all NLB library branches with details."""
    client = _client()
    libs = client.get_libraries()
    client.close()
    table = Table(title="NLB Libraries")
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Address", style="white")
    table.add_column("Weekday Hours", style="yellow")
    for lib in libs:
        table.add_row(lib.code, lib.name, lib.address, lib.weekday_hours)
    console.print(table)


@app.command()
@handle_errors
def recommend(
    keywords: str = typer.Argument("", help="Keywords for recommendations"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recommendations"),
):
    """Get title recommendations from NLB."""
    client = _client()
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
@handle_errors
def eresources(
    keywords: str = typer.Argument(..., help="Search keywords"),
    content_type: Optional[str] = typer.Option(None, "--type", "-t", help="Content type"),
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """Search NLB eResources."""
    client = _client()
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
@handle_errors
def analytics(
    command: str = typer.Argument("summary", help="Analytics: summary|gaps|branches|seasonal"),
):
    """Run analytics on NLB data."""
    from src.analytics.checkout_analysis import CirculationAnalyzer
    from src.analytics.collection_gaps import CollectionGapAnalyzer
    client = _client()

    if command == "summary":
        analyzer = CirculationAnalyzer(client)
        m = analyzer.compute_circulation_metrics()
        console.print(Panel(
            f"Total Checkouts: {m.total_checkouts_period}\n"
            f"Unique Titles: {m.unique_titles_checked}\n"
            f"Avg/Title: {m.avg_checkouts_per_title}\n"
            f"Top Branch: {m.branch_with_highest_volume}\n"
            f"Turnover: {m.collection_turnover_rate}",
            title="Circulation Summary",
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
        table.add_column("Avg", style="green", justify="right")
        table.add_column("Peak Genre", style="yellow")
        table.add_column("Spike", style="magenta", justify="right")
        for p in patterns:
            table.add_row(p.month, str(p.avg_checkouts), p.peak_genre, str(p.holiday_spike))
        console.print(table)
    client.close()


@app.command()
@handle_errors
def heritage(
    command: str = typer.Argument("entities", help="Heritage: entities|clusters|narrative"),
    subject: str = typer.Option("singapore", "--subject", "-s"),
):
    """Explore Singapore's cultural heritage through NLB collections."""
    from src.heritage.knowledge_graph import HeritageKnowledgeGraphBuilder
    from src.heritage.entity_extraction import HeritageEntityExtractor

    client = _client()
    if command == "entities":
        extractor = HeritageEntityExtractor(client)
        entities = extractor.extract_from_search(keywords=[subject])
        table = Table(title=f"Entities in '{subject}' Collection")
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Freq", style="yellow", justify="right")
        for e in sorted(entities, key=lambda x: x.frequency, reverse=True)[:20]:
            table.add_row(e.text, e.label, str(e.frequency))
        console.print(table)
    elif command == "clusters":
        kg = HeritageKnowledgeGraphBuilder(client)
        clusters = kg.build_subject_clusters(seed_subjects=[subject, "History", "Culture", "Art"])
        for seed, related in clusters.items():
            console.print(f"\n[bold cyan]{seed}[/bold cyan]: {', '.join(related[:8])}")
    elif command == "narrative":
        kg = HeritageKnowledgeGraphBuilder(client)
        narrative = kg.temporal_narrative(subject=subject)
        if narrative:
            console.print(f"[bold]Temporal Narrative: '{subject}'[/bold]")
            for item in narrative[:15]:
                console.print(f"  {item['year']}: {item['title']}")
        else:
            console.print(f"[yellow]No narrative data for '{subject}'[/yellow]")
    client.close()


def main():
    app()


if __name__ == "__main__":
    app()
