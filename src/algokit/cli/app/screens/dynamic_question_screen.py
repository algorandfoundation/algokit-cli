from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, RadioSet, Rule, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class DynamicQuestionScreen(Screen):
    app: "ProjectWizard"
    SUB_TITLE = "Project Configuration"

    """A screen that displays all questions from YAML configuration."""

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
        # overflow-y: auto;
        width: 100%;
    }
    .question-screen {
        margin-top: 2;
        height: auto;
        overflow-y: auto;
        width: 100%;
    }
    .question-container {
        margin-bottom: 2;
        height: auto;
        border: solid $primary;
    }
    .help-text {
        color: $text-muted;
        padding-left: 1;
    }
    """
    CSS_PATH = "../styles.css"

    def __init__(self, config_path: str) -> None:
        super().__init__()
        self.config_path = config_path
        self.questions = self.load_questions(config_path)

    def compose(self) -> ComposeResult:
        yield Header(icon="🧮")

        with Vertical(classes="vertical-container margin-top-2"):
            yield Label("What would you like to call your project?", classes="question-label")
            yield Input(placeholder="My Project", id="input-project-name")

        # with Vertical(classes="vertical-container"):
        yield Button("Next", id="next", variant="primary", classes="margin-top-1")

        with Vertical(classes="vertical-container"):
            yield Static(
                "Change the values below to configure your project or hit next to accept the defaults.",
                classes="margin-top-2",
            )
            yield Rule(line_style="double", classes="margin-padding-0")
        with Vertical(classes="question-screen"):
            # Generate widgets for each question
            for question_key, question_data in self.questions.items():
                if question_key.startswith("_"):  # Skip metadata fields
                    continue
                if question_key == "project_name":
                    continue

                with Vertical(
                    classes="question-container",
                ):
                    yield Label(question_key.replace("_", " ").title(), classes="question-label")
                    yield Static(question_data.get("help", ""), classes="help-text")
                    yield self._create_input_widget(question_key, question_data)

        yield Footer()

    def _create_input_widget(self, question_key: str, question_data: dict[str, Any]) -> Widget:
        """Create the appropriate input widget based on question type."""
        question_type = question_data["type"]
        widget_id = f"input-{question_key}"

        if question_type == "str":
            if "choices" in question_data:
                choices = list(question_data["choices"].keys())
                return RadioSet(*choices, id=widget_id)
            else:
                default = str(question_data.get("default", ""))
                placeholder = question_data.get("placeholder", "")
                return Input(placeholder=placeholder, value=default, id=widget_id)

        elif question_type == "bool":
            default = question_data.get("default", False)
            if isinstance(default, str):
                default = default.lower() == "yes"
            return Checkbox("Yes", id=widget_id, value=default)

        raise ValueError(f"Unsupported question type: {question_type}")  # Add default case

    @on(Button.Pressed, "#next")
    def submit_answers(self) -> None:  # noqa: C901
        """Collect and validate all answers."""
        answers = {}
        has_errors = False

        # Check project name first
        project_name_input = self.query_one("#input-project-name", Input)
        if not project_name_input.value:
            self.notify("Please enter a project name", severity="error")
            project_name_input.focus()
            return
        answers["project_name"] = project_name_input.value

        for question_key, question_data in self.questions.items():
            if question_key.startswith("_"):
                continue
            if question_key == "project_name":
                continue

            widget_id = f"input-{question_key}"
            widget = self.query_one(f"#{widget_id}")

            if isinstance(widget, RadioSet):
                if widget.pressed_button is None:
                    self.notify(f"Please select an option for {question_key}", severity="error")
                    has_errors = True
                    continue
                if "choices" in question_data:
                    answers[question_key] = question_data["choices"][str(widget.pressed_button.label)]
                else:
                    answers[question_key] = str(widget.pressed_button.label)

            elif isinstance(widget, Input):
                if not widget.value and question_data.get("required", True):
                    self.notify(f"Please enter a value for {question_key}", severity="error")
                    has_errors = True
                    continue
                answers[question_key] = widget.value

            elif isinstance(widget, Checkbox):
                answers[question_key] = widget.value

        if not has_errors:
            self.app.user_answers["data"] = answers
            # Proceed to next screen or finish
            self.app.switch_screen("choose_example")

    @staticmethod
    def load_questions(config_path: str) -> dict[str, Any]:
        """Load and parse the questions from the YAML file."""
        with Path(config_path).open() as file:
            return yaml.safe_load(file)
