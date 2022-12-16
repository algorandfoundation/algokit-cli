import prompt_toolkit.document
import questionary


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


def _get_confirm_default_yes_prompt(prompt: str) -> bool:
    return bool(
        questionary.confirm(
            prompt,
            default=True,
        ).unsafe_ask()
    )
