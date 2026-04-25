"""Adversarial Reviewer Agent — CLI entry point."""

from __future__ import annotations
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

load_dotenv()

from agent.graph import build_graph
from agent.state import AgentState

app = typer.Typer(add_completion=False)
console = Console()

_CHECK_LABELS = {
    "statistical":   "Statistical sanity",
    "claim_support": "Claim support",
    "citation":      "Citation quality",
    "language":      "Language red flags",
    "methodology":   "Methodology audit",
}


@app.command()
def run(
    source: str = typer.Argument(
        ...,
        help="PDF file path, plain-text file, or URL of the paper to review",
    ),
    output: Path = typer.Option(
        None, "--output", "-o",
        help="Save the report to this .md file",
    ),
):
    """
    Adversarial review of an academic paper.

    Attacks the paper like a hostile Nature reviewer: p-hacking detection,
    claim support verification, citation quality, language red flags,
    methodology gaps. Produces a structured report with severity levels.

    Examples:
      python main.py paper.pdf
      python main.py https://arxiv.org/abs/2301.00001
      python main.py paper.pdf -o report.md
    """
    console.print(Panel(
        Text.from_markup(
            "[bold red]Adversarial Reviewer Agent[/bold red]\n"
            f"Source: [cyan]{source}[/cyan]"
        ),
        expand=False,
    ))

    graph = build_graph()

    initial: AgentState = {
        "paper_source": source,
        "paper_text": "",
        "paper_metadata": {},
        "claims": [],
        "paper_type": "unclear",
        "planned_checks": [],
        "checks_completed": [],
        "findings": [],
        "errors": [],
        "final_report": None,
        "status": "running",
    }

    final: AgentState | None = None
    try:
        # stream_mode="values" yields the full accumulated state after each node
        for state in graph.stream(initial, stream_mode="values"):
            if final is not None:
                _print_progress_diff(state, final)
            final = state
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise

    if final is None:
        console.print("[red]No output produced.[/red]")
        sys.exit(1)

    report = final.get("final_report") or "No report generated."

    if output:
        output.write_text(report, encoding="utf-8")
        console.print(f"\n[green]Report saved →[/green] {output}")
    else:
        console.print()
        console.print(Markdown(report))

    if final.get("errors"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for err in final["errors"]:
            console.print(f"  · {err}")


def _print_progress_diff(current: dict, previous: dict) -> None:
    """Detect which node just ran by comparing consecutive states."""
    # Ingestion completed
    if not previous.get("paper_metadata") and current.get("paper_metadata"):
        title = (current["paper_metadata"].get("title") or "untitled")[:60]
        console.print(f"  [dim]✓ ingested[/dim] {title}")
        return

    # Classification completed (paper_type changed from default "unclear")
    if previous.get("paper_type") != current.get("paper_type"):
        console.print(f"  [dim]✓ classified[/dim] → {current['paper_type']}")
        return

    # Plan completed
    prev_checks = previous.get("planned_checks") or []
    curr_checks = current.get("planned_checks") or []
    if not prev_checks and curr_checks:
        claims_n = len(current.get("claims") or [])
        console.print(
            f"  [dim]✓ plan[/dim] {claims_n} claims · checks: {', '.join(curr_checks)}"
        )
        return

    # A check completed
    prev_done = previous.get("checks_completed") or []
    curr_done = current.get("checks_completed") or []
    if len(curr_done) > len(prev_done):
        last = curr_done[-1]
        n_findings = len(current.get("findings") or [])
        label = _CHECK_LABELS.get(last, last)
        console.print(f"  [dim]✓[/dim] {label} — {n_findings} finding(s) so far")


if __name__ == "__main__":
    app()
