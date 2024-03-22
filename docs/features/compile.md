# AlgoKit Compile

The AlgoKit Compile feature enables you to compile smart contract applications written in a supported high level language to TEAL.

When running the compile command, AlgoKit will take care of working out which compiler you need and dynamically resolve it. Additionally AlgoKit will detect if an appropriate compiler version is already installed globally on your machine or is included in your project and utilise that.

## Prerequisites

This command dynamically loads the appropriate compiler using [pipx](https://pipx.pypa.io/stable/). As such pipx is required when using this command.

## What is Puya and PuyaPy?

Puya is a multi-stage optimizing TEAL compiler, that allows developers to write Python smart contracts using the PuyaPy syntax.

If you want to know more, take a peek at the [Puya docs](https://github.com/algorandfoundation/puya/blob/main/docs/index.md).

The below example is a valid PuyaPy Python smart contract.

```py
from puyapy import ARC4Contract, arc4

class HelloWorldContract(ARC4Contract):
    @arc4.abimethod
    def hello(self, name: arc4.String) -> arc4.String:
        return "Hello, " + name
```

For more complex example, check out the [examples](https://github.com/algorandfoundation/puya/tree/main/examples) directory in the [Puya repo](https://github.com/algorandfoundation/puya).

## Usage

Available commands and possible usage is as follows:

```
Usage: algokit compile [OPTIONS] COMMAND [ARGS]...

  Compile smart contracts written in a high level language to TEAL.

Options:
  -v, --version TEXT  The compiler version to pin to, for example, 1.0.0. If no version is specified, AlgoKit checks
                      if the compiler is installed and runs the installed version. If the compiler is not installed,
                      AlgoKit runs the latest version.If a version is specified, AlgoKit checks if an installed
                      version matches and runs the installed version. Otherwise, AlgoKit runs the specified version.
  -h, --help          Show this message and exit.

Commands:
  py      Compile Python contract(s) to TEAL using the PuyaPy compiler.
  python  Compile Python contract(s) to TEAL using the PuyaPy compiler.
```

### Compile Python

The command `algokit compile python` or `algokit compile py` will run the [PuyaPy](https://github.com/algorandfoundation/puya) compiler against the supplied PuyaPy compatible Python smart contract.

All arguments supplied to the command are passed directly to PuyaPy and as such this command supports all options of the specific PuyaPy compiler version being used.

Any errors detected by PuyaPy during the compilation process will be printed to the output.

#### Examples

To see a list of the supported PuyaPy options, run the following:

```shell
algokit compile python -h
```

To check which version of the PuyaPy compiler is being used, run the following:

```shell
algokit compile python --version
```

To compile a single PuyaPy Python smart contract and write the output to a specific location, run the following:

```shell
algokit compile python hello_world/contract.py --out-dir hello_world/out
```

To compile multiple PuyaPy Python smart contracts and write the output to a specific location, run the following:

```shell
algokit compile python hello_world/contract.py calculator/contract.py --out-dir my_contracts
```

To compile a directory of PuyaPy Python smart contracts and write the output to the default location, run the following:

```shell
algokit compile python my_contracts
```
