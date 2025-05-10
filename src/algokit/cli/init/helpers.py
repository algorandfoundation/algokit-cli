from dataclasses import dataclass
from enum import Enum

import click

from algokit.core.init import is_valid_project_dir_name


class TemplateKey(str, Enum):
    """
    For templates included in wizard v2 by default
    """

    BASE = "base"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    TEALSCRIPT = "tealscript"
    FULLSTACK = "fullstack"
    REACT = "react"


@dataclass(kw_only=True)
class TemplateSource:
    url: str
    commit: str | None = None
    """when adding a blessed template that is verified but not controlled by Algorand,
    ensure a specific commit is used"""
    branch: str | None = None
    answers: list[tuple[str, str]] | None = None

    def __str__(self) -> str:
        if self.commit:
            return "@".join([self.url, self.commit])
        return self.url


@dataclass(kw_only=True)
class BlessedTemplateSource(TemplateSource):
    description: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlessedTemplateSource):
            return NotImplemented
        return self.description == other.description and self.url == other.url


# Please note, the main reason why below is a function is due to the need to patch the values in unit/approval tests
def _get_blessed_templates() -> dict[TemplateKey, BlessedTemplateSource]:
    return {
        TemplateKey.TEALSCRIPT: BlessedTemplateSource(
            url="gh:algorand-devrel/tealscript-algokit-template",
            description="Official starter template for TEALScript applications.",
        ),
        TemplateKey.TYPESCRIPT: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-typescript-template",
            description="Official starter template for Algorand TypeScript (Beta) applications",
        ),
        TemplateKey.PYTHON: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-python-template",
            description="Official starter template for Algorand Python applications",
        ),
        TemplateKey.REACT: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-react-frontend-template",
            description="Official template for React frontend applications (smart contracts not included).",
        ),
        TemplateKey.FULLSTACK: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-fullstack-template",
            description="Official template for starter or production fullstack applications.",
        ),
        TemplateKey.BASE: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Official base template for enforcing workspace structure for standalone AlgoKit projects.",
        ),
    }


def _validate_dir_name(context: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is not None and not is_valid_project_dir_name(value):
        raise click.BadParameter(
            "Invalid directory name. Ensure it's a mix of letters, numbers, dashes, "
            "periods, and/or underscores, and not already used.",
            context,
            param,
        )
    return value
