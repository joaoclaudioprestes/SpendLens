import click

from .ingest import ingest


@click.group()
def cli() -> None:
    """SpendLens — personal spending analyzer."""
    pass


cli.add_command(ingest)
