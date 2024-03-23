# AlgoKit Compile

The AlgoKit Compile feature enables you to compile smart contracts (apps) and smart signatures (logic signatures) written in a supported high-level language to TEAL, for deployment on the Algorand Virtual Machine (AVM).

When running the compile command, AlgoKit will take care of working out which compiler you need and dynamically resolve it. Additionally, AlgoKit will detect if an appropriate compiler version is already installed globally on your machine or is included in your project and utilize that.

## Prerequisites

See [Compile Python - Prerequisites](#prerequisites-1) for details.

## What is Algorand Python & PuyaPy?

Algorand Python is a semantically and syntactically compatible, typed Python language that works with standard Python tooling and allows you to express smart contracts (apps) and smart signatures (logic signatures) for deployment on the Algorand Virtual Machine (AVM).

This is done by compiling Algorand Python using the PuyaPy compiler, which takes Algorand Python and outputs valid, optimised TEAL code with execution semantics that match the given Python code.

If you want to know more, check out the [PuyaPy docs](https://github.com/algorandfoundation/puya/blob/main/docs/index.md).

The below example is a valid Algorand Python smart contract.

```py
from puyapy import ARC4Contract, arc4

class HelloWorldContract(ARC4Contract):
    @arc4.abimethod
    def hello(self, name: arc4.String) -> arc4.String:
        return "Hello, " + name
```

For more complex examples, check out the [examples](https://github.com/algorandfoundation/puya/tree/main/examples) in the [PuyaPy repo](https://github.com/algorandfoundation/puya).

## Usage

Available commands and possible usage are as follows:

```
Usage: algokit compile [OPTIONS] COMMAND [ARGS]...

  Compile smart contracts written in a high-level language to TEAL.

Options:
  -v, --version TEXT  The compiler version to pin to, for example, 1.0.0. If no version is specified, AlgoKit checks
                      if the compiler is installed and runs the installed version. If the compiler is not installed,
                      AlgoKit runs the latest version. If a version is specified, AlgoKit checks if an installed
                      version matches and runs the installed version. Otherwise, AlgoKit runs the specified version.
  -h, --help          Show this message and exit.

Commands:
  py      Compile Python contract(s) to TEAL using the PuyaPy compiler.
  python  Compile Python contract(s) to TEAL using the PuyaPy compiler.
```

### Compile Python

The command `algokit compile python` or `algokit compile py` will run the [PuyaPy](https://github.com/algorandfoundation/puya) compiler against the supplied Algorand Python smart contract.

All arguments supplied to the command are passed directly to PuyaPy and as such this command supports all options of the specific PuyaPy compiler version being used.

Any errors detected by PuyaPy during the compilation process will be printed to the output.

#### Prerequisites

PuyaPy requires Python 3.12+, so please ensure your Python version satisfies this requirement.

This command will attempt to resolve a matching installed PuyaPy compiler, either globally installed in the system or locally installed in your project (via [Poetry](https://python-poetry.org/)). If no appropriate match is found, the PuyaPy compiler will be dynamically loaded using [pipx](https://pipx.pypa.io/stable/). In this scenario pipx is also required.

#### Examples

To see a list of the supported PuyaPy options, run the following:

```shell
algokit compile python -h
```

To check which version of the PuyaPy compiler is being used, run the following:

```shell
algokit compile python --version
```

To compile a single Algorand Python smart contract and write the output to a specific location, run the following:

```shell
algokit compile python hello_world/contract.py --out-dir hello_world/out
```

To compile multiple Algorand Python smart contracts and write the output to a specific location, run the following:

```shell
algokit compile python hello_world/contract.py calculator/contract.py --out-dir my_contracts
```

To compile a directory of Algorand Python smart contracts and write the output to the default location, run the following:

```shell
algokit compile python my_contracts
```
