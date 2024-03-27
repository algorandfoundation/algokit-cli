# AlgoKit Compile

The AlgoKit Compile feature enables you to compile smart contracts (apps) and smart signatures (logic signatures) written in a supported high-level language to a format deployable on the Algorand Virtual Machine (AVM).

When running the compile command, AlgoKit will take care of working out which compiler you need and dynamically resolve it. Additionally, AlgoKit will detect if a matching compiler version is already installed globally on your machine or is included in your project and use that.

## Prerequisites

See [Compile Python - Prerequisites](#prerequisites-1) for details.

## What is Algorand Python & PuyaPy?

Algorand Python is a semantically and syntactically compatible, typed Python language that works with standard Python tooling and allows you to express smart contracts (apps) and smart signatures (logic signatures) for deployment on the Algorand Virtual Machine (AVM).

Algorand Python can be deployed to Algorand by using the PuyaPy optimising compiler, which takes Algorand Python and outputs [ARC-32](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0032.md) application spec files (among other formats) which, [when deployed](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/generate.md#1-typed-clients), will result in AVM bytecode execution semantics that match the given Python code.

If you want to learn more, check out the [PuyaPy docs](https://github.com/algorandfoundation/puya/blob/main/docs/index.md).

Below is an example Algorand Python smart contract.

```py
from algopy import ARC4Contract, arc4

class HelloWorldContract(ARC4Contract):
    @arc4.abimethod
    def hello(self, name: arc4.String) -> arc4.String:
        return "Hello, " + name
```

For more complex examples, see the [examples](https://github.com/algorandfoundation/puya/tree/main/examples) in the [PuyaPy repo](https://github.com/algorandfoundation/puya).

## Usage

Available commands and possible usage are as follows:

```
Usage: algokit compile [OPTIONS] COMMAND [ARGS]...

  Compile smart contracts and smart signatures written in a supported high-level language to a format deployable on
  the Algorand Virtual Machine (AVM).

Options:
  -v, --version TEXT  The compiler version to pin to, for example, 1.0.0. If no version is specified, AlgoKit checks
                      if the compiler is installed and runs the installed version. If the compiler is not installed,
                      AlgoKit runs the latest version. If a version is specified, AlgoKit checks if an installed
                      version matches and runs the installed version. Otherwise, AlgoKit runs the specified version.
  -h, --help          Show this message and exit.

Commands:
  py      Compile Algorand Python contract(s) using the PuyaPy compiler.
  python  Compile Algorand Python contract(s) using the PuyaPy compiler.
```

### Compile Python

The command `algokit compile python` or `algokit compile py` will run the [PuyaPy](https://github.com/algorandfoundation/puya) compiler against the supplied Algorand Python smart contract.

All arguments supplied to the command are passed directly to PuyaPy, therefore this command supports all options supported by the PuyaPy compiler.

Any errors detected by PuyaPy during the compilation process will be printed to the output.

#### Prerequisites

PuyaPy requires Python 3.12+, so please ensure your Python version satisfies this requirement.

This command will attempt to resolve a matching installed PuyaPy compiler, either globally installed in the system or locally installed in your project (via [Poetry](https://python-poetry.org/)). If no appropriate match is found, the PuyaPy compiler will be dynamically run using [pipx](https://pipx.pypa.io/stable/). In this case pipx is also required.

#### Examples

To see a list of the supported PuyaPy options, run the following:

```shell
algokit compile python -h
```

To determine the version of the PuyaPy compiler in use, execute the following command:

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
