import logging

import subprocess

import click

logger = logging.getLogger(__name__)

def run(command: str):
    return subprocess.run(
        command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@click.group("sandbox", short_help="Manage the Algorand sandbox")
def sandbox_group():
    logger.debug("Hello I'm the sandbox command group")


@sandbox_group.command("start")
def start_sandbox():
    print("Starting the AlgoKit sandbox now...")
    result = run("docker network create -d bridge algokit-network")
    click.echo(result.args)
    result = run(
        "docker run -p 4001:4001 -p 4002:4002 -p 9392:9392 "
        + '--network algokit-network --label com.docker.compose.project="AlgoKit_sandbox" '
        + "--name algokit_algod -d makerxau/algorand-sandbox-dev:latest"
    )
    click.echo(result.args)
    result = run(
        "docker run -u postgres -e POSTGRES_USER=algorand -e POSTGRES_PASSWORD=algorand -e POSTGRES_DB=indexer_db "
        + '--network algokit-network --label com.docker.compose.project="AlgoKit_sandbox" '
        + "--name algokit_postgres -d postgres:13-alpine"
    )
    click.echo(result.args)
    result = run(
        "docker run -p 8980:8980 -e ALGOD_HOST=algokit_algod -e POSTGRES_HOST=algokit_postgres -e POSTGRES_PORT=5432 "
        + "-e POSTGRES_USER=algorand -e POSTGRES_PASSWORD=algorand -e POSTGRES_DB=indexer_db "
        + '--network algokit-network --label com.docker.compose.project="AlgoKit_sandbox" '
        + "--name algokit_indexer -d makerxau/algorand-indexer-dev:latest "
    )
    click.echo(result.args)


@sandbox_group.command("restart")
def restart_sandbox():
    logger.info("Restarting the sandbox now...")
    # TODO: the thing
    logger.info("Done!")
