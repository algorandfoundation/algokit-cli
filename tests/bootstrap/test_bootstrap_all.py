import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_bootstrap_all_empty(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_all_env(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").touch()

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_poetry(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "poetry.toml").touch()

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize(
    "_mock_os_dependency",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["_mock_os_dependency"],
)
@pytest.mark.usefixtures("_mock_os_dependency", "proc_mock")
def test_bootstrap_all_npm(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_poetry_via_pyproject(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text("[tool.poetry]", encoding="utf-8")

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_all_skip_dirs(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".venv").mkdir()
    (cwd / "__pycache__").mkdir()
    (cwd / "node_modules").mkdir()
    (cwd / "file.txt").touch()
    (cwd / "empty_dir").mkdir()
    (cwd / "boring_dir").mkdir()
    (cwd / "boring_dir" / "file.txt").touch()
    (cwd / "double_nested_dir").mkdir()
    (cwd / "double_nested_dir" / "nest1").mkdir()
    (cwd / "double_nested_dir" / "nest2").mkdir()
    (cwd / "double_nested_dir" / "nest2" / "file.txt").touch()

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_sub_dir(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "empty_dir").mkdir()
    (cwd / "live_dir").mkdir()
    (cwd / "live_dir" / ".env.template").touch()
    (cwd / "live_dir" / "poetry.toml").touch()

    result = invoke(
        "bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)
