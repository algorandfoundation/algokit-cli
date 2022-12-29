from _pytest.tmpdir import TempPathFactory
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_bootstrap_npm_with_lower_npm_version(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):
    proc_mock.set_output("node --version", ["v16.2.1"])
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_npm_with_npm_and_package_file(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):
    proc_mock.set_output("node --version", ["v18.12.1"])
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_npm_without_npm_with_package_file(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):

    proc_mock.should_fail_on("node --version")

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_npm_with_npm_without_package_file(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):

    proc_mock.set_output("node --version", ["v18.12.1"])
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_npm_without_npm_or_package_file(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):
    proc_mock.should_fail_on("node --version")

    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_npm(
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
):
    proc_mock.set_output("node --version", ["v18.12.1"])
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").write_text('{"dependencies": {"is-whitespace": "^0.3.0"}}', encoding="utf-8")

    result = invoke(
        "bootstrap npm",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)
