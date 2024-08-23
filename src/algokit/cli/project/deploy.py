import logging
import os
import typing as t
from pathlib import Path

import click
from algosdk.mnemonic import from_private_key

from algokit.cli.common.utils import MutuallyExclusiveOption, sanitize_extra_args
from algokit.core import proc
from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.project import ProjectType, get_project_configs
from algokit.core.project.deploy import load_deploy_config, load_deploy_env_files
from algokit.core.tasks.wallet import get_alias
from algokit.core.utils import resolve_command_path, split_command_string

logger = logging.getLogger(__name__)


def _ensure_aliases(
    config_env: dict[str, str],
    deployer_alias: str | None = None,
    dispenser_alias: str | None = None,
) -> None:
    """
    Ensures that the required aliases for the deployer and dispenser are provided and valid and
    injects their mnemonics into env vars config.

    Args:
        config_env (dict[str, str]): A dictionary containing the environment variables.
        deployer_alias (str | None, optional): The alias for the deployer. Defaults to None.
        dispenser_alias (str | None, optional): The alias for the dispenser. Defaults to None.

    Raises:
        click.ClickException: If the alias or private key is missing.

    Returns:
        None
    """

    for key, alias in [("DEPLOYER_MNEMONIC", deployer_alias), ("DISPENSER_MNEMONIC", dispenser_alias)]:
        if not alias:
            continue

        alias_data = get_alias(alias)
        if not alias_data:
            raise click.ClickException(f"Error: missing {alias} alias")
        if not alias_data.private_key:
            raise click.ClickException(f"Error: missing private key for {alias} alias")
        config_env[key] = from_private_key(alias_data.private_key)  # type: ignore[no-untyped-call]
        logger.debug(f"Loaded {alias} alias mnemonic as {key} environment variable")


def _ensure_environment_secrets(
    config_env: dict[str, str],
    environment_secrets: list[str],
    *,
    skip_mnemonics_prompts: bool,
) -> None:
    """
    Ensures that the required environment variables are present in the `config_env` dictionary.
    If any of the environment variables are missing, it prompts the user to enter the missing variable.

    Args:
        config_env (dict[str, str]): A dictionary containing the current environment variables.
        environment_secrets (list[str]): A list of strings representing the required environment variables.
        skip_mnemonics_prompts (bool): A boolean indicating whether to skip prompting the user for missing variables.

    Raises:
        click.ClickException: If a required environment variable is missing and `skip_mnemonics_prompts` is True.

    Returns:
        None. The function modifies the `config_env` dictionary in-place.
    """

    for key in environment_secrets:
        if not config_env.get(key):
            if skip_mnemonics_prompts:
                raise click.ClickException(f"Error: missing {key} environment variable")
            config_env[key] = click.prompt(key, hide_input=True)


def _execute_deploy_command(  # noqa: PLR0913
    *,
    path: Path,
    environment_name: str | None,
    command: list[str] | None,
    interactive: bool,
    deployer_alias: str | None,
    dispenser_alias: str | None,
    extra_args: tuple[str, ...],
) -> None:
    logger.debug(f"Deploying from project directory: {path}")
    logger.debug("Loading deploy command from project config")
    config = load_deploy_config(name=environment_name, project_dir=path)
    if command:
        config.command = command
    elif not config.command:
        if environment_name is None:
            msg = f"No generic deploy command specified in '{ALGOKIT_CONFIG}' file."
        else:
            msg = (
                f"Deploy command for '{environment_name}' is not specified in '{ALGOKIT_CONFIG}' file, "
                "and no generic command available."
            )
        raise click.ClickException(msg)
    resolved_command = resolve_command_path(config.command + list(extra_args))
    logger.info(f"Using deploy command: {' '.join(resolved_command)}")
    logger.info("Loading deployment environment variables...")
    config_dotenv = load_deploy_env_files(environment_name, path)
    # environment variables take precedence over those in .env* files
    config_env = {**{k: v for k, v in config_dotenv.items() if v is not None}, **os.environ}
    _ensure_aliases(config_env, deployer_alias=deployer_alias, dispenser_alias=dispenser_alias)

    if config.environment_secrets:
        _ensure_environment_secrets(
            config_env,
            config.environment_secrets,
            skip_mnemonics_prompts=not interactive,
        )
    logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
    try:
        result = proc.run(resolved_command, cwd=path, env=config_env, stdout_log_level=logging.INFO)
    except FileNotFoundError as ex:
        raise click.ClickException(f"Failed to execute deploy command, '{resolved_command[0]}' wasn't found") from ex
    except PermissionError as ex:
        raise click.ClickException(
            f"Failed to execute deploy command '{resolved_command[0]}', permission denied"
        ) from ex
    else:
        if result.exit_code != 0:
            raise click.ClickException(f"Deployment command exited with error code = {result.exit_code}")


