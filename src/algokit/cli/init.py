from pathlib import Path

import click


@click.command("init", short_help="Initializes a new project.")
@click.argument(
    "path", required=False, type=click.Path(resolve_path=True, path_type=Path)
)
def init_command(path: Path):
    """Initializes a new project."""
    if path is None:
        print("Initialising in current directory")
        path = Path.cwd()
    # TODO: the thing
    print(f"Initialized the project in {click.format_filename(path)}")
