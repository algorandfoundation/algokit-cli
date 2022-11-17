from approvaltests import verify
from click.testing import CliRunner

from algokit.cli import algokit


def test_sandbox_start():
    runner = CliRunner()
    result = runner.invoke(algokit, ["sandbox", "start"])
    assert result.exit_code == 0
    verify(result.stdout)
