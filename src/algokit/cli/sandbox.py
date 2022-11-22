import json
import logging
from typing import Any

import click
import httpx
from algokit.core import exec
from algokit.core.sandbox import ComposeFileStatus, ComposeSandbox

logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the AlgoKit sandbox")
def sandbox_group() -> None:
    try:
        compose_version_result = exec.run(
            ["docker", "compose", "version", "--format", "json"],
            bad_return_code_error_message=(
                "Docker Compose not found; please install Docker Compose and add to path.\n"
                "See https://docs.docker.com/compose/install/ for more information."
            ),
        )
    except IOError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    else:
        try:
            compose_version: dict[str, str] = json.loads(compose_version_result.output)
            compose_version_str = compose_version["version"]
            compose_major, compose_minor, *_ = map(int, compose_version_str.lstrip("v").split("."))
        except Exception:
            logger.warning(
                "Unable to extract docker compose version from output: \n"
                + compose_version_result.output.strip()
                + "\nPlease ensure a minimum of compose v2.5.0 is used",
                exc_info=True,
            )
        else:
            if (compose_major, compose_minor) < (2, 5):
                raise click.ClickException(
                    f"Minimum docker compose version supported: v2.5.0, installed = {compose_version_str}\n"
                    "Please update your Docker install"
                )

    exec.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")


@sandbox_group.command("start", short_help="Start the AlgoKit Sandbox")
def start_sandbox() -> None:
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Sandbox compose file does not exist yet; writing it out for the first time")
        sandbox.write_compose_file()
    elif compose_file_status is ComposeFileStatus.UP_TO_DATE:
        logger.debug("Sandbox compose file does not require updating")
    else:
        logger.warning("Sandbox definition is out of date; please run algokit sandbox reset")
    sandbox.up()


@sandbox_group.command("stop", short_help="Stop the AlgoKit Sandbox")
def stop_sandbox() -> None:
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Sandbox compose file does not exist yet; run `algokit sandbox start` to start the Sandbox")
    else:
        sandbox.stop()


@sandbox_group.command("reset", short_help="Reset the AlgoKit Sandbox")
@click.option(
    "--update/--no-update",
    default=True,
    help="Enable or disable updating to the latest available Sandbox version",
)
def reset_sandbox(update: bool) -> None:  # noqa: FBT001
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Existing Sandbox not found; creating from scratch...")
        sandbox.write_compose_file()
    else:
        sandbox.down()
        if compose_file_status is not ComposeFileStatus.UP_TO_DATE:
            logger.info("Sandbox definition is out of date; updating it to latest")
            sandbox.write_compose_file()
        if update:
            sandbox.pull()
    sandbox.up()


SERVICE_NAMES = ("algod", "indexer")


@sandbox_group.command("status", short_help="Check the status of the AlgoKit Sandbox")
def sandbox_status() -> None:
    sandbox = ComposeSandbox()
    ps = sandbox.ps()
    ps_by_name = {stats["Service"]: stats for stats in ps}
    # if any of the required containers does not exist (ie it's not just stopped but hasn't even been created),
    # then they will be missing from the output dictionary
    if not all(item in ps_by_name.keys() for item in frozenset(SERVICE_NAMES)):
        raise click.ClickException("Sandbox has not been initialized yet, please run 'algokit sandbox start'")
    # initialise output dict by setting status
    output_by_name = {
        name: {"Status": "Running" if ps_by_name[name]["State"] == "running" else "Not running"}
        for name in SERVICE_NAMES
    }
    # fill out remaining output_by_name["algod"] values
    if output_by_name["algod"]["Status"] == "Running":
        output_by_name["algod"].update(fetch_algod_data(ps_by_name["algod"]))
    # fill out remaining output_by_name["indexer"] values
    if output_by_name["indexer"]["Status"] == "Running":
        output_by_name["indexer"].update(fetch_indexer_data(ps_by_name["indexer"]))

    # Print the status details
    for service_name, service_info in output_by_name.items():
        logger.info("\n")
        logger.info(click.style(f"# {service_name} status", bold=True))
        for key, value in service_info.items():
            logger.info(click.style(f"{key}:", bold=True) + f" {value}")

    # return non-zero if any container is not running
    if not all(item["Status"] == "Running" for item in output_by_name.values()):
        raise click.ClickException()  # type: ignore


def fetch_algod_data(service_info: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    try:
        # Docker image response
        results["Port"] = port = service_info["Publishers"][0]["PublishedPort"]
        http_status_response = httpx.get(
            f"http://localhost:{port}/v1/status",
            headers={"X-Algo-API-Token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
        )
        if http_status_response.status_code == httpx.codes.OK:
            status_response = http_status_response.json()
            results["Last round"] = status_response["lastRound"]
            results["Time since last round"] = "%.1fs" % status_response["timeSinceLastRound"]

            http_versions_response = httpx.get(
                f"http://localhost:{port}/versions",
                headers={"X-Algo-API-Token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            )
            if http_versions_response.status_code == httpx.codes.OK:
                genesis_response = http_versions_response.json()
                results["Genesis ID"] = genesis_response["genesis_id"]
                results["Genesis hash"] = genesis_response["genesis_hash_b64"]
                major_version = genesis_response["build"]["major"]
                minor_version = genesis_response["build"]["minor"]
                build_version = genesis_response["build"]["build_number"]
                results["Version"] = f"{major_version}.{minor_version}.{build_version}"
        else:
            results["Status"] = "Error"
    except Exception:
        results = {}
        results["Status"] = "Error"
    return results


def fetch_indexer_data(service_info: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    try:
        # Docker image response
        results["Port"] = port = service_info["Publishers"][0]["PublishedPort"]
        # container specific response
        http_response = httpx.get(f"http://localhost:{port}/health")
        if http_response.status_code == httpx.codes.OK:
            response = http_response.json()
            results["Last round"] = response["round"]
            if "errors" in response:
                results["Error(s)"] = response["errors"]
            results["Version"] = response["version"]
        else:
            results["Status"] = "Error"
    except Exception:
        results = {}
        results["Status"] = "Error"
    return results
