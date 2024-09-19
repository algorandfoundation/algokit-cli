# AlgoKit

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

## AlgoKit CLI commands

For details on how to use individual features see the following

- [Bootstrap](./features/project/bootstrap.md) - Bootstrap AlgoKit project dependencies
- [Compile](./features/compile.md) - Compile Algorand Python code
- [Completions](./features/completions.md) - Install shell completions for AlgoKit
- [Deploy](./features/project/deploy.md) - Deploy your smart contracts effortlessly to various networks
- [Dispenser](./features/dispenser.md) - Fund your TestNet account with ALGOs from the AlgoKit TestNet Dispenser
- [Doctor](./features/doctor.md) - Check AlgoKit installation and dependencies
- [Explore](./features/explore.md) - Explore Algorand Blockchains using lora
- [Generate](./features/generate.md) - Generate code for an Algorand project
- [Goal](./features/goal.md) - Run the Algorand goal CLI against the AlgoKit Sandbox
- [Init](./features/init.md) - Quickly initialize new projects using official Algorand Templates or community provided templates
- [LocalNet](./features/localnet.md) - Manage a locally sandboxed private Algorand network
- [Project](./features/project.md) - Manage an AlgoKit project workspace on your file system
- [Tasks](./features/tasks.md) - Perform a variety of useful operations on the Algorand blockchain

## Common AlgoKit CLI options

AlgoKit has a number of global options that can impact all commands. Note: these global options must be appended to `algokit` and appear before a command, e.g. `algokit -v localnet start`, but not `algokit localnet start -v`. The exception to this is `-h`, which can be appended to any command or sub-command to see contextual help information.

- `-h, --help` The help option can be used on any command to get details on any command, its sub-commands and options.
- `-v, --verbose` Enables DEBUG logging, useful when troubleshooting or if you want to peek under the covers and learn what AlgoKit CLI is doing.
- `--color / --no-color` Enables or disables output of console styling, we also support the [NO_COLOR](https://no-color.org) environment variable.
- `--skip-version-check` Skips updated AlgoKit version checking and prompting for that execution, this can also be disabled [permanently on a given machine](./cli/index.md#version-prompt) with `algokit config version-prompt disable`.

See also the [AlgoKit CLI Reference](./cli/index.md), which details every command, sub-command and option.

## AlgoKit Tutorials

The following tutorials guide you through various scenarios:

- [AlgoKit quick start](./tutorials/intro.md)
- [Creating AlgoKit templates](./tutorials/algokit-template.md)

## Guiding Principles

AlgoKit is guided by the following solution principles which flow through to the applications created by developers.

1. **Cohesive developer tool suite**: Using AlgoKit should feel professional and cohesive, like it was designed to work together, for the developer; not against them. Developers are guided towards delivering end-to-end, high quality outcomes on MainNet so they and Algorand are more likely to be successful.
2. **Seamless onramp**: New developers have a seamless experience to get started and they are guided into a pit of success with best practices, supported by great training collateral; you should be able to go from nothing to debugging code in 5 minutes.
3. **Leverage existing ecosystem**: AlgoKit functionality gets into the hands of Algorand developers quickly by building on top of the existing ecosystem wherever possible and aligned to these principles.
4. **Sustainable**: AlgoKit should be built in a flexible fashion with long-term maintenance in mind. Updates to latest patches in dependencies, Algorand protocol development updates, and community contributions and feedback will all feed in to the evolution of the software.
5. **Secure by default**: Include defaults, patterns and tooling that help developers write secure code and reduce the likelihood of security incidents in the Algorand ecosystem. This solution should help Algorand be the most secure Blockchain ecosystem.
6. **Extensible**: Be extensible for community contribution rather than stifling innovation, bottle-necking all changes through the Algorand Foundation and preventing the opportunity for other ecosystems being represented (e.g. Go, Rust, etc.). This helps make developers feel welcome and is part of the developer experience, plus it makes it easier to add features sustainably.
7. **Meet developers where they are**: Make Blockchain development mainstream by giving all developers an idiomatic development experience in the operating system, IDE and language they are comfortable with so they can dive in quickly and have less they need to learn before being productive.
8. **Modular components**: Solution components should be modular and loosely coupled to facilitate efficient parallel development by small, effective teams, reduced architectural complexity and allowing developers to pick and choose the specific tools and capabilities they want to use based on their needs and what they are comfortable with.
