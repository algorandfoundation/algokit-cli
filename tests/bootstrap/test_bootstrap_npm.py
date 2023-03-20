import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.parametrize(
    "_mock_os_dependency",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["_mock_os_dependency"],
)
@pytest.mark.usefixtures("_mock_os_dependency")
def test_bootstrap_npm_without_npm(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest
) -> None:
    proc_mock.should_fail_on("npm install")
    proc_mock.should_fail_on("npm.cmd install")
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, namer=PyTestNamer(request))


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
def test_bootstrap_npm_without_package_file(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


@pytest.mark.parametrize(
    "_mock_os_dependency",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["_mock_os_dependency"],
)
@pytest.mark.usefixtures("_mock_os_dependency")
def test_bootstrap_npm_without_npm_and_package_file(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest
) -> None:
    proc_mock.should_fail_on("npm install")
    proc_mock.should_fail_on("npm.cmd install")
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


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
def test_bootstrap_npm_happy_path(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))
