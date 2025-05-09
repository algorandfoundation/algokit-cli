import json
import re
import shutil
from logging import getLogger
from pathlib import Path
from typing import Any, cast

from copier._main import Worker
from copier._types import MISSING
from copier._user_data import AnswersMap, Question

from algokit.core.project import get_project_dir_names_from_workspace

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
            # https://github.com/copier-org/copier/releases/tag/v9.7.0 introduces changes to Question model,
            # which now requires passing context param.
            context={**worker._render_context(), **answers.combined},  # noqa: SLF001
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

    algokit_project_names = get_project_dir_names_from_workspace()
    if value in algokit_project_names:
        return False
    if not re.match(r"^[\w\-.]+$", value):
        return False
    return True


def resolve_vscode_workspace_file(project_root: Path | None) -> Path | None:
    """Resolve the path to the VSCode workspace file for the given project.
    Works by looking for algokit workspace and checking if there is a matching
    vscode config at the same level."""
    if not project_root:
        return None
    return next(project_root.glob("*.code-workspace"), None)


def append_project_to_vscode_workspace(project_path: Path, workspace_path: Path) -> None:
    """Append project to the code workspace, ensuring compatibility across Windows and Unix systems."""
    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace path {workspace_path} does not exist.")

    try:
        workspace = _load_vscode_workspace(workspace_path)

        # Compute the project path relative to the workspace root
        processed_project_path = project_path.relative_to(workspace_path.parent)
        project_abs_path = (workspace_path.parent / processed_project_path).resolve(strict=False)

        # Gather existing paths as absolute paths
        existing_abs_paths = []
        for folder in workspace.get("folders", []):
            folder_path = Path(folder.get("path", "").replace("\\", "/"))
            existing_abs_path = (workspace_path.parent / folder_path).resolve(strict=False)
            existing_abs_paths.append(existing_abs_path)

        # Check if the project path is already in the workspace
        if project_abs_path not in existing_abs_paths:
            workspace.setdefault("folders", []).append({"path": str(processed_project_path).replace("\\", "/")})
            _save_vscode_workspace(workspace_path, workspace)
            logger.debug(f"Appended project {project_path} to workspace {workspace_path}.")
        else:
            logger.debug(f"Project {project_path} is already in workspace {workspace_path}, not appending.")

    except json.JSONDecodeError as json_err:
        logger.warning(f"Invalid JSON format in the workspace file {workspace_path}. {json_err}")
    except Exception as e:
        logger.warning(f"Failed to append project {project_path} to workspace {workspace_path}. {e}")


def _load_vscode_workspace(workspace_path: Path) -> dict[str, Any]:
    """Load the workspace file as a JSON object."""
    with workspace_path.open(mode="r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, dict)
        return cast(dict[str, Any], data)


def _save_vscode_workspace(workspace_path: Path, workspace: dict) -> None:
    """Save the modified workspace back to the file."""
    with workspace_path.open(mode="w", encoding="utf-8") as f:
        json.dump(workspace, f, indent=2)
