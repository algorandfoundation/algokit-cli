import abc
import json
import logging
import re
from pathlib import Path
from typing import ClassVar

import click

from algokit.core import proc
from algokit.core.utils import extract_version_triple, find_valid_pipx_command, get_valid_npx_command

logger = logging.getLogger(__name__)

TYPESCRIPT_NPX_PACKAGE = "@algorandfoundation/algokit-client-generator"
PYTHON_PYPI_PACKAGE = "algokit-client-generator"


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
        self.command = self.find_valid_generate_command(version)

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

    @abc.abstractmethod
    def find_valid_generate_command(self, version: str | None) -> list[str]:
        ...

    @abc.abstractmethod
    def _find_generate_command_at_version(self, version: str) -> list[str]:
        ...

    @abc.abstractmethod
    def _find_generate_command(self) -> list[str]:
        ...

    def format_contract_name(self, contract_name: str) -> str:
        return contract_name


class PythonClientGenerator(ClientGenerator, language="python", extension=".py"):
    def generate(self, app_spec: Path, output: Path) -> None:
        logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
        cmd = [
            *self.command,
            "-a",
            str(app_spec),
            "-o",
            str(output),
        ]
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

    def find_valid_generate_command(self, version: str | None) -> list[str]:
        return self._find_generate_command_at_version(version) if version is not None else self._find_generate_command()

    def _find_generate_command_at_version(self, version: str) -> list[str]:
        """
        Find python generator command with a specific version.
        If the python generator version isn't installed, install it with pipx run.
        """
        pipx_command = find_valid_pipx_command(
            "Unable to find pipx install so that the `algokit-client-generator` can be installed; "
            "please install pipx via https://pypa.github.io/pipx/ "
            "and then try `algokit generate client ...` again."
        )
        client_generator_intalation_command = ["pipx", "list"]
        try:
            result = proc.run(client_generator_intalation_command)
            if result.exit_code == 0:
                installed_version = None
                for line in result.output.splitlines():
                    if PYTHON_PYPI_PACKAGE in line:
                        installed_version = extract_version_triple(line)
                        break
                if extract_version_triple(version) == installed_version:
                    return ["algokitgen-py"]
        except OSError:
            pass
        except ValueError:
            pass

        return [
            *pipx_command,
            "run",
            f"algokit-client-generator=={version}",
        ]

    def _find_generate_command(self) -> list[str]:
        """
        Find python generator command.
        If python generator isn't installed, install the latest version with pipx.
        If it is installed, use whatever version is installed.
        """
        client_generator_intalation_command = ["pipx", "list"]
        try:
            result = proc.run(client_generator_intalation_command)
            if result.exit_code == 0:
                for line in result.output.splitlines():
                    if PYTHON_PYPI_PACKAGE in line:
                        return ["algokitgen-py"]

        except OSError:
            pass

        pipx_command = find_valid_pipx_command(
            "Unable to find pipx install so that the `algokit-client-generator` can be installed; "
            "please install pipx via https://pypa.github.io/pipx/ "
            "and then try `algokit generate client ...` again."
        )
        return [
            *pipx_command,
            "run",
            "algokit-client-generator",
        ]


class TypeScriptClientGenerator(ClientGenerator, language="typescript", extension=".ts"):
    def generate(self, app_spec: Path, output: Path) -> None:
        cmd = [*self.command, "generate", "-a", str(app_spec), "-o", str(output)]
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

    def find_valid_generate_command(self, version: str | None) -> list[str]:
        return self._find_generate_command_at_version(version) if version is not None else self._find_generate_command()

    def _find_generate_command_at_version(self, version: str) -> list[str]:
        """
        Find the typescript generator command with a specific version.
        If the typescript generator version isn't installed, run it with npx with the given version.
        If the typescript generator version is installed, run it with npx with the given version.
        """
        npx_command = get_valid_npx_command(
            "Unable to find npx install so that the `algokit-client-generator` can be installed; "
            "please install npx via https://www.npmjs.com/package/npx "
            "and then try `algokit generate client ...` again.",
            npx=True,
        )
        npm_command = get_valid_npx_command(
            "Unable to find npm install so that the `algokit-client-generator` can be installed; "
            "please install npm via https://docs.npmjs.com/downloading-and-installing-node-js-and-npm "
            "and then try `algokit generate client ...` again.",
            npx=False,
        )
        client_generator_installation_command = [*npm_command, "list"]
        try:
            result = proc.run(client_generator_installation_command)
            if result.exit_code == 0:
                for line in result.output.splitlines():
                    if TYPESCRIPT_NPX_PACKAGE in line:
                        typescript_client_generator_version_result = line
                        installed_version = extract_version_triple(typescript_client_generator_version_result)
                        if extract_version_triple(version) == installed_version:
                            return [
                                *npx_command,
                                "--yes",
                                f"{TYPESCRIPT_NPX_PACKAGE}@{installed_version}",
                            ]
        except OSError:
            pass
        except ValueError:
            pass

        return [
            *npx_command,
            "--yes",
            f"{TYPESCRIPT_NPX_PACKAGE}@{extract_version_triple(version)}",
        ]

    def _find_generate_command(self) -> list[str]:
        """
        Find the typescript generator command.
        If the typescript generator isn't installed, install the latest version with npx.
        IF it is installed, use whatever version is installed.
        """
        npx_command = get_valid_npx_command(
            "Unable to find npx install so that the `algokit-client-generator` can be installed; "
            "please install npx via https://www.npmjs.com/package/npx "
            "and then try `algokit generate client ...` again.",
            npx=True,
        )
        npm_command = get_valid_npx_command(
            "Unable to find npm install so that the `algokit-client-generator` can be installed; "
            "please install npm via https://docs.npmjs.com/downloading-and-installing-node-js-and-npm "
            "and then try `algokit generate client ...` again.",
            npx=False,
        )
        client_generator_installation_command = [*npm_command, "list"]
        try:
            result = proc.run(client_generator_installation_command)
            typescript_client_generator_version_result = ""
            if result.exit_code == 0:
                for line in result.output.splitlines():
                    if TYPESCRIPT_NPX_PACKAGE in line:
                        typescript_client_generator_version_result = line
                        break

        except OSError:
            pass
        else:
            if typescript_client_generator_version_result != "":
                return [
                    *npx_command,
                    "--yes",
                    f"{TYPESCRIPT_NPX_PACKAGE}@{extract_version_triple(typescript_client_generator_version_result)}",
                ]

        return [
            *npx_command,
            "--yes",
            f"{TYPESCRIPT_NPX_PACKAGE}@latest",
        ]

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}Client{self.extension}"
