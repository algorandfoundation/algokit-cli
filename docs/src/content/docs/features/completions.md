---
title: "AlgoKit Completions"
---

AlgoKit supports shell completions for zsh and bash shells, e.g.

**bash**

```bash
algokit <Press Tab>
compile      completions  config       dispenser    doctor       explore      generate     goal         init         localnet     project      task
```

**zsh**

```zsh
algokit <Press Tab>
compile      -- Compile smart contracts and smart signatures...
completions  -- Install and Uninstall AlgoKit shell integrations.
config       -- Configure AlgoKit settings.
dispenser    -- Interact with the AlgoKit TestNet Dispenser.
doctor       -- Diagnose potential environment issues that may affect AlgoKit.
explore      -- Explore the specified network using lora.
generate     -- Generate code for an Algorand project.
goal         -- Run the Algorand goal CLI against the AlgoKit LocalNet.
init         -- Initializes a new project from a template;...
localnet     -- Manage the AlgoKit LocalNet.
project      -- Provides a suite of commands for managing your...
task         -- Collection of useful tasks to help you...
```

## Installing

To setup the completions, AlgoKit provides commands that will modify the current users interactive shell script (`.bashrc`/`.zshrc`).

> **Note**
> If you would prefer AlgoKit to not modify your interactive shell scripts you can install the completions yourself by following the instructions [here](https://click.palletsprojects.com/en/8.1.x/shell-completion/).

To [install](/algokit-cli/cli/#install) completions for the current shell execute `algokit completions install`. You should see output similar to below:

```bash
algokit completions install
AlgoKit completions installed for zsh 🎉
Restart shell or run `. ~/.zshrc` to enable completions
```

After installing the completions don't forget to restart the shell to begin using them!

## Uninstalling

To [uninstall](/algokit-cli/cli/#uninstall) completions for the current shell run `algokit completions uninstall`:

```bash
algokit completions uninstall
AlgoKit completions uninstalled for zsh 🎉
```

## Shell Option

To install/uninstall the completions for a specific [shell](/algokit-cli/cli/#shell) the `--shell` option can be used e.g. `algokit completions install --shell bash`.

To learn more about the `algokit completions` command, please refer to [completions](/algokit-cli/cli/#completions) in the AlgoKit CLI reference documentation.
