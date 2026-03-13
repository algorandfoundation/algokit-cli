import logging
import os
import platform
from pathlib import Path

import click

from algokit.core import proc
from algokit.core.sandbox import (
    DEFAULT_ALGOD_PORT,
    DEFAULT_ALGOD_SERVER,
    DEFAULT_ALGOD_TOKEN,
    DEFAULT_INDEXER_PORT,
    DEFAULT_INDEXER_TOKEN,
    ComposeSandbox,
)
from algokit.core.utils import resolve_command_path

logger = logging.getLogger(__name__)

VIBEKIT_INSTALL_URL = "https://getvibekit.ai/install"


@click.group("vibe", short_help="Give your AI assistant Algorand superpowers using VibeKit.")
def vibe_group() -> None:
    """Give your AI assistant Algorand superpowers using VibeKit."""


def _resolve_vibekit_command() -> list[str] | None:
    try:
        return resolve_command_path(["vibekit"])
    except click.ClickException:
        return None


def _get_install_command() -> list[str]:
    if platform.system() == "Windows":
        return ["powershell", "-ExecutionPolicy", "ByPass", "-c", f"irm {VIBEKIT_INSTALL_URL} | iex"]
    return ["sh", "-c", f"curl -fsSL {VIBEKIT_INSTALL_URL} | sh"]


def _build_vibekit_init_env() -> dict[str, str]:
    env = dict(os.environ)

    is_running = False
    try:
        sandbox = ComposeSandbox.from_environment()
        if sandbox is not None:
            ps_by_name = {stats["Service"]: stats for stats in sandbox.ps()}
            required_services = ("algod", "indexer")
            is_running = (
                all(name in ps_by_name for name in required_services)
                and all(ps_by_name[name].get("State") == "running" for name in required_services)
            )
    except Exception as ex:
        # Context injection should never block initialization.
        logger.warning("Unable to inspect AlgoKit LocalNet status; proceeding without confirmed LocalNet state.")
        logger.debug("LocalNet inspection failed", exc_info=ex)

    env["ALGOKIT_LOCALNET_ALGOD_URL"] = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}"
    env["ALGOKIT_LOCALNET_ALGOD_TOKEN"] = DEFAULT_ALGOD_TOKEN
    env["ALGOKIT_LOCALNET_INDEXER_URL"] = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_INDEXER_PORT}"
    env["ALGOKIT_LOCALNET_INDEXER_TOKEN"] = DEFAULT_INDEXER_TOKEN
    env["ALGOKIT_LOCALNET_RUNNING"] = "true" if is_running else "false"
    return env


@vibe_group.command("setup")
def setup() -> None:
    """Install and initialize VibeKit for the current project."""
    run_vibe_setup()


def run_vibe_setup(cwd: Path | None = None) -> None:
    """Run VibeKit setup flow."""
    vibekit_cmd = _resolve_vibekit_command()
    if vibekit_cmd is None:
        click.echo(click.style("VibeKit not found.", fg="yellow"))
        if not click.confirm("Would you like to install VibeKit now?", default=True):
            raise click.ClickException(
                f"Please install VibeKit manually from {VIBEKIT_INSTALL_URL} and re-run `algokit vibe setup`."
            )

        install_error_message = (
            f"Failed to install VibeKit automatically. Install manually from {VIBEKIT_INSTALL_URL} "
            "and re-run `algokit vibe setup`."
        )
        try:
            proc.run(_get_install_command(), bad_return_code_error_message=install_error_message)
        except OSError as ex:
            raise click.ClickException(install_error_message) from ex

        vibekit_cmd = _resolve_vibekit_command()
        if vibekit_cmd is None:
            raise click.ClickException(
                f"VibeKit was installed but isn't available on PATH yet. Restart your shell and run "
                f"`algokit vibe setup`, or install manually from {VIBEKIT_INSTALL_URL}."
            )

    logger.info("Initializing VibeKit context...")
    env = _build_vibekit_init_env()
    result = proc.run_interactive([*vibekit_cmd, "init"], env=env, cwd=cwd)
    if result.exit_code != 0:
        raise click.ClickException("VibeKit initialization failed.")


@vibe_group.command("status")
def status() -> None:
    """Check the status of VibeKit AI skills and MCP servers."""
    run_vibe_status()


def run_vibe_status(cwd: Path | None = None) -> None:
    """Run VibeKit status flow."""
    vibekit_cmd = _resolve_vibekit_command()
    if vibekit_cmd is None:
        raise click.ClickException(
            f"VibeKit is not installed. Install it from {VIBEKIT_INSTALL_URL} and run `algokit vibe setup`."
        )

    result = proc.run_interactive([*vibekit_cmd, "status"], cwd=cwd)
    if result.exit_code != 0:
        raise click.ClickException("VibeKit status check failed.")
