import json
import logging
import pathlib
import platform
from re import sub

import algokit_client_generator
import click

from algokit.core import proc

logger = logging.getLogger(__name__)


def snake_case(s: str) -> str:
    return "_".join(sub("([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))).split()).lower()


def format_client_name(output: pathlib.Path, application_file: pathlib.Path) -> pathlib.Path:
    client_name = str(output).replace("%parent_dir%", snake_case(application_file.parent.name))

    if str(output).find("%name%") > 0:
        application_json = json.loads(application_file.read_text())
        client_name = str(output).replace("%name%", snake_case(application_json["contract"]["name"]))

    return pathlib.Path(client_name)


def check_node_installed() -> None:
    try:
        proc.run(
            ["npx", "--version"], bad_return_code_error_message="npx --version failed, please check your npx install"
        )
    except OSError as e:
        raise click.ClickException(
            "The TypeScript generator requires Node.js and npx to be installed. Please install Node.js to continue."
        ) from e

def generate_client_by_language (app_spec: pathlib.Path, output: pathlib.Path, language:str) -> None:
    if language.lower() == "typescript":
        check_node_installed()
        is_windows = platform.system() == "Windows"
        cmd = "npx" if not is_windows else "npx.cmd"
        proc.run(
            [
                cmd,
                "--yes",
                "@algorandfoundation/algokit-client-generator@v2.0.0-beta.1",
                "generate",
                "-a",
                str(app_spec),
                "-o",
                str(output),
            ],
            bad_return_code_error_message=f"Failed to run {' '.join(cmd)} for {app_spec}. Is npx installed and available on PATH?",
        )
        logger.info(
            f"Generating TypeScript client code for application specified in "
            f"{app_spec} and writing to {output}"
        )
    elif language.lower() == "python":
        logger.info(
            f"Generating Python client code for application specified in "
            f"{app_spec} and writing to {output}"
        )
        algokit_client_generator.generate_client(app_spec, pathlib.Path(output))


def generate_recursive_clients(app_spec: pathlib.Path, output: pathlib.Path, language: str) -> None:
    if app_spec.is_dir():
        for child in app_spec.iterdir():
            if child.is_dir():
                generate_recursive_clients(app_spec=child, output=output, language=language)
            elif child.name.lower() == "application.json":
                formatted_output = format_client_name(output=output, application_file=child)
                generate_client_by_language(app_spec=child, output=formatted_output, language=language)
    else:
        formatted_output = format_client_name(output=output, application_file=app_spec)
        generate_client_by_language(app_spec=app_spec, output=formatted_output, language=language)


@click.group("generate", short_help="Generate code for an AlgoKit application.")
def generate_group() -> None:
    pass


@generate_group.command("client")
@click.option(
    "app_spec",
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
    help="Path to the output file",
)
@click.option(
    "--language",
    default=None,
    type=click.Choice(["python", "typescript"]),
    help="Programming language of the generated client code",
)
def generate_client(app_spec: str, output: str, language: str | None) -> None:
    """
    typed ApplicationClient from and ARC-32 application.json
    """
    output_path = pathlib.Path(output)
    app_spec_path = pathlib.Path(app_spec)
    if language is None:
        extension = output_path.suffix
        if extension == ".ts":
            language = "typescript"
        elif extension == ".py":
            language = "python"
        else:
            raise click.ClickException(
                "Could not determine language from file extension, Please use the --language option to specify a "
                "target language"
            )

    generate_recursive_clients(app_spec=app_spec_path, output=output_path, language=language)
