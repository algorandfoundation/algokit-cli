from pathlib import Path
import logging

import click

logger = logging.getLogger(__name__)


@click.command("init", short_help="Initializes a new project.")
@click.argument("path", required=False, type=click.Path(resolve_path=True, path_type=Path))
def init_command(path: Path):
    """Initializes a new project."""
    if path is None:
        logger.info("Initialising in current directory")
        path = Path.cwd()
    # TODO: the thing
    logger.info(f"Initialized the project in {click.format_filename(path)}")
