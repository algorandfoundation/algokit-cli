import re
import shutil
from logging import getLogger

from copier.main import MISSING, AnswersMap, Question, Worker  # type: ignore[import]

from algokit.core.project import get_algokit_projects_names_from_workspace

logger = getLogger(__name__)

DEFAULT_MIN_VERSION = "1.8.0"
DEFAULT_PROJECTS_ROOT_PATH = "projects"


def populate_default_answers(worker: Worker) -> None:
    """Helper function to pre-populate Worker.data with default answers, based on Worker.answers implementation (see
    https://github.com/copier-org/copier/blob/v7.1.0/copier/main.py#L363).

    Used as a work-around for the behaviour of Worker(default=True, ...) which in >=7.1 raises an error instead of
    prompting if no default is provided"""
    answers = AnswersMap(
        user_defaults=worker.user_defaults,
        init=worker.data,
        last=worker.subproject.last_answers,
        metadata=worker.template.metadata,
    )

    for var_name, details in worker.template.questions_data.items():
        if var_name in worker.data:
            continue
        question = Question(
            answers=answers,
            jinja_env=worker.jinja_env,
            var_name=var_name,
            **details,
        )
        default_value = question.get_default()
        if default_value is not MISSING:
            worker.data[var_name] = default_value


def get_git_user_info(param: str) -> str | None:
    """Get git user info from the system. Returns None if git is not available."""

    from subprocess import check_output

    if not shutil.which("git"):
        return None

    try:
        return check_output(f"git config user.{param}", shell=True).decode("utf-8").strip()
    except Exception:
        logger.warning(
            f"Failed to get user info from git, please input your '{param}' manually or use default placeholder."
        )
        logger.debug("Failed to get user info from git", exc_info=True)
        return None


def is_valid_project_dir_name(value: str) -> bool:
    """Check if the project directory name for algokit project is valid."""

    algokit_project_names = get_algokit_projects_names_from_workspace()
    if value in algokit_project_names:
        return False
    if not re.match(r"^[\w\-.]+$", value):
        return False
    return True
