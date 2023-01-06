# AlgoKit Completions

AlgoKit supports shell completions for zsh and bash shells, e.g.

**bash**

```
$ algokit <Press Tab>
bootstrap    completions  config       doctor       explore      goal         init         sandbox
```

**zsh**

```
$ ~ algokit <Press Tab>
bootstrap    -- Bootstrap AlgoKit project dependencies.
completions  -- Install and Uninstall AlgoKit shell integration.
config       -- Configure AlgoKit options.
doctor       -- Run the Algorand doctor CLI.
explore      -- Explore the specified network in the...
goal         -- Run the Algorand goal CLI against the AlgoKit Sandbox.
init         -- Initializes a new project.
sandbox      -- Manage the AlgoKit sandbox.
```

## Installing

To setup the completions, AlgoKit provides commands that will modify the current users interactive shell script (`.bashrc`/`.zshrc`).

> **Note**
> If you would prefer AlgoKit to not modify your interactive shell scripts you can install the completions yourself by following the instructions [here](https://click.palletsprojects.com/en/8.1.x/shell-completion/).

To [install](../cli/index.md#install) completions for the current shell execute `algokit completions install`. You should see output similar to below:

```
$ ~ algokit completions install
AlgoKit completions installed for zsh 🎉
Restart shell or run `. ~/.zshrc` to enable completions
```

After installing the completions don't forget to restart the shell to begin using them!

## Uninstalling

To [uninstall](../cli/index.md#uninstall) completions for the current shell run `algokit completions uninstall`:

```
$ ~ algokit completions uninstall
AlgoKit completions uninstalled for zsh 🎉
```

## Shell Option

To install/uninstall the completions for a specific [shell](../cli/index.md#shell) the `--shell` option can be used e.g. `algokit completions install --shell bash`.

To learn more about the `algokit completions` command, please refer to [completions](../cli/index.md#completions) in the AlgoKit CLI reference documentation.
