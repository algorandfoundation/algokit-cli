from pathlib import Path
from typing import Any, ClassVar

from textual.app import App

from algokit.core.init import ALGOKIT_TEMPLATES_DIR, ALGOKIT_USER_DIR

from .screens.example_selector_screen import ChooseExampleScreen

examples_config_path = str(
    (Path.home() / ALGOKIT_USER_DIR / ALGOKIT_TEMPLATES_DIR / "examples" / "examples.yml").absolute()
)

UserAnswers = dict[str, Any]


class ExampleSelector(App):
    SCREENS: ClassVar[dict] = {
        "example_selector": lambda: ChooseExampleScreen(examples_config_path),
    }
    ENABLE_COMMAND_PALETTE = False
    BINDINGS: ClassVar[list] = [
        ("b", "toggle_dark", "Toggle theme"),
        ("q", "quit", "Quit"),
    ]
    TITLE: str = "AlgoKit Examples"

    def __init__(self) -> None:
        super().__init__()
        self.user_answers: UserAnswers = {}

    def on_mount(self) -> None:
        # Disable the palette by not calling the default palette setup
        self.push_screen("example_selector")
