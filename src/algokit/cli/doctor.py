import datetime as dt
import logging
import platform
import sys

import click
import pyclip  # type: ignore[import-untyped]

from algokit.core.conf import get_current_package_version
from algokit.core.config_commands.version_prompt import get_latest_github_version
from algokit.core.doctor import DoctorResult, check_dependency
from algokit.core.sandbox import (
    COMPOSE_VERSION_COMMAND,
    get_min_compose_version,
)
from algokit.core.utils import is_windows as get_is_windows

logger = logging.getLogger(__name__)

WARNING_COLOR = "yellow"
CRITICAL_COLOR = "red"


@click.command(
    "doctor",
    short_help="Diagnose potential environment issues that may affect AlgoKit.",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.option(
    "--copy-to-clipboard",
    "-c",
    help="Copy the contents of the doctor message (in Markdown format) in your clipboard.",
    is_flag=True,
    default=False,
)
def doctor_command(*, copy_to_clipboard: bool) -> None:
    """Diagnose potential environment issues that may affect AlgoKit.

    Will search the system for AlgoKit dependencies and show their versions, as well as identifying any
    potential issues."""
    from algokit.core.config_commands.container_engine import get_container_engine

    os_type = platform.system()
    is_windows = get_is_windows()
    container_engine = get_container_engine()
    docs_url = f"https://{container_engine}.io"
    compose_minimum_version = get_min_compose_version()
    service_outputs = {
        "timestamp": DoctorResult(ok=True, output=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()),
        "AlgoKit": _get_algokit_version_output(),
        "AlgoKit Python": DoctorResult(ok=True, output=f"{sys.version} (location: {sys.prefix})"),
        "OS": DoctorResult(ok=True, output=platform.platform()),
        container_engine: check_dependency(
            [container_engine, "--version"],
            missing_help=[f"`{container_engine}` required to run `algokit localnet` command; install via {docs_url}"],
        ),
        f"{container_engine} compose": check_dependency(
            COMPOSE_VERSION_COMMAND,
            minimum_version=compose_minimum_version,
            minimum_version_help=[
                f"{container_engine.capitalize()} Compose {compose_minimum_version} required to run `algokit localnet` command;",  # noqa: E501
                f"install via {docs_url}",
            ],
        ),
        "git": check_dependency(
            ["git", "--version"],
            missing_help=(
                [
                    "Git required to `run algokit init`; install via `winget install -e --id Git.Git` if using winget,",
                    "or via https://github.com/git-guides/install-git#install-git-on-windows",
                ]
                if is_windows
                else ["Git required to run `algokit init`; install via https://github.com/git-guides/install-git"]
            ),
        ),
        "python": check_dependency(["python", "--version"], include_location=True),
        "python3": check_dependency(["python3", "--version"], include_location=True),
        "pipx": check_dependency(
            ["pipx", "--version"],
            missing_help=[
                "pipx is required if poetry is not installed in order to install it automatically;",
                "install via https://pypa.github.io/pipx/",
            ],
        ),
        "poetry": check_dependency(
            ["poetry", "--version"],
            missing_help=[
                "Poetry is required for some Python-based templates;",
                "install via `algokit project bootstrap` within project directory, or via:",
                "https://python-poetry.org/docs/#installation",
            ],
        ),
        "node": check_dependency(
            ["node", "--version"],
            missing_help=[
                "Node.js is required for some Node.js-based templates;",
                "install via `algokit project bootstrap` within project directory, or via:",
                "https://nodejs.dev/en/learn/how-to-install-nodejs/",
            ],
        ),
        "npm": check_dependency(["npm" if not is_windows else "npm.cmd", "--version"]),
    }
    if is_windows:
        service_outputs["winget"] = check_dependency(["winget", "--version"])
    elif os_type == "Darwin":
        service_outputs["brew"] = check_dependency(["brew", "--version"])

    critical_services = [container_engine, f"{container_engine} compose", "git"]
    # Print the status details
    for key, value in service_outputs.items():
        if value.ok:
            color = None
        else:
            color = CRITICAL_COLOR if key in critical_services else WARNING_COLOR
        msg = click.style(f"{key}: ", bold=True) + click.style(value.output, fg=color)
        for ln in value.extra_help or []:
            msg += f"\n  {ln}"
        logger.info(msg)

    # print end message anyway
    logger.info(
        "\n"
        "If you are experiencing a problem with AlgoKit, feel free to submit an issue via:\n"
        "https://github.com/algorandfoundation/algokit-cli/issues/new\n"
        "Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`"
    )

    if copy_to_clipboard:
        pyclip.copy(
            "\n".join(
                f"* {key}: " + "\n  ".join([value.output, *(value.extra_help or [])])
                for key, value in service_outputs.items()
            )
        )

    if any(not value.ok for value in service_outputs.values()):
        raise click.exceptions.Exit(code=1)


def _get_algokit_version_output() -> DoctorResult:
    current = get_current_package_version()
    try:
        latest = get_latest_github_version()
    except Exception as ex:
        logger.warning("Failed to check latest AlgoKit release version", exc_info=ex)
        latest = None
    if latest is None or current == latest:
        output = current
    else:
        output = click.style(current, fg=WARNING_COLOR) + f" (latest: {latest})"
    return DoctorResult(ok=True, output=output)
