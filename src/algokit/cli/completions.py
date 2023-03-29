import logging
from pathlib import Path

import click
import click.shell_completion
import shellingham  # type: ignore[import]

from algokit.core.atomic_write import atomic_write
from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)

SUPPORTED_SHELLS = ["bash", "zsh"]


@click.group("completions", short_help="Install and Uninstall AlgoKit shell integrations.")
def completions_group() -> None:
    pass


shell_option = click.option(
    "--shell", type=click.Choice(SUPPORTED_SHELLS), help="Specify shell to install algokit completions for."
)


@completions_group.command(
    "install",
    short_help="Install shell completions",
)
@shell_option
def install(shell: str | None) -> None:
    """Install shell completions, this command will attempt to update the interactive profile script
    for the current shell to support algokit completions. To specify a specific shell use --shell."""
    shell_completion = ShellCompletion(shell)
    shell_completion.install()


@completions_group.command(
    "uninstall",
    short_help="Uninstall shell completions",
)
@shell_option
def uninstall(shell: str | None) -> None:
    """Uninstall shell completions, this command will attempt to update the interactive profile script
    for the current shell to remove any algokit completions that have been added.
    To specify a specific shell use --shell."""
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
        if self._insert_profile_line():
            logger.info(f"AlgoKit completions installed for {self.shell} 🎉")
        else:
            logger.info(f"{self.profile_path} already contains completion source 🤔")
        home_based_profile_path = _get_home_based_path(self.profile_path)
        logger.info(f"Restart shell or run `. {home_based_profile_path}` to enable completions")

    def uninstall(self) -> None:
        self._remove_source()
        if self._remove_profile_line():
            logger.info(f"AlgoKit completions uninstalled for {self.shell} 🎉")
        else:
            logger.info(f"AlgoKit completions not installed for {self.shell} 🤔")

    @property
    def source(self) -> str:
        completion_class = click.shell_completion.get_completion_class(self.shell)
        if completion_class is None:
            raise click.ClickException(f"Unsupported shell for completions: {self.shell}")
        completion = completion_class(
            # class is only instantiated to get source snippet, so don't need to pass a real command
            cli=None,  # type: ignore[arg-type]
            ctx_args={},
            prog_name="algokit",
            complete_var="_ALGOKIT_COMPLETE",
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
        self.source_path.write_text(source, encoding="utf-8")

    def _remove_source(self) -> None:
        logger.debug(f"Removing source script {self.source_path}")
        self.source_path.unlink(missing_ok=True)

    def _insert_profile_line(self) -> bool:
        try:
            content = self.profile_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            pass
        else:
            if self.profile_line in content:
                # profile already contains source of completion script. nothing to do
                return False

        logger.debug(f"Appending completion source to {self.profile_path}")
        # got to end of file, so append profile line
        atomic_write(self.profile_line, self.profile_path, "a")
        return True

    def _remove_profile_line(self) -> bool:
        try:
            content = self.profile_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.debug(f"{self.profile_path} not found")
            return False
        # see if profile script contains profile_line, if it does remove it
        if self.profile_line not in content:
            return False
        logger.debug(f"Completion source found in {self.profile_path}")
        content = content.replace(self.profile_line, "")

        logger.debug(f"Removing completion source found in {self.profile_path}")
        atomic_write(content, self.profile_path, "w")
        return True


def _get_home_based_path(path: Path) -> Path:
    home = Path.home()
    try:
        home_based_path = path.relative_to(home)
    except ValueError:
        return path
    else:
        return "~" / home_based_path


def _get_current_shell() -> str:
    try:
        shell_name, *_ = shellingham.detect_shell()  # type: tuple[str, str]
    except Exception as ex:
        logger.debug("Could not determine current shell", exc_info=ex)
        logger.warning("Could not determine current shell. Try specifying a supported shell with --shell")
        raise click.exceptions.Exit(code=1) from ex

    if shell_name not in SUPPORTED_SHELLS:
        logger.warning(f"{shell_name} is not a supported shell. 😢")
        raise click.exceptions.Exit(code=1)
    return shell_name
