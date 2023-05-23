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
    default='python',
    help='Programming language of the generated client code'
)
def generate_client(app_spec: str, output: str, language: str):
    """
    Generate a client.
    """
    if language == 'typescript':
        check_node_installed()

    logger.info(f"Generating {language} client code for application specified in {app_spec} and writing to {output}")

    algokit_client_generator.generate_client(pathlib.Path(app_spec), pathlib.Path(output))
