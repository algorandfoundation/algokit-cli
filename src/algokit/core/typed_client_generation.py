import abc
import json
import logging
import re
import shutil  # noqa: F401
from pathlib import Path
from typing import ClassVar

import click

from algokit.core import proc
from algokit.core.utils import extract_version_triple, find_valid_pipx_command, get_npm_command

logger = logging.getLogger(__name__)

TYPESCRIPT_NPM_PACKAGE = "@algorandfoundation/algokit-client-generator"
TYPESCRIPT_GENERATE_COMMAND = "algokitgen-ts"
PYTHON_PYPI_PACKAGE = "algokit-client-generator"
PYTHON_GENERATE_COMMAND = "algokitgen-py"


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
        self.command = self.find_generate_command(version)

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
        return cls._by_language[language](version)

    @classmethod
    def create_for_extension(cls, extension: str, version: str | None) -> "ClientGenerator":
        return cls._by_extension[extension](version)

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
    def generate(self, app_spec: Path, output: Path) -> None: ...

    @property
    @abc.abstractmethod
    def default_output_pattern(self) -> str: ...

    @abc.abstractmethod
    def find_generate_command(self, version: str | None) -> list[str]: ...

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

    def find_project_generate_command(self, version: str | None) -> list[str] | None:
        """
        Try find the generate command in the project.
        """
        try:
            # Use the tree output as it puts the package info on the first line of the output
            result = proc.run(["poetry", "show", PYTHON_PYPI_PACKAGE, "--tree"])
            if result.exit_code == 0:
                generate_command = ["poetry", "run", PYTHON_GENERATE_COMMAND]
                if version is not None:
                    installed_version = None
                    lines = result.output.splitlines()
                    if len(lines) > 0:
                        installed_version = extract_version_triple(lines[0])
                        if extract_version_triple(version) == installed_version:
                            return generate_command
                else:
                    return generate_command
        except OSError:
            pass
        except ValueError:
            pass

        return None

    def find_global_generate_command(self, pipx_command: list[str], version: str | None) -> list[str] | None:
        """
        Try find the generate command installed globally.
        """
        try:
            result = proc.run([*pipx_command, "list", "--short"])
            if result.exit_code == 0:
                generate_command = [PYTHON_GENERATE_COMMAND]
                for line in result.output.splitlines():
                    if PYTHON_PYPI_PACKAGE in line:
                        if version is not None:
                            installed_version = None
                            installed_version = extract_version_triple(line)
                            if extract_version_triple(version) == installed_version:
                                return generate_command
                        else:
                            return generate_command
        except OSError:
            pass
        except ValueError:
            pass

        return None

    def find_generate_command(self, version: str | None) -> list[str]:
        """
        Find Python generator command.
        If a matching version is installed at a project level, use that.
        If a matching version is installed at a global level, use that.
        Otherwise, run the matching version via pipx.
        """

        logger.debug("Searching for project installed client generator")
        project_result = self.find_project_generate_command(version)
        if project_result is not None:
            return project_result

        pipx_command = find_valid_pipx_command(
            f"Unable to find pipx install so that the `{PYTHON_PYPI_PACKAGE}` can be run; "
            "please install pipx via https://pypa.github.io/pipx/ "
            "and then try `algokit generate client ...` again."
        )

        logger.debug("Searching for globally installed client generator")
        global_result = self.find_global_generate_command(pipx_command, version)
        if global_result is not None:
            return global_result

        # when not installed, run via pipx
        logger.debug("No matching installed client generator found, run client generator via pipx")
        return [
            *pipx_command,
            "run",
            f"--spec={PYTHON_PYPI_PACKAGE}{f'=={version}' if version is not None else ''}",
            PYTHON_GENERATE_COMMAND,
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

    def find_project_generate_command(
        self, npm_command: list[str], npx_command: list[str], version: str | None
    ) -> list[str] | None:
        try:
            result = proc.run([*npm_command, "ls"])
            if result.exit_code == 0:
                generate_command = [*npx_command, TYPESCRIPT_NPM_PACKAGE]
                for line in result.output.splitlines():
                    if TYPESCRIPT_NPM_PACKAGE in line:
                        if version is not None:
                            installed_version = extract_version_triple(line)
                            if extract_version_triple(version) == installed_version:
                                return generate_command
                        else:
                            return generate_command
        except OSError:
            pass
        except ValueError:
            pass

        return None

    def find_global_generate_command(
        self, npm_command: list[str], npx_command: list[str], version: str | None
    ) -> list[str] | None:
        return self.find_project_generate_command([*npm_command, "--global"], npx_command, version)

    def find_generate_command(self, version: str | None) -> list[str]:
        """
        Find TypeScript generator command.
        If a matching version is installed at a project level, use that.
        If a matching version is installed at a global level, use that.
        Otherwise, run the matching version via npx.
        """

        npm_command = get_npm_command(
            f"Unable to find npm install so that the `{TYPESCRIPT_NPM_PACKAGE}` can be run; "
            "please install npm via https://docs.npmjs.com/downloading-and-installing-node-js-and-npm "
            "and then try `algokit generate client ...` again.",
        )
        npx_command = get_npm_command(
            f"Unable to find npx install so that the `{TYPESCRIPT_NPM_PACKAGE}` can be run; "
            "please install npx via https://www.npmjs.com/package/npx "
            "and then try `algokit generate client ...` again.",
            is_npx=True,
        )

        logger.debug("Searching for project installed client generator")
        project_result = self.find_project_generate_command(npm_command, npx_command, version)
        if project_result is not None:
            return project_result

        logger.debug("Searching for globally installed client generator")
        global_result = self.find_global_generate_command(npm_command, npx_command, version)
        if global_result is not None:
            return global_result

        # when not installed, run via npx
        logger.debug("No matching installed client generator found, run client generator via npx")
        return [
            *npx_command,
            "--yes",
            f"{TYPESCRIPT_NPM_PACKAGE}@{version if version is not None else 'latest'}",
        ]

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}Client{self.extension}"
