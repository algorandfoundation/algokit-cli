VALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT = """
from algopy import Contract, Txn, log


class HelloWorldContract(Contract):
    def approval_program(self) -> bool:
        name = Txn.application_args(0)
        log(b"Hello, " + name)
        return True

    def clear_state_program(self) -> bool:
        return True
"""

INVALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT = """
from algopy import Contract, Txn, log


class HelloWorldContract(Contract):
    def approval_program(self) -> bool:
        name = Txn.application_args_invalid(0)
        log(b"Hello, " + name)
        return True

    def clear_state_program(self) -> bool:
        return True
"""
