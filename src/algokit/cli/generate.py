import logging
from pathlib import Path

import click

from algokit.core.conf import get_algokit_config
from algokit.core.typed_client_generation import ClientGenerator

logger = logging.getLogger(__name__)


@click.group("generate")
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


def init_generator(answers: dict, path: Path) -> None:
    # copier is lazy imported for two reasons
    # 1. it is slow to import on first execution after installing
    # 2. the import fails if git is not installed (which we check above)
    # TODO: copier is typed, need to figure out how to force mypy to accept that or submit a PR
    #       to their repo to include py.typed file
    from copier.main import Worker  # type: ignore[import]

    cwd = Path.cwd()
    with Worker(
        src_path=str(path),
        dst_path=cwd,
        data=answers,
        quiet=True,
    ) as copier_worker:
        logger.debug(f"Running generator in {copier_worker.src_path}")
        copier_worker.run_copy()


try:
    cwd = Path.cwd()
    config = get_algokit_config(cwd)

    if config and "generators" in config:
        for generator_data in config["generators"].values():
            command = click.command(name=generator_data["name"], help=generator_data["description"])(init_generator)
            command = click.option(
                "answers",
                "--answer",
                "-a",
                multiple=True,
                help="Answers key/value pairs to pass to the template.",
                nargs=2,
                default=[],
                metavar="<key> <value>",
            )(command)
            command = click.option(
                "path",
                "--path",
                "-p",
                help=f"Path to {generator_data['name']} generator. (Default: {generator_data['path']})",
                type=click.Path(exists=True),
                default=generator_data["path"],
            )(command)

            generate_group.add_command(command)
except Exception as ex:
    logger.error(f"Error: {ex}")
