import abc
import json
import logging
import re
import shutil
from pathlib import Path
from typing import ClassVar

import algokit_client_generator
import click

from algokit.core import proc

logger = logging.getLogger(__name__)

TYPESCRIPT_NPX_PACKAGE = "@algorandfoundation/algokit-client-generator@^2.2.2"


def _snake_case(s: str) -> str:
    s = s.replace("-", " ")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"[-\s]", "_", s).lower()


class ClientGenerator(abc.ABC):
    language: ClassVar[str]
    extension: ClassVar[str]

    _by_language: ClassVar[dict[str, type["ClientGenerator"]]] = {}
    _by_extension: ClassVar[dict[str, type["ClientGenerator"]]] = {}

    def __init_subclass__(cls, language: str, extension: str) -> None:
        cls.language = language
        cls.extension = extension
        cls._by_language[language] = cls
        cls._by_extension[extension] = cls

    @classmethod
    def languages(cls) -> list[str]:
        return list(cls._by_language.keys())

    @classmethod
    def create_for_language(cls, language: str) -> "ClientGenerator":
        return cls._by_language[language]()

    @classmethod
    def create_for_extension(cls, extension: str) -> "ClientGenerator":
        return cls._by_extension[extension]()

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
    def generate(self, app_spec: Path, output: Path) -> None:
        logger.info(f"Generating Python client code for application specified in {app_spec} and writing to {output}")
        algokit_client_generator.generate_client(app_spec, output)

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}_client{self.extension}"

    def format_contract_name(self, contract_name: str) -> str:
        return _snake_case(contract_name)


class TypeScriptClientGenerator(ClientGenerator, language="typescript", extension=".ts"):
    def __init__(self) -> None:
        npx_path = shutil.which("npx")
        if not npx_path:
            raise click.ClickException("Typescript generator requires Node.js and npx to be installed.")
        self._npx_path = npx_path

    def generate(self, app_spec: Path, output: Path) -> None:
        cmd = [
            self._npx_path,
            "--yes",
            TYPESCRIPT_NPX_PACKAGE,
            "generate",
            "-a",
            str(app_spec),
            "-o",
            str(output),
        ]
        logger.info(
            f"Generating TypeScript client code for application specified in {app_spec} and writing to {output}"
        )
        proc.run(
            cmd,
            bad_return_code_error_message=f"Client generation failed for {app_spec}.",
        )

    @property
    def default_output_pattern(self) -> str:
        return f"{{contract_name}}Client{self.extension}"
