from collections.abc import Callable, Sequence
from typing import Any

import prompt_toolkit.document
import questionary
from questionary.prompts.common import build_validator


class NonEmptyValidator(questionary.Validator):
    def validate(self, document: prompt_toolkit.document.Document) -> None:
        value = document.text.strip()
        if not value:
            raise questionary.ValidationError(message="Please enter a value")


class ChainedValidator(questionary.Validator):
    def __init__(self, *validators: questionary.Validator):
        self._validators = validators

    def validate(self, document: prompt_toolkit.document.Document) -> None:
        for validator in self._validators:
            validator.validate(document)


def prompt_confirm(message: str, *, default: bool) -> bool:
    # note: we use unsafe_ask here (and everywhere else) so we don't have to
    # handle None returns for KeyboardInterrupt - click will handle these nicely enough for us
    # at the root level
    result = questionary.confirm(
        message,
        default=default,
    ).unsafe_ask()
    assert isinstance(result, bool)
    return result


def prompt_text(
    message: str,
    *,
    validators: Sequence[type[questionary.Validator] | questionary.Validator | Callable[[str], bool]] | None = None,
    validate_while_typing: bool = False,
) -> str:
    if validators:
        validate, *others = filter(None, map(build_validator, validators))
        if others:
            validate = ChainedValidator(validate, *others)
    else:
        validate = None
    result = questionary.text(
        message,
        validate=validate,
        validate_while_typing=validate_while_typing,
    ).unsafe_ask()
    assert isinstance(result, str)
    return result


def prompt_select(
    message: str,
    *choices: str | questionary.Choice,
) -> Any:  # noqa: ANN401
    return questionary.select(
        message,
        choices=choices,
    ).unsafe_ask()
