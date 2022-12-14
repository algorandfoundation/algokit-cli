import logging
import platform

import click
import pyperclip3
from algokit.core.doctor import DoctorFunctions

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
    os_type = platform.system().lower()

    service_outputs: dict[str, str] = {}
    service_outputs_contents_lines: list[str] = []
    doctor_functions = DoctorFunctions()

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

    # Print the status details
    if copy_to_clipboard:
        for key, value in service_outputs.items():
            logger.info(click.style(f"{key}: ", bold=True) + f"{value}")
            service_outputs_contents_lines.append(f"{key}: {value}\n")
        service_outputs_contents_lines.append(DOCTOR_END_MESSAGE)
    else:
        for key, value in service_outputs.items():
            logger.info(click.style(f"{key}: ", bold=True) + f"{value}")

    # print end message anyway
    logger.info(DOCTOR_END_MESSAGE)

    if copy_to_clipboard:
        pyperclip3.copy("".join(service_outputs_contents_lines))
