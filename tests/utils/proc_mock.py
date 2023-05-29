import dataclasses
from collections.abc import Sequence
from io import StringIO
from typing import IO, Any, TypeVar


class PopenMock:
    def __init__(self, stdout: str, returncode: int = 0, min_poll_calls: int = 1):
        self._returncode = returncode
        self._stdout = StringIO(stdout)
        self._remaining_poll_calls = min_poll_calls

    def __enter__(self) -> "PopenMock":
        return self

    def __exit__(self, *args: Any) -> None:
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


@dataclasses.dataclass
class CommandMockData:
    raise_not_found: bool = False
    raise_permission_denied: bool = False
    exit_code: int = 0
    output_lines: list[str] = dataclasses.field(default_factory=lambda: ["STDOUT", "STDERR"])


class ProcMock:
    def __init__(self) -> None:
        self._mock_data: dict[tuple[str, ...], CommandMockData] = {}
        self.called: list[list[str]] = []

    def _add_mock_data(self, cmd: list[str] | str, data: CommandMockData) -> None:
        cmd_list = tuple(cmd.split() if isinstance(cmd, str) else cmd)
        if cmd_list in self._mock_data:
            # update if exact match already exists
            self._mock_data[cmd_list] = data
            return
        # otherwise we quickly check to make sure we won't get surprising results due to ordering,
        # since if another command is a prefix of the one attempted to be added, and it comes before, this won't work
        without_overlapping_prefixes = {
            existing_cmd_prefix: data
            for existing_cmd_prefix, data in self._mock_data.items()
            if not sequence_starts_with(existing_cmd_prefix, cmd_list)
        }
        without_overlapping_prefixes[cmd_list] = data
        self._mock_data = without_overlapping_prefixes

    def should_fail_on(self, cmd: list[str] | str) -> None:
        self._add_mock_data(cmd, CommandMockData(raise_not_found=True))

    def should_deny_on(self, cmd: list[str] | str) -> None:
        self._add_mock_data(cmd, CommandMockData(raise_permission_denied=True))

    def should_bad_exit_on(self, cmd: list[str] | str, exit_code: int = -1, output: list[str] | None = None) -> None:
        if exit_code == 0:
            raise ValueError("zero is considered a good exit code")

        mock_data = CommandMockData(
            exit_code=exit_code,
        )
        if output is not None:
            mock_data.output_lines = output
        self._add_mock_data(cmd, mock_data)

    def set_output(self, cmd: list[str] | str, output: list[str]) -> None:
        self._add_mock_data(cmd, CommandMockData(output_lines=output))

    def popen(self, cmd: list[str], *_args: Any, **_kwargs: Any) -> PopenMock:
        self.called.append(cmd)
        for i in reversed(range(len(cmd))):
            prefix = cmd[: i + 1]
            try:
                mock_data = self._mock_data[tuple(prefix)]
            except KeyError:
                pass
            else:
                break
        else:
            mock_data = CommandMockData()

        if mock_data.raise_not_found:
            raise FileNotFoundError(f"No such file or directory: {cmd[0]}")
        if mock_data.raise_permission_denied:
            raise PermissionError(f"I'm sorry Dave I can't do {cmd[0]}")
        exit_code = mock_data.exit_code
        output = "\n".join(mock_data.output_lines)
        return PopenMock(output, exit_code)


T = TypeVar("T")


def sequence_starts_with(seq: Sequence[T], test: Sequence[T]) -> bool:
    """Like startswith, but for a generic sequence"""
    test_len = len(test)
    if len(seq) < test_len:
        return False
    return seq[:test_len] == test
