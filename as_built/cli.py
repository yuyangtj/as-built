"""
The CLI is the entry point for running a campaign and inspecting its events.

Three commands for now:
  init  — create the events table
  run   — run the campaign for N ticks
  tail  — print the most recent events
"""

import click

from as_built import event_store
from as_built.orchestrator import Orchestrator


@click.group()
def cli() -> None:
    """as-built — a data platform with a biography, operated by agents."""


@cli.command()
def init() -> None:
    """Create the events table. Idempotent."""
    event_store.init()
    click.echo("event log schema ready.")


@cli.command()
@click.option("--ticks", default=50, show_default=True,
              help="How many ticks to run.")
def run(ticks: int) -> None:
    """Run a campaign for N ticks."""
    o = Orchestrator()
    o.run(ticks)
    click.echo(
        f"ran {ticks} ticks. "
        f"backlog: {o.backlog.count('open')} open, "
        f"{o.backlog.count('resolved')} resolved."
    )


@cli.command()
@click.option("-n", default=20, show_default=True,
              help="How many events to show.")
def tail(n: int) -> None:
    """Print the most recent events, oldest first."""
    events = event_store.tail(n)
    if not events:
        click.echo("(no events yet — run a campaign first)")
        return
    for e in events:
        subj = f" [{e.subject[:8]}]" if e.subject else ""
        note = e.payload.get("note") or e.payload.get("body") or ""
        if note:
            note = f"  — {note}"
        click.echo(f"t{e.tick:04d} {e.type:30s} {e.actor:25s}{subj}{note}")
