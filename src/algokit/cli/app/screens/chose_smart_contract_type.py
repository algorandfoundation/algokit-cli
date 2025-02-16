from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RadioSet, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class SmartContractTypeScreen(Screen):
    app: "ProjectWizard"
    CSS = """
    .smart-contract-type-screen {
        margin-top: 2;
    }
    """
    CSS_PATH = "../styles.css"
    SUB_TITLE = "Choose Smart Contract Language"

    def compose(self) -> ComposeResult:
        yield Header(icon="🧮")
        yield Vertical(
            Static("Choose Smart Contract Language", id="question"),
            RadioSet("Python", "TypeScript", id="smart-contract-type"),
            Horizontal(Button("Next", id="next"), classes="button-container"),
            classes="smart-contract-type-screen",
        )
        yield Footer()

    def on_mount(self) -> None:
        # Focus the first radio button in the RadioSet
        self.query_one("#smart-contract-type").focus()

    @on(Button.Pressed, "#next")
    def submit_answer(self) -> None:
        radio_set = self.query_one("#smart-contract-type", RadioSet)
        if radio_set.pressed_button is None:
            self.notify("Please select a smart contract language", severity="error")
            self.query_one("#smart-contract-type").focus()
            return
        pressed_button_label = radio_set.pressed_button.label
        self.app.user_answers["framework"] = str(pressed_button_label)

        # Switch to the appropriate screen based on selection
        if pressed_button_label == "Python":
            self.app.switch_screen("python_smart_contract")
        else:  # TypeScript
            self.app.switch_screen("typescript_smart_contract")
