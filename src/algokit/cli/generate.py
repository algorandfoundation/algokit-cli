import json
import logging
import pathlib
from re import sub

import algokit_client_generator
import click

from algokit.core import proc

logger = logging.getLogger(__name__)


def snake_case(s: str) -> str:
    return "_".join(sub("([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))).split()).lower()


def format_client_name(output: pathlib.Path, application_file: pathlib.Path) -> str:
    client_name = str(output).replace("%parent_dir%", snake_case(application_file.parent.name))

    if str(output).find("%name%") > 0:
        application_json = json.load(pathlib.Path.open(application_file))
        client_name = str(output).replace("%name%", snake_case(application_json["contract"]["name"]))

    return client_name


def check_node_installed() -> None:
    try:
        proc.run(
            ["npx", "--version"], bad_return_code_error_message="npx --version failed, please check your npx install"
        )
    except OSError as e:
        raise click.ClickException(
            "The TypeScript generator requires Node.js and npx to be installed. Please install Node.js to continue."
        ) from e


def generate_clients(app_spec: pathlib.Path, output: pathlib.Path) -> None:
    if app_spec.is_dir():
        for child in app_spec.iterdir():
            if child.is_dir():
                generate_clients(child, output)
            elif child.name.lower() == "application.json":
                formatted_output = format_client_name(output=output, application_file=child)
                logger.info(
                    f"Generating Python client code for application specified in "
                    f"{child} and writing to {formatted_output}"
                )
                algokit_client_generator.generate_client(child, pathlib.Path(formatted_output))
    else:
        formatted_output = format_client_name(output=output, application_file=app_spec)
        logger.info(
            f"Generating Python client code for application specified in {app_spec} and writing to {formatted_output}"
        )
        algokit_client_generator.generate_client(app_spec, pathlib.Path(formatted_output))


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
    help="Path to the application specification file",
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
    Generate a client.
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
                f"Unsupported file extension: {extension}. Please use '.py' for Python or .ts' for TypeScript."
            )

    if language.lower() == "typescript":
        check_node_installed()
        proc.run(
            [
                "npx",
                "--yes",
                "@algorandfoundation/algokit-client-generator@v2.0.0-beta.1",
                "generate",
                "-a",
                app_spec,
                "-o",
                output,
            ],
            bad_return_code_error_message="npx failed, please check your npm",
        )
        logger.info(
            f"Generating TypeScript client code for application specified in "
            f"{app_spec_path} and writing to {output_path}"
        )
    elif language.lower() == "python":
        generate_clients(app_spec=app_spec_path, output=output_path)
