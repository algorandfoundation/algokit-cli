# Common constants, variables and enums used by the CLI.

from enum import Enum


# >= Py 3.11, there is a built-in StrEnum, however,
# we still support older versions of Python.
# Hence, a custom implementation for now.
class StringEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def to_list(cls) -> list[str]:
        return [member.value for member in cls]


class ExplorerEntityType(StringEnum):
    """
    Used to indicate type of entity when used with `get_explorer_url` function.
    """

    TRANSACTION = "transaction"
    ASSET = "asset"
    ADDRESS = "account"


class AlgorandNetwork(StringEnum):
    """
    Used to indicate the Algorand network.
    """

    LOCALNET = "localnet"
    TESTNET = "testnet"
    MAINNET = "mainnet"
