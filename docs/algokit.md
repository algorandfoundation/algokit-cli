# AlgoKit

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

## AlgoKit CLI commands

For details on how to use individual features see the following

- [AlgoKit Bootstrap](./features/bootstrap.md) - Bootstrap AlgoKit project dependencies
- [AlgoKit Completions](./features/completions.md) - Install shell completions for AlgoKit
- [AlgoKit Doctor](/features/doctor.md) - Check AlgoKit installation and dependencies
- [AlgoKit Explore](./features/explore.md) - Explore Algorand Blockchains using Dappflow
- [AlgoKit Goal](./features/goal.md) - Run the Algorand goal CLI against the AlgoKit Sandbox
- [AlgoKit Sandbox](./features/sandbox.md) - Manage a locally sandboxed private Algorand network

## AlgoKit CLI options

AlgoKit has a number of global options that can impact all commands

- `-h, --help` The help option can be used on any command to get details on any command, its sub-commands and options
- `-v, --verbose` Enables DEBUG logging, useful when troubleshooting
- `--color / --no-color` Enables or disables output of console styling, also supports the [NO_COLOR](https://no-color.org) environment variable
- `--skip-version-check` Skips version checking and prompting for a single command, this can also be disabled [permanently](./cli/index.md#version-prompt) with `algokit config version-prompt disable`

See also [AlgoKit CLI Reference](./cli/index.md)
