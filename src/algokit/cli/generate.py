import os
import subprocess
import logging
import click
import algokit_client_generator
import pathlib

logger = logging.getLogger(__name__)


def check_node_installed():
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise click.ClickException(
            "The TypeScript generator requires Node.js and npx to be installed. Please install Node.js to continue.")


@click.group("generate", short_help="Generate code for an AlgoKit application.")
def generate_group():
    pass


@generate_group.command("client")
@click.option(
    'app_spec',
    '--appspec',
    '-a',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default='./application.json',
    help='Path to the application specification file'
)
@click.option(
    'output',
    '--output',
    '-o',
    type=click.Path(exists=False, dir_okay=False, resolve_path=True),
    default='./client_generated.py',
    help='Path to the output file'
)
@click.option(
    '--language',
    help='Programming language of the generated client code'
)
def generate_client(app_spec: str, output: str, language: str):
    """
    Generate a client.
    """
    if language is None:
        _, extension = os.path.splitext(output)
        if extension == '.ts':
            language = 'typescript'
        elif extension == '.py':
            language = 'python'
        else:
            raise click.ClickException(f"Unsupported file extension: {extension}."
                                       f"Please use '.py' for Python or .ts' for TypeScript.")

    if language.lower() == 'typescript':
        check_node_installed()
        subprocess.run(["npx", "--yes", "@algorandfoundation/algokit-client-generator@v2.0.0-beta.1", "generate", "-a",
                        app_spec, "-o", output], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Generating TypeScript client code for application specified in {app_spec} and writing to {output}")
    elif language.lower() == 'python':
        algokit_client_generator.generate_client(pathlib.Path(app_spec), pathlib.Path(output))
        logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
    else:
        raise click.ClickException(f"Unsupported language: {language}. Please select 'python' or 'typescript'.")
