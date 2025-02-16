from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RadioSet, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class DappTypeScreen(Screen):
    app: "ProjectWizard"
    CSS_PATH = "../styles.css"
    SUB_TITLE = "Choose Dapp Components"

    def compose(self) -> ComposeResult:
        yield Header(icon="🏗️")
        yield Vertical(
            Static("Choose Smart Contract Language", id="smart-contract-question"),
            RadioSet("Python", "TypeScript", id="smart-contract-type"),
            Static("Choose Frontend Framework", id="frontend-question"),
            RadioSet("Astro", "React", id="frontend-type"),
            Horizontal(Button("Next", id="next"), classes="button-container"),
        )
        yield Footer()

    def on_mount(self) -> None:
        # Focus the first radio button in the smart contract RadioSet
        self.query_one("#smart-contract-type").focus()

    @on(Button.Pressed, "#next")
    def submit_answer(self) -> None:
        smart_contract_set = self.query_one("#smart-contract-type", RadioSet)
        frontend_set = self.query_one("#frontend-type", RadioSet)

        if smart_contract_set.pressed_button is None:
            self.notify("Please select a smart contract language", severity="error")
            self.query_one("#smart-contract-type").focus()
            return

        if frontend_set.pressed_button is None:
            self.notify("Please select a frontend framework", severity="error")
            self.query_one("#frontend-type").focus()
            return

        self.app.user_answers["smart_contract_language"] = smart_contract_set.pressed_button.label
        self.app.user_answers["frontend_type"] = frontend_set.pressed_button.label
        # self.app.switch_screen("question3")  # Adjust this to your next screen  # noqa: ERA001
