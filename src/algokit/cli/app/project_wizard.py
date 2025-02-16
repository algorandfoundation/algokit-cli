from pathlib import Path
from typing import Any, ClassVar

from textual.app import App

from .screens.choose_dapp_type import DappTypeScreen
from .screens.choose_example import ChooseExampleScreen
from .screens.choose_frontend_type import FrontendTypeScreen
from .screens.choose_project_type import ProjectTypeScreen
from .screens.chose_smart_contract_type import SmartContractTypeScreen
from .screens.dynamic_question_screen import DynamicQuestionScreen
from .screens.results import ResultsScreen

python_smart_contract_config_path = (
    Path.home()
    / ".algokit"
    / "templates-gallery-spike"
    / "templates"
    / "base-templates"
    / "python-smart-contract"
    / "copier.yaml"
)
typescript_smart_contract_config_path = (
    Path.home()
    / ".algokit"
    / "templates-gallery-spike"
    / "templates"
    / "base-templates"
    / "typescript-smart-contract"
    / "copier.yaml"
)
frontend_astro_config_path = (
    Path.home()
    / ".algokit"
    / "templates-gallery-spike"
    / "templates"
    / "base-templates"
    / "frontend-astro"
    / "copier.yml"
)

frontend_vite_react_config_path = (
    Path.home()
    / ".algokit"
    / "templates-gallery-spike"
    / "templates"
    / "base-templates"
    / "frontend-vite-react"
    / "copier.yml"
)

dapp_template_config_path = (
    Path.home()
    / ".algokit"
    / "templates-gallery-spike"
    / "templates"
    / "base-templates"
    / "dapp-template"
    / "copier.yml"
)

examples_path = Path.home() / ".algokit" / "templates-gallery-spike" / "templates"

UserAnswers = dict[str, Any]


class ProjectWizard(App):
    SCREENS: ClassVar[dict] = {
        "project_type": ProjectTypeScreen,
        "smart_contract_type": SmartContractTypeScreen,
        "frontend_type": FrontendTypeScreen,
        "dapp_type": DappTypeScreen,
        "python_smart_contract": lambda: DynamicQuestionScreen(config_path=str(python_smart_contract_config_path)),
        "typescript_smart_contract": lambda: DynamicQuestionScreen(
            config_path=str(typescript_smart_contract_config_path)
        ),
        "frontend_astro": lambda: DynamicQuestionScreen(config_path=str(frontend_astro_config_path)),
        "frontend_vite_react": lambda: DynamicQuestionScreen(config_path=str(frontend_vite_react_config_path)),
        "dapp_template": lambda: DynamicQuestionScreen(config_path=str(dapp_template_config_path)),
        "results": ResultsScreen,
        "choose_example": lambda: ChooseExampleScreen(examples_path=str(examples_path)),
    }
    BINDINGS: ClassVar[list] = [("b", "toggle_dark", "Toggle dark mode")]
    TITLE: ClassVar[str] = "Algokit Project Wizard"

    def __init__(self):
        super().__init__()
        self.user_answers: UserAnswers = {}

    def on_mount(self) -> None:
        # Push the initial screen after the app is mounted
        self.push_screen("project_type")
