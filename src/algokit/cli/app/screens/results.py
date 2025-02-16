from typing import TYPE_CHECKING

import yaml
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

if TYPE_CHECKING:
    from algokit.cli.app.project_wizard import ProjectWizard


class ResultsScreen(Screen):
    SUB_TITLE = "Template Config"
    app: "ProjectWizard"

    def compose(self) -> ComposeResult:
        yield Header(icon="🧪")
        yield Vertical(Static("Your Answers", id="results-text"))
        yield Footer()

    def on_mount(self) -> None:
        results_text = self.query_one("#results-text", Static)
        results = {
            "Project Name": self.app.user_answers["data"]["project_name"],
            "type": self.app.user_answers["type"],
            "Framework": self.app.user_answers["framework"],
        }

        templates = []
        templates.append(
            {
                "source": "path/to/base/template",
                "data": self.app.user_answers["data"],
            }
        )
        if self.app.user_answers["example"]:
            templates.append(
                {
                    "source": "path/to/example/template",
                    "data": {
                        "framework_choice": self.app.user_answers["framework"],
                    },
                }
            )
        results["templates"] = templates

        results_text.update(yaml.dump(results, sort_keys=False, default_flow_style=False))
