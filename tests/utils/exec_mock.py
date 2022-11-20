from io import StringIO
from pathlib import Path
from typing import IO


class RunningProcessMock:

    _returncode: int | None
    _stdout: IO[str] | None

    def __init__(self, stdout: str, returncode: int | None = None):
        self._returncode = returncode
        self._stdout = StringIO(stdout)

    @property
    def returncode(self) -> int:
        return self._returncode or 0

    @property
    def stdout(self) -> IO[str] | None:
        return self._stdout

    def wait(self):
        pass

    def poll(self) -> None | int:
        return self._returncode


class ExecMock:

    fail_on: list[list[str]]
    bad_exit_on: list[list[str]]

    def __init__(self):
        self.fail_on = []
        self.bad_exit_on = []

    def should_fail_on(self, cmd: list[str] | str):
        self.fail_on.append(cmd.split() if isinstance(cmd, str) else cmd)

    def should_bad_exit_on(self, cmd: list[str] | str):
        self.bad_exit_on.append(cmd.split() if isinstance(cmd, str) else cmd)

    def get_run(self):
        def run(cmd: list[str], _cwd: Path | None, _env: dict[str, str] | None) -> RunningProcessMock:
            should_fail = cmd in self.fail_on
            if should_fail:
                raise FileNotFoundError(f"No such file or directory: {cmd[0]}")
            should_bad_exit = cmd in self.bad_exit_on
            return RunningProcessMock("STDOUT+STDERR", -1 if should_bad_exit else 0)

        return run
