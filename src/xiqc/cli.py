from __future__ import annotations

import typer

app = typer.Typer(help="XIQ-C command-line interface.")
aps_app = typer.Typer(help="AP commands.")
stations_app = typer.Typer(help="Station commands.")

app.add_typer(aps_app, name="aps")
app.add_typer(stations_app, name="stations")


@aps_app.command("list")
def aps_list() -> None:
    """List all adopted APs."""
    typer.echo("aps list — not yet implemented")


@aps_app.command("report")
def aps_report(serial: str = typer.Option(..., help="AP serial number")) -> None:
    """Show a report for a single AP."""
    typer.echo(f"aps report {serial} — not yet implemented")


@stations_app.command("list")
def stations_list() -> None:
    """List all associated stations."""
    typer.echo("stations list — not yet implemented")


def main() -> None:
    """Entry point for the xiqc CLI."""
    app()
