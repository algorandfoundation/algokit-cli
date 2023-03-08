# AlgoKit

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

## AlgoKit CLI commands

For details on how to use individual features see the following

- [Bootstrap](./features/bootstrap.md) - Bootstrap AlgoKit project dependencies
- [Completions](./features/completions.md) - Install shell completions for AlgoKit
- [Doctor](./features/doctor.md) - Check AlgoKit installation and dependencies
- [Explore](./features/explore.md) - Explore Algorand Blockchains using Dappflow
- [Goal](./features/goal.md) - Run the Algorand goal CLI against the AlgoKit Sandbox
- [Init](./features/init.md) - Quickly initialize new projects using official Algorand Templates or community provided templates.
- [LocalNet](./features/localnet.md) - Manage a locally sandboxed private Algorand network.

## AlgoKit CLI options

AlgoKit has a number of global options that can impact all commands. Note: these global options must be appended to `algokit` and appear before a command, e.g. `algokit -v localnet start`, but not `algokit localnet start -v`. The exception to this is `-h`, which can be appended to any command or sub-command to see contextual help information.

- `-h, --help` The help option can be used on any command to get details on any command, its sub-commands and options.
- `-v, --verbose` Enables DEBUG logging, useful when troubleshooting or if you want to peek under the covers and learn what AlgoKit CLI is doing.
- `--color / --no-color` Enables or disables output of console styling, we also support the [NO_COLOR](https://no-color.org) environment variable.
- `--skip-version-check` Skips updated AlgoKit version checking and prompting for that execution, this can also be disabled [permanently on a given machine](./cli/index.md#version-prompt) with `algokit config version-prompt disable`.

See also the [AlgoKit CLI Reference](./cli/index.md), which details every command, sub-command and option.
