class WhichMock:
    def __init__(self) -> None:
        self.paths: dict[str, str] = {}

    def add(self, cmd: str, path: str | None = None) -> str:
        path = path or f"/bin/{cmd}"
        self.paths[cmd] = path
        return path

    def remove(self, cmd: str) -> None:
        self.paths.pop(cmd, None)

    def which(self, cmd: str) -> str | None:
        return self.paths.get(cmd)
