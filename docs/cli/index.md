# AlgoKit CLI Reference Documentation


- [algokit](#algokit)
    - [Options](#options)
    - [--version](#--version)
    - [-v, --verbose](#-v---verbose)
    - [--color, --no-color](#--color---no-color)
    - [--skip-version-check](#--skip-version-check)
  - [bootstrap](#bootstrap)
    - [all](#all)
    - [env](#env)
    - [npm](#npm)
    - [poetry](#poetry)
  - [completions](#completions)
    - [install](#install)
    - [Options](#options-1)
    - [--shell ](#--shell-)
    - [uninstall](#uninstall)
    - [Options](#options-2)
    - [--shell ](#--shell--1)
  - [config](#config)
    - [version-prompt](#version-prompt)
    - [Arguments](#arguments)
    - [ENABLE](#enable)
  - [doctor](#doctor)
    - [Options](#options-3)
    - [-c, --copy-to-clipboard](#-c---copy-to-clipboard)
  - [explore](#explore)
    - [Arguments](#arguments-1)
    - [NETWORK](#network)
  - [goal](#goal)
    - [Options](#options-4)
    - [--console](#--console)
    - [Arguments](#arguments-2)
    - [GOAL_ARGS](#goal_args)
  - [init](#init)
    - [Options](#options-5)
    - [-n, --name ](#-n---name-)
    - [-t, --template ](#-t---template-)
    - [--template-url ](#--template-url-)
    - [--template-url-ref ](#--template-url-ref-)
    - [--UNSAFE-SECURITY-accept-template-url](#--unsafe-security-accept-template-url)
    - [--git, --no-git](#--git---no-git)
    - [--defaults](#--defaults)
    - [--bootstrap, --no-bootstrap](#--bootstrap---no-bootstrap)
    - [-a, --answer  ](#-a---answer--)
  - [localnet](#localnet)
    - [console](#console)
    - [explore](#explore-1)
    - [reset](#reset)
    - [Options](#options-6)
    - [--update, --no-update](#--update---no-update)
    - [start](#start)
    - [status](#status)
    - [stop](#stop)

# algokit

AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.

```shell
algokit [OPTIONS] COMMAND [ARGS]...
```

### Options


### --version
Show the version and exit.


### -v, --verbose
Enable logging of DEBUG messages to the console.


### --color, --no-color
Force enable or disable of console output styling.


### --skip-version-check
Skip version checking and prompting.

## bootstrap

Bootstrap AlgoKit project dependencies.

```shell
algokit bootstrap [OPTIONS] COMMAND [ARGS]...
```

### all

Bootstrap all aspects of the current directory and immediate sub directories by convention.

```shell
algokit bootstrap all [OPTIONS]
```

### env

Bootstrap .env file in the current working directory.

```shell
algokit bootstrap env [OPTIONS]
```

### npm

Bootstrap Node.js project in the current working directory.

```shell
algokit bootstrap npm [OPTIONS]
```

### poetry

Bootstrap Python Poetry and install in the current working directory.

```shell
algokit bootstrap poetry [OPTIONS]
```

## completions

Install and Uninstall AlgoKit shell integration.

```shell
algokit completions [OPTIONS] COMMAND [ARGS]...
```

### install

Install shell completions, this command will attempt to update the interactive profile script for the current shell to support algokit completions. To specify a specific shell use –shell.

```shell
algokit completions install [OPTIONS]
```

### Options


### --shell <shell>
Specify shell to install algokit completions for.


* **Options**

    bash | zsh


### uninstall

Uninstall shell completions, this command will attempt to update the interactive profile script for the current shell to remove any algokit completions that have been added. To specify a specific shell use –shell.

```shell
algokit completions uninstall [OPTIONS]
```

### Options


### --shell <shell>
Specify shell to install algokit completions for.


* **Options**

    bash | zsh


## config

Configure AlgoKit options.

```shell
algokit config [OPTIONS] COMMAND [ARGS]...
```

### version-prompt

Controls whether AlgoKit checks and prompts for new versions.
Set to [disable] to prevent AlgoKit performing this check permanently, or [enable] to resume checking.
If no argument is provided then outputs current setting.

Also see –skip-version-check which can be used to disable check for a single command.

```shell
algokit config version-prompt [OPTIONS] [[enable|disable]]
```

### Arguments


### ENABLE
Optional argument

## doctor

Run the Algorand doctor CLI.

```shell
algokit doctor [OPTIONS]
```

### Options


### -c, --copy-to-clipboard
Copy the contents of the doctor message (in Markdown format) in your clipboard.

## explore

Explore the specified network in the browser using Dappflow.

```shell
algokit explore [OPTIONS] [[localnet|testnet|mainnet]]
```

### Arguments


### NETWORK
Optional argument

## goal

Run the Algorand goal CLI against the AlgoKit LocalNet.

```shell
algokit goal [OPTIONS] [GOAL_ARGS]...
```

### Options


### --console
Open a Bash console so you can execute multiple goal commands and/or interact with a filesystem.

### Arguments


### GOAL_ARGS
Optional argument(s)

## init

Initializes a new project from a template.

```shell
algokit init [OPTIONS]
```

### Options


### -n, --name <directory_name>
Name of the project / directory / repository to create.


### -t, --template <template_name>
Name of an official template to use.


### --template-url <URL>
URL to a git repo with a custom project template.


### --template-url-ref <URL>
Specific tag, branch or commit to use on git repo specified with –template-url. Defaults to latest.


### --UNSAFE-SECURITY-accept-template-url
Accept the specified template URL, acknowledging the security implications of arbitrary code execution trusting an unofficial template.


### --git, --no-git
Initialise git repository in directory after creation.


### --defaults
Automatically choose default answers without asking when creating this template.


### --bootstrap, --no-bootstrap
Whether to run algokit bootstrap to bootstrap the new project’s dependencies.


### -a, --answer <key> <value>
Answers key/value pairs to pass to the template.

## localnet

Manage the AlgoKit LocalNet.

```shell
algokit localnet [OPTIONS] COMMAND [ARGS]...
```

### console

Run the Algorand goal CLI against the AlgoKit LocalNet via a Bash console so you can execute multiple goal commands and/or interact with a filesystem.

```shell
algokit localnet console [OPTIONS]
```

### explore

Explore the AlgoKit LocalNet using Dappflow

```shell
algokit localnet explore [OPTIONS]
```

### reset

Reset the AlgoKit LocalNet.

```shell
algokit localnet reset [OPTIONS]
```

### Options


### --update, --no-update
Enable or disable updating to the latest available LocalNet version

### start

Start the AlgoKit LocalNet.

```shell
algokit localnet start [OPTIONS]
```

### status

Check the status of the AlgoKit LocalNet.

```shell
algokit localnet status [OPTIONS]
```

### stop

Stop the AlgoKit LocalNet.

```shell
algokit localnet stop [OPTIONS]
```
