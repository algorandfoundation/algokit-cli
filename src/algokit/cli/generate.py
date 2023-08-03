import logging
import shutil
from pathlib import Path

import click

from algokit.core.generate import load_generators, run_generator
from algokit.core.typed_client_generation import ClientGenerator

logger = logging.getLogger(__name__)


def _load_custom_generate_commands(project_dir: Path) -> dict[str, click.Command]:
    """
    Load custom generate commands from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: Custom generate commands.
    """

    generators = load_generators(project_dir)
    commands_table: dict[str, click.Command] = {}

    for generator in generators:

        @click.command(
            name=generator.name, help=generator.description or "Generator command description is not supplied."
        )
        @click.option(
            "answers",
            "--answer",
            "-a",
            multiple=True,
            help="Answers key/value pairs to pass to the template.",
            nargs=2,
            default=[],
            metavar="<key> <value>",
        )
        @click.option(
            "path",
            "--path",
            "-p",
            help=f"Path to {generator.name} generator. (Default: {generator.path})",
            type=click.Path(exists=True),
            default=generator.path,
        )
        def command(answers: dict, path: Path) -> None:
            if not shutil.which("git"):
                raise click.ClickException(
                    "Git not found; please install git and add to path.\n"
                    "See https://github.com/git-guides/install-git for more information."
                )

            return run_generator(answers, path)

        commands_table[generator.name] = command

    return commands_table


class GeneratorGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return_value = super().get_command(ctx, cmd_name)

        if return_value is not None:
            return return_value

        commands = _load_custom_generate_commands(Path.cwd())
        return commands.get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        predefined_command_names = super().list_commands(ctx)
        dynamic_commands = _load_custom_generate_commands(Path.cwd())
        dynamic_command_names = list(dynamic_commands)

        return sorted(predefined_command_names + dynamic_command_names)


@click.group("generate", cls=GeneratorGroup)
def generate_group() -> None:
    """Generate code for an Algorand project."""


@generate_group.command("client")
@click.argument(
    "app_spec_path_or_dir",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True, path_type=Path),
)
@click.option(
    "output_path_pattern",
    "--output",
    "-o",
    type=click.Path(exists=False),
    default=None,
    help="Path to the output file. The following tokens can be used to substitute into the output path:"
    " {contract_name}, {app_spec_dir}",
)
@click.option(
    "--language",
    "-l",
    default=None,
    type=click.Choice(ClientGenerator.languages()),
    help="Programming language of the generated client code",
)
def generate_client(output_path_pattern: str | None, app_spec_path_or_dir: Path, language: str | None) -> None:
    """Create a typed ApplicationClient from an ARC-32 application.json

    Supply the path to an application specification file or a directory to recursively search
    for "application.json" files"""
    if language is not None:
        generator = ClientGenerator.create_for_language(language)
    elif output_path_pattern is not None:
        extension = Path(output_path_pattern).suffix
        try:
            generator = ClientGenerator.create_for_extension(extension)
        except KeyError as ex:
            raise click.ClickException(
                "Could not determine language from file extension, Please use the --language option to specify a "
                "target language"
            ) from ex
    else:
        raise click.ClickException(
            "One of --language or --output is required to determine the client langauge to generate"
        )

    if not app_spec_path_or_dir.is_dir():
        app_specs = [app_spec_path_or_dir]
    else:
        app_specs = sorted(app_spec_path_or_dir.rglob("application.json"))
        if not app_specs:
            raise click.ClickException("No app specs found")
    for app_spec in app_specs:
        output_path = generator.resolve_output_path(app_spec, output_path_pattern)
        if output_path is not None:
            generator.generate(app_spec, output_path)
