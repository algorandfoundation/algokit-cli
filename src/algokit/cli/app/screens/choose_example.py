from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RadioSet, Rule

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class ChooseExampleScreen(Screen):
    app: "ProjectWizard"
    """A screen that displays available example templates based on chosen framework."""

    CSS = """
    .margin-top-1 {
        margin-top: 1;
    }
    .margin-top-2 {
        margin-top: 2;
    }
    .margin-padding-0 {
        margin: 0;
        padding: 0;
    }
    .vertical-container {
        height: auto;
        width: 100%;
    }
    .examples-screen {
        margin-top: 2;
        height: auto;
        overflow-y: auto;
        width: 100%;
    }
    """
    CSS_PATH = "../styles.css"
    SUB_TITLE = "Add Example"

    def __init__(self, examples_path: str) -> None:
        super().__init__()
        self.examples_path = examples_path
        self.examples = self.load_examples(examples_path, self.app.user_answers.get("framework", ""))

    def compose(self) -> ComposeResult:
        yield Header(icon="📚")

        with Vertical(classes="vertical-container margin-top-2"):
            yield Label("Would you like to add an example to your project?")
            yield RadioSet("Yes", "No", id="input-add-example")

        with Vertical(classes="examples-screen") as examples_container:
            self.examples_container = examples_container
            # Examples will be dynamically added here when "Yes" is selected

        with Vertical(classes="vertical-container"):
            yield Button("Next", id="next", variant="primary", classes="margin-top-1")
            yield Rule(line_style="double", classes="margin-padding-0")

        yield Footer()

    @on(RadioSet.Changed, "#input-add-example")
    def handle_add_example_change(self, event: RadioSet.Changed) -> None:
        """Show or hide example choices based on selection."""
        examples_container = self.query_one(".examples-screen")
        examples_container.remove_children()

        if str(event.pressed.label) == "Yes":
            examples_container.mount(
                Label("Choose an example:", classes="margin-top-2"),
                RadioSet(
                    *self.examples,
                    id="input-example-choice",
                ),
            )

    @on(Button.Pressed, "#next")
    def submit_selection(self) -> None:
        """Process the example selection and move to the next screen."""
        add_example = self.query_one("#input-add-example", RadioSet)

        if add_example.pressed_button is None:
            self.notify("Please select whether to add an example", severity="error")
            return

        if str(add_example.pressed_button.label) == "Yes":
            example_choice = self.query_one("#input-example-choice", RadioSet)
            if example_choice.pressed_button is None:
                self.notify("Please select an example", severity="error")
                return
            self.app.user_answers["example"] = str(example_choice.pressed_button.label)
        else:
            self.app.user_answers["example"] = None

        self.app.switch_screen("results")

    @staticmethod
    def load_examples(examples_path: str, user_chosen_framework: str) -> list[str]:
        """
        Load and parse the examples from directories containing copier config files.

        Args:
            examples_path: Path to the directory containing example templates

        Returns:
            A dictionary of valid example templates with their copier configurations
        """
        examples = []
        examples_dir = Path(examples_path)

        for template_dir in examples_dir.iterdir():
            if not template_dir.is_dir():
                continue

            # Check for copier.yml or copier.yaml
            copier_file = next(
                (f for f in template_dir.glob("copier.y*ml") if f.is_file()),
                None,
            )

            if copier_file:
                with copier_file.open() as file:
                    file_content = yaml.safe_load(file)
                    framework_choices = file_content.get("framework_choice", {}).get("choices", [])
                    if user_chosen_framework.lower() in framework_choices:
                        examples.append(template_dir.stem)

        return examples