class _CommandParamType(click.types.StringParamType):
    name = "command"

    def convert(
        self,
        value: t.Any,  # noqa: ANN401
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> list[str]:
        str_value = super().convert(value=value, param=param, ctx=ctx)
        try:
            return split_command_string(str_value)
        except ValueError as ex:
            logger.debug(f"Failed to parse command string: {str_value}", exc_info=True)
            raise click.BadParameter(str(ex), param=param, ctx=ctx) from ex


class _DeployCommand(click.Command):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        # Join all args into a single string
        full_command = " ".join(args)

        try:
            separator_index = full_command.find("-- ")
            if separator_index == -1:
                raise ValueError("No separator found")
            main_args = args[:separator_index]
            extra_args = args[separator_index + 1 :]
        except Exception:
            main_args = args
            extra_args = []

        # Ensure we have at least one argument for environment_name if extra_args exist
        if extra_args and len(main_args) == 0:
            main_args.insert(0, "")

        # Reconstruct args list
        args = main_args + (["--"] if extra_args else []) + extra_args

        return super().parse_args(ctx, args)


@click.command(
    "deploy",
    context_settings={"ignore_unknown_options": True},
    cls=_DeployCommand,
)
@click.argument(
    "environment_name",
    default=None,
    required=False,
    callback=lambda _, __, value: None if value == "" else value,
)
@click.option(
    "--command",
    "-C",
    "-c",
    type=_CommandParamType(),
    default=None,
    help=("Custom deploy command. If not provided, will load the deploy command " "from .algokit.toml file."),
    required=False,
)
@click.option(
    "--interactive/--non-interactive",
    " /--ci",  # this aliases --non-interactive to --ci
    default=lambda: "CI" not in os.environ,
    help=(
        "Enable/disable interactive prompts. Defaults to non-interactive if the CI "
        "environment variable is set. Interactive MainNet deployments prompt for confirmation."
    ),
)
@click.option(
    "--path",
    "-P",
    type=click.Path(exists=True, readable=True, file_okay=False, resolve_path=True, path_type=Path),
    default=".",
    help="Specify the project directory. If not provided, current working directory will be used.",
)
@click.option(
    "--deployer",
    "deployer_alias",
    type=click.STRING,
    required=False,
    help=(
        "(Optional) Alias of the deployer account. Otherwise, will prompt the deployer mnemonic "
        "if specified in .algokit.toml file."
    ),
)
@click.option(
    "--dispenser",
    "dispenser_alias",
    type=click.STRING,
    required=False,
    help=(
        "(Optional) Alias of the dispenser account. Otherwise, will prompt the dispenser mnemonic "
        "if specified in .algokit.toml file."
    ),
)
@click.option(
    "--project-name",
    "-p",
    "project_names",
    multiple=True,
    help="(Optional) Projects to execute the command on. Defaults to all projects found in the current directory.",
    nargs=1,
    default=[],
    metavar="<value>",
    required=False,
    cls=MutuallyExclusiveOption,
    not_required_if=[
        "command",
    ],
)
@click.argument(
    "extra_args",
    nargs=-1,
    required=False,
)
@click.pass_context
def deploy_command(  # noqa: PLR0913
    ctx: click.Context,
    *,
    environment_name: str | None,
    command: list[str] | None,
    interactive: bool,
    path: Path,
    deployer_alias: str | None,
    dispenser_alias: str | None,
    project_names: tuple[str, ...],
    extra_args: tuple[str, ...],
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    extra_args = sanitize_extra_args(extra_args)

    if ctx.parent and ctx.parent.command.name == "algokit":
        click.secho(
            "WARNING: The 'deploy' command is scheduled for deprecation in v2.x release. "
            "Please migrate to using 'algokit project deploy' instead.",
            fg="yellow",
        )

    if interactive and environment_name and environment_name.lower() == "mainnet":
        click.confirm(
            click.style(
                "Warning: Proceed with MainNet deployment?",
                fg="yellow",
            ),
            default=True,
            abort=True,
        )

    config = get_algokit_config() or {}
    is_workspace = config.get("project", {}).get("type") == ProjectType.WORKSPACE
    project_name = config.get("project", {}).get("name", None)

    if not is_workspace and project_names:
        message = (
            f"Deploying `{project_name}`..."
            if project_name in project_names
            else "No project with the specified name found in the current directory or workspace."
        )
        if project_name in project_names:
            click.echo(message)
        else:
            raise click.ClickException(message)

    if is_workspace:
        projects = get_project_configs(project_type=ProjectType.CONTRACT, project_names=project_names)

        for project in projects:
            project_name = project.get("project", {}).get("name", None)

            if not project_name:
                click.secho("WARNING: Skipping an unnamed project...", fg="yellow")
                continue

            _execute_deploy_command(
                path=project.get("cwd", None),
                environment_name=environment_name,
                command=None,
                interactive=interactive,
                deployer_alias=deployer_alias,
                dispenser_alias=dispenser_alias,
                extra_args=extra_args,
            )
    else:
        _execute_deploy_command(
            path=path,
            environment_name=environment_name,
            command=command,
            interactive=interactive,
            deployer_alias=deployer_alias,
            dispenser_alias=dispenser_alias,
            extra_args=extra_args,
        )
