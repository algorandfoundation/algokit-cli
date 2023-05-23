import logging
import pathlib
import subprocess

import algokit_client_generator
import click
import json
from re import sub

logger = logging.getLogger(__name__)


def snake_case(s: str) -> str:
  return '_'.join(
    sub('([A-Z][a-z]+)', r' \1',
    sub('([A-Z]+)', r' \1',
    s.replace('-', ' '))).split()).lower()


def check_node_installed() -> None:
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise click.ClickException(
            "The TypeScript generator requires Node.js and npx to be installed. Please install Node.js to continue."
        ) from e


def walk_dir(app_spec: pathlib.Path, output: pathlib.Path) -> None:
    for child in app_spec.iterdir():
        if child.is_dir():
            walk_dir(child, output)
        elif child.name.lower() == "application.json":
            output_replaced = str(output).replace("%parent_dir%", snake_case(child.parent.name))

            if str(output).find("%name%") > 0:
                application_file = open(str(child))
                application_json = json.load(application_file)
                output_replaced = str(output).replace("%name%", snake_case(application_json["contract"]["name"]))

            logger.info(
                f"Generating Python client code for application specified in {child} and writing to {output_replaced}"
            )
            algokit_client_generator.generate_client(child, pathlib.Path(output_replaced))



@click.group("generate", short_help="Generate code for an AlgoKit application.")
def generate_group() -> None:
    pass


@generate_group.command("client")
@click.option(
    'app_spec',
    '--appspec',
    '-a',
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    default='./application.json',
    help='Path to the application specification file'
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
        subprocess.run(
            [
                "npx",
                "--yes",
                "@algorandfoundation/algokit-client-generator@v2.0.0-beta.1",
                "generate",
                "-a",
                app_spec,
                "-o",
                output_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(
            f"Generating TypeScript client code for application specified in {app_spec} and writing to {output_path}"
        )
    elif language.lower() == "python":
        walk_dir(app_spec=pathlib.Path(app_spec), output=pathlib.Path(output))

        # algokit_client_generator.generate_client(pathlib.Path(app_spec), output_path)
        # logger.info(
        #     f"Generating Python client code for application specified in {app_spec} and writing to {output_path}"
        # )
