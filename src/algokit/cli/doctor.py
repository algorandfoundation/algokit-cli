import logging
import platform

import click
import pyclip  # type: ignore
from algokit.core import doctor as doctor_functions
from algokit.core.doctor import ProcessResult

logger = logging.getLogger(__name__)
DOCTOR_END_MESSAGE = (
    "If you are experiencing a problem with algokit, feel free to submit an issue "
    "via https://github.com/algorandfoundation/algokit-cli/issues/new; please include this output, "
    "if you want to populate this message in your clipboard, run `algokit doctor -c`"
)


@click.command(
    "doctor",
    short_help="Run the Algorand doctor CLI.",
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
    return_code = 0
    os_type = platform.system().lower()
    service_outputs: dict[str, ProcessResult] = {}

    service_outputs["Time"] = doctor_functions.get_date()
    service_outputs["AlgoKit"] = doctor_functions.get_algokit_info()
    if os_type == "windows":
        service_outputs["Chocolatey"] = doctor_functions.get_choco_info()
    if os_type == "darwin":
        service_outputs["Brew"] = doctor_functions.get_brew_info()
    service_outputs["OS"] = doctor_functions.get_os(os_type)
    service_outputs["Docker"] = doctor_functions.get_docker_info()
    service_outputs["Docker Compose"] = doctor_functions.get_docker_compose_info()
    service_outputs["Git"] = doctor_functions.get_git_info(os_type)
    service_outputs["AlgoKit Python"] = doctor_functions.get_algokit_python_info()
    service_outputs["Global Python"] = doctor_functions.get_global_python_info()
    service_outputs["Pipx"] = doctor_functions.get_pipx_info()
    service_outputs["Poetry"] = doctor_functions.get_poetry_info()
    service_outputs["Node.js"] = doctor_functions.get_node_info()
    service_outputs["Npm"] = doctor_functions.get_npm_info()

    critical_services = ["Docker", "Docker Compose", "Git"]
    # Print the status details
    for key, value in service_outputs.items():
        color = "green"
        if value.exit_code != 0:
            color = "red" if key in critical_services else "yellow"
            return_code = 1
        logger.info(click.style(f"{key}: ", bold=True) + click.style(f"{value.info}", fg=color))

    # print end message anyway
    logger.info(DOCTOR_END_MESSAGE)

    if copy_to_clipboard:
        pyclip.copy("\n".join(f"{key}: {value.info}" for key, value in service_outputs.items()))

    if return_code != 0:
        raise click.exceptions.Exit(code=1)
