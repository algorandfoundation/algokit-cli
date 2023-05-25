import json
import logging
import platform
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import algokit_client_generator
import click

from algokit.core import proc

logger = logging.getLogger(__name__)

TypedClientGenerator = Callable[[Path, Path], None]
AllowedLanguages = Literal["python", "typescript"]
TYPESCRIPT_NPX_PACKAGE = "@algorandfoundation/algokit-client-generator@v2.0.0-beta.1"


def snake_case(s: str) -> str:
    s = s.replace("-", " ")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"[-\s]", "_", s).lower()


def format_client_name(output: str, application_file: Path) -> Path:
    client_name = output.replace("%parent_dir%", snake_case(application_file.parent.name))

    if "%name%" in output:
        application_json = json.loads(application_file.read_text())
        client_name = output.replace("%name%", snake_case(application_json["contract"]["name"]))

    return Path(client_name)


def _generate_python_client(app_spec: Path, output: Path) -> None:
    logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
    algokit_client_generator.generate_client(app_spec, Path(output))


def _generate_typescript_client(app_spec: Path, output: Path) -> None:
    is_windows = platform.system() == "Windows"
    npx = "npx.cmd" if is_windows else "npx"
    cmd = [
        npx,
        "--yes",
        TYPESCRIPT_NPX_PACKAGE,
        "generate",
        "-a",
        str(app_spec),
        "-o",
        str(output),
    ]
    logger.info(f"Generating TypeScript client code for application specified in {app_spec} and writing to {output}")
    try:
        proc.run(
            cmd,
            bad_return_code_error_message=f"Failed to run {' '.join(cmd)} for {app_spec}.",
        )
    except OSError as e:
        raise click.ClickException("Typescript generator requires Node.js and npx to be installed.") from e


EXTENSION_TO_LANGUAGE: dict[str, AllowedLanguages] = {
    ".py": "python",
    ".ts": "typescript",
}
LANGUAGE_TO_GENERATOR: dict[AllowedLanguages, TypedClientGenerator] = {
    "python": _generate_python_client,
    "typescript": _generate_typescript_client,
}


@click.group("generate")
def generate_group() -> None:
    """Generate code for an Algorand project."""


@generate_group.command("client")
@click.option(
    "app_spec_or_dir",
    "--appspec",
    "-a",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    default="./application.json",
    help="Path to an application specification file or a directory to recursively search for application.json",
)
@click.option(
    "output",
    "--output",
    "-o",
    type=click.Path(exists=False, dir_okay=False, resolve_path=True),
    default="./client_generated.py",
    help="Path to the output file. The following tokens can be used to substitute into the output path:"
    " %name%, %parent_dir% ",
)
@click.option(
    "--language",
    default=None,
    type=click.Choice(list(LANGUAGE_TO_GENERATOR.keys())),
    help="Programming language of the generated client code",
)
def generate_client(app_spec_or_dir: str, output: str, language: AllowedLanguages | None) -> None:
    """
    Create a typed ApplicationClient from an ARC-32 application.json
    """
    app_spec_path = Path(app_spec_or_dir)
    if language is None:
        language = EXTENSION_TO_LANGUAGE.get(Path(output).suffix)
        if language is None:
            raise click.ClickException(
                "Could not determine language from file extension, Please use the --language option to specify a "
                "target language"
            )

    app_specs = list(app_spec_path.rglob("application.json")) if app_spec_path.is_dir() else [app_spec_path]
    for app_spec in app_specs:
        formatted_output = format_client_name(output=output, application_file=app_spec)
        LANGUAGE_TO_GENERATOR[language](app_spec, formatted_output)
