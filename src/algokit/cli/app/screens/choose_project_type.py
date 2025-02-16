from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RadioButton, RadioSet, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class ProjectTypeScreen(Screen):
    app: "ProjectWizard"
    CSS_PATH = "../styles.css"
    SUB_TITLE = "Choose Project Type"

    def compose(self) -> ComposeResult:
        yield Header(icon="🚀")
        yield Vertical(
            Static(
                """
    █████╗  ██╗      ██████╗  ██████╗ ██╗  ██╗██╗████████╗
   ██╔══██╗ ██║     ██╔════╝ ██╔═══██╗██║ ██╔╝██║╚══██╔══╝
   ███████║ ██║     ██║  ███╗██║   ██║█████╔╝ ██║   ██║
   ██╔══██║ ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║
   ██║  ██║ ███████╗╚██████╔╝╚██████╔╝██║  ██╗██║   ██║
   ╚═╝  ╚═╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝
            """,
                id="banner",
            ),
            Static("Choose Project Type", id="question"),
            RadioSet(
                "Smart Contract",
                "DApp Frontend",
                RadioButton("Smart Contract & DApp Frontend", disabled=True),
                id="project-type",
            ),
            Horizontal(Button("Next", id="next"), classes="button-container"),
        )
        yield Footer()

    def on_mount(self) -> None:
        # Focus the first radio button in the RadioSet
        self.query_one("#project-type").focus()

    @on(Button.Pressed, "#next")
    def submit_answer(self) -> None:
        radio_set = self.query_one("#project-type", RadioSet)
        if radio_set.pressed_button is None:
            self.notify("Please select a project type", severity="error")
            self.query_one("#project-type").focus()
            return
        pressed_button_label = str(radio_set.pressed_button.label)

        # Route to appropriate screen based on selection
        if pressed_button_label == "Smart Contract":
            self.app.user_answers["type"] = "smart_contract"
            self.app.switch_screen("smart_contract_type")
        elif pressed_button_label == "DApp Frontend":
            self.app.user_answers["type"] = "frontend"
            self.app.switch_screen("frontend_type")
        else:  # "Smart Contract & DApp Frontend"
            self.app.user_answers["type"] = "dapp"
            self.app.switch_screen("dapp_type")
