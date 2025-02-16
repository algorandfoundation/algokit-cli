from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RadioSet, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class FrontendTypeScreen(Screen):
    app: "ProjectWizard"
    CSS_PATH = "../styles.css"
    SUB_TITLE = "Choose Frontend Type"

    def compose(self) -> ComposeResult:
        yield Header(icon="🎨")
        yield Vertical(
            Static("Choose Frontend Framework", id="question"),
            RadioSet("Astro", "React", id="frontend-type"),
            Horizontal(Button("Next", id="next"), classes="button-container"),
        )
        yield Footer()

    def on_mount(self) -> None:
        # Focus the first radio button in the RadioSet
        self.query_one("#frontend-type").focus()

    @on(Button.Pressed, "#next")
    def submit_answer(self) -> None:
        radio_set = self.query_one("#frontend-type", RadioSet)
        if radio_set.pressed_button is None:
            self.notify("Please select a frontend framework", severity="error")
            self.query_one("#frontend-type").focus()
            return
        pressed_button_label = radio_set.pressed_button.label
        self.app.user_answers["framework"] = pressed_button_label

        # Switch to the appropriate screen based on selection
        if pressed_button_label == "Astro":
            self.app.switch_screen("frontend_astro")
        else:  # React
            self.app.switch_screen("frontend_vite_react")
