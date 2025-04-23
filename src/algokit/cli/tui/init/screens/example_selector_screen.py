from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from algokit.core.init import _load_algokit_examples

if TYPE_CHECKING:
    from algokit.cli.tui.init.example_selector import ExampleSelector


class ChooseExampleScreen(Screen):
    app: "ExampleSelector"
    """A screen that displays available example templates based on chosen framework."""

    CSS = """
    .margin-bottom-1 {
        margin-bottom: 1;
    }
    .examples-screen {
        height: auto;
        overflow-y: auto;
        width: 100%;
    }
    """
    SUB_TITLE = "Initialize Example"

    def __init__(self, examples_path: str) -> None:
        super().__init__()
        self.examples_path = examples_path
        # Use the imported load_examples function
        self.examples = _load_algokit_examples(examples_path)

    def compose(self) -> ComposeResult:
        yield Header(icon="📚")

        with Vertical(classes="examples-screen") as examples_container:
            self.examples_container = examples_container
            yield Label("Choose an example:", classes="margin-bottom-1")
            yield ListView(
                *[
                    ListItem(Label(f"{example['name']} - {example['type']}"), id=example["id"])
                    for example in self.examples
                ],
                id="input-example-choice",
            )

        yield Footer()

    @on(ListView.Selected, "#input-example-choice")
    def handle_example_selection(self, event: ListView.Selected) -> None:
        """Handle the selection of an example using the keyboard."""
        selected_item = event.item.id
        if selected_item:
            self.app.user_answers["example_id"] = selected_item
            self.app.exit()
