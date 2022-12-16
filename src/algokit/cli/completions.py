import logging
from pathlib import Path

import click
import click.shell_completion
import shellingham  # type: ignore
from algokit.core.atomic_write import atomic_write
from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)

SUPPORTED_SHELLS = ["bash", "zsh"]


@click.group("completions", short_help="Install and Uninstall AlgoKit shell integration.")
def completions_group() -> None:
    pass


shell_option = click.option(
    "--shell", type=click.Choice(SUPPORTED_SHELLS), help="Specify shell to install algokit completions for."
)


@completions_group.command(
    "install",
    short_help="Install shell completions, this command will attempt to update the interactive profile script"
    " for the current shell to support algokit completions. To specify a specific shell use --shell.",
)
@shell_option
def install(shell: str | None) -> None:
    shell_completion = ShellCompletion(shell)
    shell_completion.install()


@completions_group.command(
    "uninstall",
    short_help="Uninstall shell completions, this command will attempt to update the interactive profile script"
    " for the current shell to remove any algokit completions that have been added."
    " To specify a specific shell use --shell.",
)
@shell_option
def uninstall(shell: str | None) -> None:
    shell_completion = ShellCompletion(shell)
    shell_completion.uninstall()


class ShellCompletion:
    def __init__(self, shell: str | None) -> None:
        shell = shell or _get_current_shell()
        self.shell = shell
        self.source_path = get_app_config_dir() / f".algokit-completions.{shell}"
        self.profile_path = Path(f"~/.{shell}rc").expanduser()
        home_based_source_path = _get_home_based_path(self.source_path)
        self.profile_line = f". {home_based_source_path}\n"

    def install(self) -> None:
        self._save_source()
        self._insert_profile_line()
        logger.info(f"AlgoKit completions installed for {self.shell} 🎉")
        home_based_profile_path = _get_home_based_path(self.profile_path)
        logger.info(f"Restart shell or run `. {home_based_profile_path}` to enable completions")

    def uninstall(self) -> None:
        self._remove_source()
        self._remove_profile_line()
        logger.info(f"AlgoKit completions uninstalled for {self.shell} 🎉")

    @property
    def source(self) -> str:
        completion_class = click.shell_completion.get_completion_class(self.shell)
        completion = completion_class(
            # class is only instantiated to get source snippet, so don't need to pass a real command
            None,  # type: ignore
            {},
            "algokit",
            "_ALGOKIT_COMPLETE",
        )
        try:
            return completion.source()
        except RuntimeError as ex:
            logger.debug(f"Failed to generate completion source. {ex}")
            if self.shell == "bash":
                logger.error("Shell completion is not supported for Bash versions older than 4.4.")
            else:
                logger.error("Failed to install completions 😢.")
            raise click.exceptions.Exit(code=1) from ex

    def _save_source(self) -> None:
        # grab source before attempting to write file in case it fails
        source = self.source
        logger.debug(f"Writing source script {self.source_path}")
        with open(self.source_path, "w") as source_file:
            source_file.write(source)
            source_file.flush()

    def _remove_source(self) -> None:
        logger.debug(f"Removing source script {self.source_path}")
        self.source_path.unlink(missing_ok=True)

    def _insert_profile_line(self) -> None:
        do_write = True
        if self.profile_path.exists():
            with open(self.profile_path) as file:
                for line in file:
                    if self.profile_line in line:
                        logger.debug(f"{self.profile_path} already contains completion source")
                        # profile already contains source of completion script. nothing to do
                        do_write = False
                        break

        if do_write:
            logger.debug(f"Appending completion source to {self.profile_path}")
            # got to end of file, so append profile line
            atomic_write([self.profile_line], self.profile_path, "a")

    def _remove_profile_line(self) -> None:
        if not self.profile_path.exists():
            logger.debug(f"{self.profile_path} not found")
            # nothing to do
            return

        # see if profile script contains profile_line, if it does remove it
        do_write = False
        lines = []
        with open(self.profile_path) as file:
            for line in file:
                if self.profile_line in line:
                    do_write = True
                    logger.debug(f"Completion source found in {self.profile_path}")
                else:
                    lines.append(line)

        if do_write:
            logger.debug(f"Removing completion source found in {self.profile_path}")
            atomic_write(lines, self.profile_path, "w")


def _get_home_based_path(path: Path) -> Path:
    home = Path("~").expanduser()
    try:
        home_based_path = path.relative_to(home)
        return "~" / home_based_path
    except ValueError:
        return path


def _get_current_shell() -> str:
    try:
        shell = shellingham.detect_shell()
        shell_name: str = shell[0]
    except Exception as ex:
        logger.debug("Could not determine current shell", exc_info=ex)
        logger.warning("Could not determine current shell. Try specifying a supported shell with --shell")
        raise click.exceptions.Exit(code=1) from ex

    if shell_name not in SUPPORTED_SHELLS:
        logger.warning(f"{shell_name} is not a supported shell. 😢")
        raise click.exceptions.Exit(code=1)
    return shell_name
