import abc
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import ClassVar

import click

from algokit.core import proc
from algokit.core.utils import is_windows

logger = logging.getLogger(__name__)

TYPESCRIPT_NPX_PACKAGE = "@algorandfoundation/algokit-client-generator"
DEFAULT_TYPESCRIPT_NPX_PACKAGE_VERSION = "@^2.5.0"
PYTHON_PYPI_PACKAGE = "algokit-client-generator"
DEFAULT_PYTHON_PYPI_PACKAGE_VERSION = ">=1.1.1"


def _snake_case(s: str) -> str:
    s = s.replace("-", " ")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"[-\s]", "_", s).lower()


class ClientGenerator(abc.ABC):
    language: ClassVar[str]
    extension: ClassVar[str]
    version: str | None

    _by_language: ClassVar[dict[str, type["ClientGenerator"]]] = {}
    _by_extension: ClassVar[dict[str, type["ClientGenerator"]]] = {}

    def __init__(self, version: str | None) -> None:
        self.version = version

    def __init_subclass__(cls, language: str, extension: str) -> None:
        cls.language = language
        cls.extension = extension
        cls._by_language[language] = cls
        cls._by_extension[extension] = cls

    @classmethod
    def languages(cls) -> list[str]:
        return list(cls._by_language.keys())

    @classmethod
    def create_for_language(cls, language: str, version: str | None) -> "ClientGenerator":
        return cls._by_language[language](version=version)

    @classmethod
    def create_for_extension(cls, extension: str, version: str | None) -> "ClientGenerator":
        return cls._by_extension[extension](version=version)

    def resolve_output_path(self, app_spec: Path, output_path_pattern: str | None) -> Path | None:
        try:
            application_json = json.loads(app_spec.read_text())
            contract_name: str = application_json["contract"]["name"]
        except Exception:
            logger.error(f"Couldn't parse contract name from {app_spec}", exc_info=True)
            return None
        output_resolved = (output_path_pattern or self.default_output_pattern).format(
            contract_name=self.format_contract_name(contract_name),
            app_spec_dir=str(app_spec.parent),
        )
        output_path = Path(output_resolved)
        if output_path.exists() and not output_path.is_file():
            logger.error(f"Could not output to {output_path} as it already exists and is a directory")
            return None
        return output_path

    @abc.abstractmethod
    def generate(self, app_spec: Path, output: Path) -> None:
        ...

    @property
    @abc.abstractmethod
    def default_output_pattern(self) -> str:
        ...

    def format_contract_name(self, contract_name: str) -> str:
        return contract_name


class PythonClientGenerator(ClientGenerator, language="python", extension=".py"):
    def __init__(self, version: str | None) -> None:
        super().__init__(version=version)
        if version:
            self.version = f"=={version}"
        else:
            self.version = DEFAULT_PYTHON_PYPI_PACKAGE_VERSION
        pipx_path = shutil.which("pipx")
        if not pipx_path:
            raise click.ClickException(
                "Python generator requires Python and pipx to be installed. "
                "Please install pipx via https://pypa.github.io/pipx/ first. "
            )
        self._pipx_path = pipx_path

    def generate(self, app_spec: Path, output: Path) -> None:
        logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
        cmd = [
            self._pipx_path,
            "run",
            f"{PYTHON_PYPI_PACKAGE}{self.version}",
            "-a",
            str(app_spec),
            "-o",
            str(output),
        ]
        logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
        run_result = proc.run(cmd)
        click.echo(run_result.output)

        if run_result.exit_code != 0:
            click.secho(
                f"Client generation failed for {app_spec}.",
                err=True,
                fg="red",
            )
            raise click.exceptions.Exit(run_result.exit_code)

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}_client{self.extension}"

    def format_contract_name(self, contract_name: str) -> str:
        return _snake_case(contract_name)


class TypeScriptClientGenerator(ClientGenerator, language="typescript", extension=".ts"):
    def __init__(self, version: str | None) -> None:
        super().__init__(version=version)
        if version:
            self.version = f"@{version}"
        else:
            self.version = DEFAULT_TYPESCRIPT_NPX_PACKAGE_VERSION

        npx_path = shutil.which("npx")
        if not npx_path:
            raise click.ClickException("Typescript generator requires Node.js and npx to be installed.")

        # Create the npm directory inside %APPDATA% if it doesn't exist, as npx on windows needs this.
        # See https://github.com/npm/cli/issues/7089 for more details.
        if is_windows():
            appdata_dir = os.getenv("APPDATA")
            if appdata_dir is not None:
                appdata_dir_path = Path(appdata_dir).expanduser()
                npm_dir = appdata_dir_path / "npm"
                try:
                    if not npm_dir.exists():
                        npm_dir.mkdir(parents=True)
                except OSError as ex:
                    logger.debug(ex)
                    raise click.ClickException(
                        f"Failed to create the `npm` directory in {appdata_dir_path}.\n"
                        "This command uses `npx`, which requires the `npm` directory to exist "
                        "in the above path, otherwise an ENOENT 4058 error will occur.\n"
                        "Please create this directory manually and try again."
                    ) from ex

    def generate(self, app_spec: Path, output: Path) -> None:
        cmd = [
            "npx" if not is_windows() else "npx.cmd",
            "--yes",
            f"{TYPESCRIPT_NPX_PACKAGE}{self.version}",
            "generate",
            "-a",
            str(app_spec),
            "-o",
            str(output),
        ]
        logger.info(
            f"Generating TypeScript client code for application specified in {app_spec} and writing to {output}"
        )
        run_result = proc.run(cmd)
        click.echo(run_result.output)

        if run_result.exit_code != 0:
            click.secho(
                f"Client generation failed for {app_spec}.",
                err=True,
                fg="red",
            )
            raise click.exceptions.Exit(run_result.exit_code)

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}Client{self.extension}"
