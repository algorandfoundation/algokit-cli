from io import StringIO
from typing import IO, Any


class PopenMock:
    def __init__(self, stdout: str, returncode: int = 0, min_poll_calls: int = 1):
        self._returncode = returncode
        self._stdout = StringIO(stdout)
        self._remaining_poll_calls = min_poll_calls

    def __enter__(self) -> "PopenMock":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        # TODO: we should change the structure of this mocking a bit,
        #       and check that I/O cleanup was called
        pass

    @property
    def returncode(self) -> int:
        return self._returncode or 0

    @property
    def stdout(self) -> IO[str] | None:
        return self._stdout

    def wait(self) -> int:
        return self._returncode

    def poll(self) -> int | None:
        if self._remaining_poll_calls > 0:
            self._remaining_poll_calls -= 1
            return None
        return self._returncode


class ExecMock:
    def __init__(self):
        self.fail_on: list[list[str]] = []
        self.bad_exit_on: list[list[str]] = []
        self._output: list[str] = []

    def should_fail_on(self, cmd: list[str] | str):
        self.fail_on.append(cmd.split() if isinstance(cmd, str) else cmd)

    def should_bad_exit_on(self, cmd: list[str] | str):
        self.bad_exit_on.append(cmd.split() if isinstance(cmd, str) else cmd)

    def set_output(self, *lines: str):
        self._output = lines

    def popen(self, cmd: list[str], *args: Any, **kwargs: Any) -> PopenMock:
        should_fail = cmd in self.fail_on
        if should_fail:
            raise FileNotFoundError(f"No such file or directory: {cmd[0]}")
        exit_code = -1 if cmd in self.bad_exit_on else 0
        output = "\n".join(self._output or ["STDOUT", "STDERR"])
        return PopenMock(output, exit_code)
