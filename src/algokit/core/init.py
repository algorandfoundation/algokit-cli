from enum import Enum

from copier.main import MISSING, AnswersMap, Question, Worker  # type: ignore[import]

DEFAULT_MIN_VERSION = "1.8.0"
DEFAULT_PROJECTS_ROOT_PATH = "projects"


class ProjectType(str, Enum):
    """
    For distinguishing main template preset type question invoked by `algokit init`
    """

    WORKSPACE = "workspace"
    BACKEND = "backend"  # any project focused on smart contracts or standalone backend services
    FRONTEND = "frontend"  # any project focused on user facing services


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


def _get_algokit_toml(
    project_type: ProjectType, min_version: str = "1.8.0", projects_root_path: str | None = None
) -> str:
    """
    Generates the TOML configuration for Algokit projects.

    Args:
        project_type (ProjectType): The type of the project (WORKSPACE, BACKEND, FRONTEND).
        min_version (str): Minimum version of Algokit required.
        projects_root_path (Optional[str]): The root path for projects, applicable only for WORKSPACE type.

    Returns:
        str: The TOML configuration as a string.
    """
    toml_config = f"""[algokit]
min_version = "{min_version}"
"""

    if project_type == ProjectType.WORKSPACE and projects_root_path:
        toml_config += f"""
[project]
type = '{project_type.value}'
projects_root_path = '{projects_root_path}'
"""
    else:
        toml_config += f"""
[project]
type = '{project_type.value}'
"""

    return toml_config


def get_default_algokit_toml(
    project_type: ProjectType,
    projects_root_path: str = DEFAULT_PROJECTS_ROOT_PATH,
    min_version: str = DEFAULT_MIN_VERSION,
) -> str:
    """
    Wrapper function to generate default Algokit TOML configuration.

    Args:
        project_type (ProjectType): The type of the project (WORKSPACE, BACKEND, FRONTEND).
        projects_root_path (str): The root path for projects, applicable only for WORKSPACE type.
        min_version (str): Minimum version of Algokit required.

    Returns:
        str: The TOML configuration as a string.
    """
    return _get_algokit_toml(
        project_type, min_version, projects_root_path if project_type == ProjectType.WORKSPACE else None
    )
