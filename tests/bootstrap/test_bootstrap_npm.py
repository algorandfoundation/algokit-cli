import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer
from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


@pytest.fixture()
def mock_dependencies(request: pytest.FixtureRequest, mocker: MockerFixture) -> None:
    # Mock OS.platform
    platform_system: str = getattr(request, "param", "Darwin")
    platform_module = mocker.patch("algokit.core.bootstrap.platform")
    platform_module.system.return_value = platform_system


@pytest.mark.parametrize(
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_bootstrap_npm_without_npm(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mock_dependencies: None
):
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
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_bootstrap_npm_without_package_file(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mock_dependencies: None
):

    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


@pytest.mark.parametrize(
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_bootstrap_npm_without_npm_and_package_file(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mock_dependencies: None
):
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
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_bootstrap_npm_happy_path(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mock_dependencies: None
):
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))
