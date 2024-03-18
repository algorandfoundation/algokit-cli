# AlgoKit Compile

The AlgoKit Compile feature allows you to compile high level language smart contracts to TEAL.

## Functionality

The AlgoKit Compile feature allows you to compile high level language smart contracts to TEAL.

Supported languages are:

- Python is compiled to TEAL with [PuyaPy](https://github.com/algorandfoundation/puya). When using this feature, all PuyaPy options are supported.

# Examples

For example, to compile a Python smart contract and output to a directory, run

```
algokit compile python hello_world/contract.py --out-dir hello_world/out
```

Any compilation errors will be logged to the command line output.
