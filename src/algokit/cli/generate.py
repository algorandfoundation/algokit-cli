import logging
import shutil
from functools import cache
from pathlib import Path

import click

from algokit.core.generate import load_generators, run_generator
from algokit.core.typed_client_generation import AppSpecsNotFoundError, ClientGenerator

logger = logging.getLogger(__name__)


@cache
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
        @click.option(
            "--force",
            "-f",
            is_flag=True,
            required=False,
            default=False,
            type=click.BOOL,
            help="Executes generator without confirmation. Use with trusted sources only.",
        )
        def command(
            *,
            answers: list[tuple[str, str]],
            path: Path,
            force: bool,
        ) -> None:
            if not shutil.which("git"):
                raise click.ClickException(
                    "Git not found; please install git and add to path.\n"
                    "See https://github.com/git-guides/install-git for more information."
                )

            answers_dict = dict(answers)

            if not force and not click.confirm(
                "You are about to run a generator. Please make sure it's from a "
                "trusted source (for example, official AlgoKit Templates). Do you want to proceed?",
                default=False,
            ):
                logger.warning("Generator execution cancelled.")
                return None

            return run_generator(answers_dict, path)

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


@generate_group.command(
    "client",
    context_settings={
        "ignore_unknown_options": True,
    },
    add_help_option=False,
)
@click.argument(
    "app_spec_path_or_dir",
    type=click.Path(dir_okay=True, resolve_path=True, path_type=Path),
    required=False,
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
@click.option(
    "--version",
    "-v",
    "version",
    default=None,
    help="The client generator version to pin to, for example, 1.0.0. "
    "If no version is specified, AlgoKit checks if the client generator is installed and runs the installed version. "
    "If the client generator is not installed, AlgoKit runs the latest version. "
    "If a version is specified, AlgoKit checks if an installed version matches and runs the installed version. "
    "Otherwise, AlgoKit runs the specified version.",
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def generate_client(
    app_spec_path_or_dir: Path | None,
    output_path_pattern: str | None,
    language: str | None,
    version: str | None,
    args: tuple[str, ...],
) -> None:
    """Create a typed ApplicationClient from an ARC-32/56 application.json

    Supply the path to an application specification file or a directory to recursively search
    for "application.json" files"""

    generator = None
    if language is not None:
        generator = ClientGenerator.create_for_language(language, version)
    elif output_path_pattern is not None:
        extension = Path(output_path_pattern).suffix
        try:
            generator = ClientGenerator.create_for_extension(extension, version)
        except KeyError as ex:
            raise click.ClickException(
                "Could not determine language from file extension, Please use the --language option to specify a "
                "target language"
            ) from ex

    help_in_args = any(_is_help_flag(arg) for arg in args)
    help_in_positional = app_spec_path_or_dir is not None and _is_help_flag(app_spec_path_or_dir)

    if help_in_positional:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
    elif generator:
        if help_in_args:
            generator.show_help()
            return

        if app_spec_path_or_dir is None:
            raise click.ClickException("Missing argument 'APP_SPEC_PATH_OR_DIR'.")

        try:
            generator.generate_all(
                app_spec_path_or_dir,
                output_path_pattern,
                list(args),
                raise_on_path_resolution_failure=False,
            )
        except AppSpecsNotFoundError as ex:
            raise click.ClickException("No app specs found") from ex
    else:
        raise click.ClickException(
            "One of --language or --output is required to determine the client language to generate"
        )


HELP_FLAGS = ("--help", "-h")


def _is_help_flag(value: str | Path) -> bool:
    """Check if a value is a help flag (--help or -h)."""
    if isinstance(value, Path):
        return any(str(value).endswith(flag) for flag in HELP_FLAGS)
    return value in HELP_FLAGS
