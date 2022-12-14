import logging
import platform

import click
from algokit.core.doctor import DoctorFunctions

logger = logging.getLogger(__name__)


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
    help="Copy the contents of the doctor message (in Markdown format) in the user's clipboard.",
    is_flag=True,
    default=False,
)
def doctor_command(copy_to_clipboard: bool) -> None:
    os_type = platform.system().lower()

    result_lines = []
    doctor_functions = DoctorFunctions()
    result_lines.append(doctor_functions.get_date())
    result_lines.append(doctor_functions.get_algokit_version())
    if os_type == "windows":
        result_lines.append(doctor_functions.get_choco_info())
    if os_type == "darwin":
        result_lines.append(doctor_functions.get_brew_info())
    result_lines.append(doctor_functions.get_os(os_type))
    result_lines.append(doctor_functions.get_docker_info())
    result_lines.append(doctor_functions.get_docker_compose_info())

    result_lines.append(doctor_functions.get_git_info(os_type == "windows"))

    result_lines.append(doctor_functions.get_algokit_python_info())
    result_lines.append(doctor_functions.get_global_info())
    result_lines.append(doctor_functions.get_pipx_info())
    result_lines.append(doctor_functions.get_poetry_info())

    result_lines.append(doctor_functions.get_node_info())

    result_lines.append(doctor_functions.get_npm_info())

    result_lines.append(
        (
            "If you are experiencing a problem with algokit, feel free to submit an issue "
            "via https://github.com/algorandfoundation/algokit-cli/issues/new; please include this output, "
            "if you want to populate this message in your clipboard, run `algokit doctor -c`"
        )
    )

    logger.info("".join(result_lines))

    if copy_to_clipboard:
        logger.info("Contents copied to your clipboard")
        # TODO: copy to clipboard
