import shutil
from pathlib import Path

import click

from algokit.cli.tui.init.example_selector import ExampleSelector
from algokit.core.init import (
    ALGOKIT_TEMPLATES_DIR,
    ALGOKIT_USER_DIR,
    _load_algokit_examples,
    _manage_templates_repository,
    _open_ide,
)


@click.command("example")
@click.argument("example_id", required=False)
def example_command(example_id: str) -> None:
    """Initialize a new project from an example template.

    Allows you to quickly create a new project by copying one of the official AlgoKit example templates.
    If no example ID is provided, launches an interactive selector to choose from available examples.
    The example will be copied to a new directory in your current location."""

    _manage_templates_repository()

    if not example_id:
        app = ExampleSelector()
        app.run()
        example_id = app.user_answers.get("example_id", "")
        if not example_id:
            return

    examples_config_path = Path.home() / ALGOKIT_USER_DIR / ALGOKIT_TEMPLATES_DIR / "examples" / "examples.yml"
    source_dir = Path.home() / ALGOKIT_USER_DIR / ALGOKIT_TEMPLATES_DIR / "examples" / example_id
    target_dir = Path.cwd() / example_id

    if not source_dir.exists():
        examples = _load_algokit_examples(str(examples_config_path.absolute()))
        click.echo(f"Example {example_id} not found")
        if example_id not in [example["id"] for example in examples]:
            click.echo("Available example ids:")
            for example in examples:
                click.echo(f"  {example['id']}")
        return

    shutil.copytree(source_dir, target_dir)
    click.echo(f"Created example {example_id}")
    _open_ide(target_dir)
