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

VALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT = """
import { Contract } from '@algorandfoundation/algorand-typescript'

export class HelloWorld extends Contract {
  public hello(name: string): string {
    return `${this.getHello()} ${name}`
  }

  private getHello() {
    return 'Hello'
  }
}
"""

INVALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT = """
import { Contract } from '@algorandfoundation/algorand-typescript'

export class HelloWorld extends ContractInvalid {
  public hello(name: string): string {
    return `${this.getHello()} ${name}`
  }

  private getHello() {
    return 'Hello'
  }
}
"""
