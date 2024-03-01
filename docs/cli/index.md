# AlgoKit CLI Reference Documentation


- [algokit](#algokit)
    - [Options](#options)
    - [--version](#--version)
    - [-v, --verbose](#-v---verbose)
    - [--color, --no-color](#--color---no-color)
    - [--skip-version-check](#--skip-version-check)
  - [bootstrap](#bootstrap)
    - [Options](#options-1)
    - [--force](#--force)
    - [all](#all)
    - [Options](#options-2)
    - [--interactive, --non-interactive, --ci](#--interactive---non-interactive---ci)
    - [env](#env)
    - [Options](#options-3)
    - [--interactive, --non-interactive, --ci](#--interactive---non-interactive---ci-1)
    - [npm](#npm)
    - [poetry](#poetry)
  - [completions](#completions)
    - [install](#install)
    - [Options](#options-4)
    - [--shell ](#--shell-)
    - [uninstall](#uninstall)
    - [Options](#options-5)
    - [--shell ](#--shell--1)
  - [config](#config)
    - [version-prompt](#version-prompt)
    - [Arguments](#arguments)
    - [ENABLE](#enable)
  - [deploy](#deploy)
    - [Options](#options-6)
    - [-C, --command ](#-c---command-)
    - [--interactive, --non-interactive, --ci](#--interactive---non-interactive---ci-2)
    - [-P, --path ](#-p---path-)
    - [--deployer ](#--deployer-)
    - [--dispenser ](#--dispenser-)
    - [Arguments](#arguments-1)
    - [ENVIRONMENT_NAME](#environment_name)
  - [dispenser](#dispenser)
    - [fund](#fund)
    - [Options](#options-7)
    - [-r, --receiver ](#-r---receiver-)
    - [-a, --amount ](#-a---amount-)
    - [--whole-units](#--whole-units)
    - [limit](#limit)
    - [Options](#options-8)
    - [--whole-units](#--whole-units-1)
    - [login](#login)
    - [Options](#options-9)
    - [--ci](#--ci)
    - [-o, --output ](#-o---output-)
    - [-f, --file ](#-f---file-)
    - [logout](#logout)
    - [refund](#refund)
    - [Options](#options-10)
    - [-t, --txID ](#-t---txid-)
  - [doctor](#doctor)
    - [Options](#options-11)
    - [-c, --copy-to-clipboard](#-c---copy-to-clipboard)
  - [explore](#explore)
    - [Arguments](#arguments-2)
    - [NETWORK](#network)
  - [generate](#generate)
    - [client](#client)
    - [Options](#options-12)
    - [-o, --output ](#-o---output--1)
    - [-l, --language ](#-l---language-)
    - [Arguments](#arguments-3)
    - [APP_SPEC_PATH_OR_DIR](#app_spec_path_or_dir)
  - [goal](#goal)
    - [Options](#options-13)
    - [--console](#--console)
    - [Arguments](#arguments-4)
    - [GOAL_ARGS](#goal_args)
  - [init](#init)
    - [Options](#options-14)
    - [-n, --name ](#-n---name-)
    - [-t, --template ](#-t---template-)
    - [--template-url ](#--template-url-)
    - [--template-url-ref ](#--template-url-ref-)
    - [--UNSAFE-SECURITY-accept-template-url](#--unsafe-security-accept-template-url)
    - [--git, --no-git](#--git---no-git)
    - [--defaults](#--defaults)
    - [--bootstrap, --no-bootstrap](#--bootstrap---no-bootstrap)
    - [--ide, --no-ide](#--ide---no-ide)
    - [--workspace, --no-workspace](#--workspace---no-workspace)
    - [-a, --answer  ](#-a---answer--)
  - [localnet](#localnet)
    - [console](#console)
    - [explore](#explore-1)
    - [logs](#logs)
    - [Options](#options-15)
    - [--follow, -f](#--follow--f)
    - [--tail ](#--tail-)
    - [reset](#reset)
    - [Options](#options-16)
    - [--update, --no-update](#--update---no-update)
    - [start](#start)
    - [Options](#options-17)
    - [-n, --name ](#-n---name--1)
    - [status](#status)
    - [stop](#stop)
  - [task](#task)
    - [analyze](#analyze)
    - [Options](#options-18)
    - [-r, --recursive](#-r---recursive)
    - [--force](#--force-1)
    - [--diff](#--diff)
    - [-o, --output ](#-o---output--2)
    - [-e, --exclude ](#-e---exclude-)
    - [Arguments](#arguments-5)
    - [INPUT_PATHS](#input_paths)
    - [ipfs](#ipfs)
    - [Options](#options-19)
    - [-f, --file ](#-f---file--1)
    - [-n, --name ](#-n---name--2)
    - [mint](#mint)
    - [Options](#options-20)
    - [--creator ](#--creator-)
    - [-n, --name ](#-n---name--3)
    - [-u, --unit ](#-u---unit-)
    - [-t, --total ](#-t---total-)
    - [-d, --decimals ](#-d---decimals-)
    - [-i, --image ](#-i---image-)
    - [-m, --metadata ](#-m---metadata-)
    - [--mutable, --immutable](#--mutable---immutable)
    - [--nft, --ft](#--nft---ft)
    - [-n, --network ](#-n---network-)
    - [nfd-lookup](#nfd-lookup)
    - [Options](#options-21)
    - [-o, --output ](#-o---output--3)
    - [Arguments](#arguments-6)
    - [VALUE](#value)
    - [opt-in](#opt-in)
    - [Options](#options-22)
    - [-a, --account ](#-a---account-)
    - [-n, --network ](#-n---network--1)
    - [Arguments](#arguments-7)
    - [ASSET_IDS](#asset_ids)
    - [opt-out](#opt-out)
    - [Options](#options-23)
    - [-a, --account ](#-a---account--1)
    - [--all](#--all)
    - [-n, --network ](#-n---network--2)
    - [Arguments](#arguments-8)
    - [ASSET_IDS](#asset_ids-1)
    - [send](#send)
    - [Options](#options-24)
    - [-f, --file ](#-f---file--2)
    - [-t, --transaction ](#-t---transaction-)
    - [-n, --network ](#-n---network--3)
    - [sign](#sign)
    - [Options](#options-25)
    - [-a, --account ](#-a---account--2)
    - [-f, --file ](#-f---file--3)
    - [-t, --transaction ](#-t---transaction--1)
    - [-o, --output ](#-o---output--4)
    - [--force](#--force-2)
    - [transfer](#transfer)
    - [Options](#options-26)
    - [-s, --sender ](#-s---sender-)
    - [-r, --receiver ](#-r---receiver--1)
    - [--asset, --id ](#--asset---id-)
    - [-a, --amount ](#-a---amount--1)
    - [--whole-units](#--whole-units-2)
    - [-n, --network ](#-n---network--4)
    - [vanity-address](#vanity-address)
    - [Options](#options-27)
    - [-m, --match ](#-m---match-)
    - [-o, --output ](#-o---output--5)
    - [-a, --alias ](#-a---alias-)
    - [--file-path ](#--file-path-)
    - [-f, --force](#-f---force)
    - [Arguments](#arguments-9)
    - [KEYWORD](#keyword)
    - [wallet](#wallet)
    - [Options](#options-28)
    - [-a, --address ](#-a---address-)
    - [-m, --mnemonic](#-m---mnemonic)
    - [-f, --force](#-f---force-1)
    - [Arguments](#arguments-10)
    - [ALIAS_NAME](#alias_name)
    - [Arguments](#arguments-11)
    - [ALIAS](#alias)
    - [Options](#options-29)
    - [-f, --force](#-f---force-2)
    - [Arguments](#arguments-12)
    - [ALIAS](#alias-1)
    - [Options](#options-30)
    - [-f, --force](#-f---force-3)

# algokit

AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.

If you are getting started, please see the quick start tutorial: [https://bit.ly/algokit-intro-tutorial](https://bit.ly/algokit-intro-tutorial).

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

Expedited initial setup for any developer by installing and configuring dependencies and other
key development environment setup activities.

```shell
algokit bootstrap [OPTIONS] COMMAND [ARGS]...
```

### Options


### --force
Continue even if minimum AlgoKit version is not met

### all

Runs all bootstrap sub-commands in the current directory and immediate sub directories.

```shell
algokit bootstrap all [OPTIONS]
```

### Options


### --interactive, --non-interactive, --ci
Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive

### env

Copies .env.template file to .env in the current working directory and prompts for any unspecified values.

```shell
algokit bootstrap env [OPTIONS]
```

### Options


### --interactive, --non-interactive, --ci
Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive

### npm

Runs npm install in the current working directory to install Node.js dependencies.

```shell
algokit bootstrap npm [OPTIONS]
```

### poetry

Installs Python Poetry (if not present) and runs poetry install in the current working directory to install Python dependencies.

```shell
algokit bootstrap poetry [OPTIONS]
```

## completions

Install and Uninstall AlgoKit shell integrations.

```shell
algokit completions [OPTIONS] COMMAND [ARGS]...
```

### install

Install shell completions, this command will attempt to update the interactive profile script
for the current shell to support algokit completions. To specify a specific shell use --shell.

```shell
algokit completions install [OPTIONS]
```

### Options


### --shell <shell>
Specify shell to install algokit completions for.


* **Options**

    bash | zsh


### uninstall

Uninstall shell completions, this command will attempt to update the interactive profile script
for the current shell to remove any algokit completions that have been added.
To specify a specific shell use --shell.

```shell
algokit completions uninstall [OPTIONS]
```

### Options


### --shell <shell>
Specify shell to install algokit completions for.


* **Options**

    bash | zsh


## config

Configure settings used by AlgoKit

```shell
algokit config [OPTIONS] COMMAND [ARGS]...
```

### version-prompt

Controls whether AlgoKit checks and prompts for new versions.
Set to [disable] to prevent AlgoKit performing this check permanently, or [enable] to resume checking.
If no argument is provided then outputs current setting.

Also see --skip-version-check which can be used to disable check for a single command.

```shell
algokit config version-prompt [OPTIONS] [[enable|disable]]
```

### Arguments


### ENABLE
Optional argument

## deploy

Deploy smart contracts from AlgoKit compliant repository.

```shell
algokit deploy [OPTIONS] [ENVIRONMENT_NAME]
```

### Options


### -C, --command <command>
Custom deploy command. If not provided, will load the deploy command from .algokit.toml file.


### --interactive, --non-interactive, --ci
Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive


### -P, --path <path>
Specify the project directory. If not provided, current working directory will be used.


### --deployer <deployer_alias>
(Optional) Alias of the deployer account. Otherwise, will prompt the deployer mnemonic if specified in .algokit.toml file.


### --dispenser <dispenser_alias>
(Optional) Alias of the dispenser account. Otherwise, will prompt the dispenser mnemonic if specified in .algokit.toml file.

### Arguments


### ENVIRONMENT_NAME
Optional argument

## dispenser

Interact with the AlgoKit TestNet Dispenser.

```shell
algokit dispenser [OPTIONS] COMMAND [ARGS]...
```

### fund

Fund your wallet address with TestNet ALGOs.

```shell
algokit dispenser fund [OPTIONS]
```

### Options


### -r, --receiver <receiver>
**Required** Address or alias of the receiver to fund with TestNet ALGOs.


### -a, --amount <amount>
**Required** Amount to fund. Defaults to microAlgos.


### --whole-units
Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.

### limit

Get information about current fund limit on your account. Resets daily.

```shell
algokit dispenser limit [OPTIONS]
```

### Options


### --whole-units
Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.

### login

Login to your Dispenser API account.

```shell
algokit dispenser login [OPTIONS]
```

### Options


### --ci
Generate an access token for CI. Issued for 30 days.


### -o, --output <output_mode>
Choose the output method for the access token. Defaults to stdout. Only applicable when --ci flag is set.


* **Options**

    stdout | file



### -f, --file <output_filename>
Output filename where you want to store the generated access token.Defaults to algokit_ci_token.txt. Only applicable when --ci flag is set and --output mode is file.

### logout

Logout of your Dispenser API account.

```shell
algokit dispenser logout [OPTIONS]
```

### refund

Refund ALGOs back to the dispenser wallet address.

```shell
algokit dispenser refund [OPTIONS]
```

### Options


### -t, --txID <tx_id>
**Required** Transaction ID of your refund operation.

## doctor

Diagnose potential environment issues that may affect AlgoKit.

Will search the system for AlgoKit dependencies and show their versions, as well as identifying any
potential issues.

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

## generate

Generate code for an Algorand project.

```shell
algokit generate [OPTIONS] COMMAND [ARGS]...
```

### client

Create a typed ApplicationClient from an ARC-32 application.json

Supply the path to an application specification file or a directory to recursively search
for "application.json" files

```shell
algokit generate client [OPTIONS] APP_SPEC_PATH_OR_DIR
```

### Options


### -o, --output <output_path_pattern>
Path to the output file. The following tokens can be used to substitute into the output path: {contract_name}, {app_spec_dir}


### -l, --language <language>
Programming language of the generated client code


* **Options**

    python | typescript


### Arguments


### APP_SPEC_PATH_OR_DIR
Required argument

## goal

Run the Algorand goal CLI against the AlgoKit LocalNet.

Look at [https://developer.algorand.org/docs/clis/goal/goal/](https://developer.algorand.org/docs/clis/goal/goal/) for more information.

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

Initializes a new project from a template, including prompting
for template specific questions to be used in template rendering.

Templates can be default templates shipped with AlgoKit, or custom
templates in public Git repositories.

Includes ability to initialise Git repository, run algokit bootstrap and
automatically open Visual Studio Code.

This should be run in the parent directory that you want the project folder
created in.

By default, the --workspace flag creates projects within a workspace structure or integrates them into an existing
one, promoting organized management of multiple projects. Alternatively,
to disable this behavior use the --no-workspace flag, which ensures
the new project is created in a standalone target directory. This is
suitable for isolated projects or when workspace integration is unnecessary.

```shell
algokit init [OPTIONS]
```

### Options


### -n, --name <directory_name>
Name of the project / directory / repository to create.


### -t, --template <template_name>
Name of an official template to use. To choose interactively, run this command with no arguments.


* **Options**

    tealscript | puya | react | fullstack | beaker | base | playground



### --template-url <URL>
URL to a git repo with a custom project template.


### --template-url-ref <URL>
Specific tag, branch or commit to use on git repo specified with --template-url. Defaults to latest.


### --UNSAFE-SECURITY-accept-template-url
Accept the specified template URL, acknowledging the security implications of arbitrary code execution trusting an unofficial template.


### --git, --no-git
Initialise git repository in directory after creation.


### --defaults
Automatically choose default answers without asking when creating this template.


### --bootstrap, --no-bootstrap
Whether to run algokit bootstrap to install and configure the new project's dependencies locally.


### --ide, --no-ide
Whether to open an IDE for you if the IDE and IDE config are detected. Supported IDEs: VS Code.


### --workspace, --no-workspace
Whether to prefer structuring standalone projects as part of a workspace.


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

### logs

See the output of the Docker containers

```shell
algokit localnet logs [OPTIONS]
```

### Options


### --follow, -f
Follow log output.


### --tail <tail>
Number of lines to show from the end of the logs for each container.


* **Default**

    `all`


### reset

Reset the AlgoKit LocalNet.

```shell
algokit localnet reset [OPTIONS]
```

### Options


### --update, --no-update
Enable or disable updating to the latest available LocalNet version, default: don't update

### start

Start the AlgoKit LocalNet.

```shell
algokit localnet start [OPTIONS]
```

### Options


### -n, --name <name>
Specify a name for a custom LocalNet instance. AlgoKit will not manage the configuration of named LocalNet instances, allowing developers to configure it in any way they need.

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

## task

Collection of useful tasks to help you develop on Algorand.

```shell
algokit task [OPTIONS] COMMAND [ARGS]...
```

### analyze

Analyze TEAL programs for common vulnerabilities using Tealer. This task uses a third party tool to suggest improvements for your TEAL programs, but remember to always test your smart contracts code, follow modern software engineering practices and use the guidelines for smart contract development. This should not be used as a substitute for an actual audit. For full list of available detectors, please refer to [https://github.com/crytic/tealer?tab=readme-ov-file#detectors](https://github.com/crytic/tealer?tab=readme-ov-file#detectors)

```shell
algokit task analyze [OPTIONS] INPUT_PATHS...
```

### Options


### -r, --recursive
Recursively search for all TEAL files within the provided directory.


### --force
Force verification without the disclaimer confirmation prompt.


### --diff
Exit with a non-zero code if differences are found between current and last reports. Reports are generated each run, but with this flag execution fails if the current report doesn't match the last report. Reports are stored in the .algokit/static-analysis/snapshots folder by default. Use --output for a custom path.


### -o, --output <output_path>
Directory path where to store the results of the static analysis. Defaults to .algokit/static-analysis/snapshots.


### -e, --exclude <detectors_to_exclude>
Exclude specific vulnerabilities from the analysis. Supports multiple exclusions in a single run.

### Arguments


### INPUT_PATHS
Required argument(s)

### ipfs

Upload files to IPFS using Pinata provider.

```shell
algokit task ipfs [OPTIONS] COMMAND [ARGS]...
```

#### login

Login to Pinata ipfs provider. You will be prompted for your JWT.

```shell
algokit task ipfs login [OPTIONS]
```

#### logout

Logout of Pinata ipfs provider.

```shell
algokit task ipfs logout [OPTIONS]
```

#### upload

Upload a file to Pinata ipfs provider. Please note, max file size is 100MB.

```shell
algokit task ipfs upload [OPTIONS]
```

### Options


### -f, --file <file_path>
**Required** Path to the file to upload.


### -n, --name <name>
Human readable name for this upload, for use in file listings.

### mint

Mint new fungible or non-fungible assets on Algorand.

```shell
algokit task mint [OPTIONS]
```

### Options


### --creator <creator>
**Required** Address or alias of the asset creator.


### -n, --name <asset_name>
**Required** Asset name.


### -u, --unit <unit_name>
**Required** Unit name of the asset.


### -t, --total <total>
Total supply of the asset. Defaults to 1.


### -d, --decimals <decimals>
Number of decimals. Defaults to 0.


### -i, --image <image_path>
**Required** Path to the asset image file to be uploaded to IPFS.


### -m, --metadata <token_metadata_path>
Path to the ARC19 compliant asset metadata file to be uploaded to IPFS. If not provided,
a default metadata object will be generated automatically based on asset-name, decimals and image.
For more details refer to [https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema](https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema).


### --mutable, --immutable
Whether the asset should be mutable or immutable. Refers to ARC19 by default.


### --nft, --ft
Whether the asset should be validated as NFT or FT. Refers to NFT by default and validates canonical
definitions of pure or fractional NFTs as per ARC3 standard.


### -n, --network <network>
Network to use. Refers to localnet by default.


* **Options**

    localnet | testnet | mainnet


### nfd-lookup

Perform a lookup via NFD domain or address, returning the associated address or domain respectively.

```shell
algokit task nfd-lookup [OPTIONS] VALUE
```

### Options


### -o, --output <output>
Output format for NFD API response. Defaults to address|domain resolved.


* **Options**

    full | tiny | address


### Arguments


### VALUE
Required argument

### opt-in

Opt-in to an asset(s). This is required before you can receive an asset. Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.

```shell
algokit task opt-in [OPTIONS] ASSET_IDS...
```

### Options


### -a, --account <account>
**Required** Address or alias of the signer account.


### -n, --network <network>
Network to use. Refers to localnet by default.


* **Options**

    localnet | testnet | mainnet


### Arguments


### ASSET_IDS
Required argument(s)

### opt-out

opt-out of an asset(s). You can only opt out of an asset with a zero balance. Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.

```shell
algokit task opt-out [OPTIONS] [ASSET_IDS]...
```

### Options


### -a, --account <account>
**Required** Address or alias of the signer account.


### --all
Opt-out of all assets with zero balance.


### -n, --network <network>
Network to use. Refers to localnet by default.


* **Options**

    localnet | testnet | mainnet


### Arguments


### ASSET_IDS
Optional argument(s)

### send

Send a signed transaction to the given network.

```shell
algokit task send [OPTIONS]
```

### Options


### -f, --file <file>
Single or multiple message pack encoded signed transactions from binary file to send. Option is mutually exclusive with transaction.


### -t, --transaction <transaction>
Base64 encoded signed transaction to send. Option is mutually exclusive with file.


### -n, --network <network>
Network to use. Refers to localnet by default.


* **Options**

    localnet | testnet | mainnet


### sign

Sign goal clerk compatible Algorand transaction(s).

```shell
algokit task sign [OPTIONS]
```

### Options


### -a, --account <account>
**Required** Address or alias of the signer account.


### -f, --file <file>
Single or multiple message pack encoded transactions from binary file to sign. Option is mutually exclusive with transaction.


### -t, --transaction <transaction>
Single base64 encoded transaction object to sign. Option is mutually exclusive with file.


### -o, --output <output>
The output file path to store signed transaction(s).


### --force
Force signing without confirmation.

### transfer

Transfer algos or assets from one account to another.

```shell
algokit task transfer [OPTIONS]
```

### Options


### -s, --sender <sender>
**Required** Address or alias of the sender account.


### -r, --receiver <receiver>
**Required** Address or alias to an account that will receive the asset(s).


### --asset, --id <asset_id>
Asset ID to transfer. Defaults to 0 (Algo).


### -a, --amount <amount>
**Required** Amount to transfer.


### --whole-units
Use whole units (Algos | ASAs) instead of smallest divisible units (for example, microAlgos). Disabled by default.


### -n, --network <network>
Network to use. Refers to localnet by default.


* **Options**

    localnet | testnet | mainnet


### vanity-address

Generate a vanity Algorand address. Your KEYWORD can only include letters A - Z and numbers 2 - 7.
Keeping your KEYWORD under 5 characters will usually result in faster generation.
Note: The longer the KEYWORD, the longer it may take to generate a matching address.
Please be patient if you choose a long keyword.

```shell
algokit task vanity-address [OPTIONS] KEYWORD
```

### Options


### -m, --match <match>
Location where the keyword will be included. Default is start.


* **Options**

    start | anywhere | end



### -o, --output <output>
How the output will be presented.


* **Options**

    stdout | alias | file



### -a, --alias <alias>
Alias for the address. Required if output is "alias".


### --file-path <output_file_path>
File path where to dump the output. Required if output is "file".


### -f, --force
Allow overwriting an aliases without confirmation, if output option is 'alias'.

### Arguments


### KEYWORD
Required argument

### wallet

Create short aliases for your addresses and accounts on AlgoKit CLI.

```shell
algokit task wallet [OPTIONS] COMMAND [ARGS]...
```

#### add

Add an address or account to be stored against a named alias (at most 50 aliases).

```shell
algokit task wallet add [OPTIONS] ALIAS_NAME
```

### Options


### -a, --address <address>
**Required** The address of the account.


### -m, --mnemonic
If specified then prompt the user for a mnemonic phrase interactively using masked input.


### -f, --force
Allow overwriting an existing alias.

### Arguments


### ALIAS_NAME
Required argument

#### get

Get an address or account stored against a named alias.

```shell
algokit task wallet get [OPTIONS] ALIAS
```

### Arguments


### ALIAS
Required argument

#### list

List all addresses and accounts stored against a named alias.

```shell
algokit task wallet list [OPTIONS]
```

#### remove

Remove an address or account stored against a named alias.

```shell
algokit task wallet remove [OPTIONS] ALIAS
```

### Options


### -f, --force
Allow removing an alias without confirmation.

### Arguments


### ALIAS
Required argument

#### reset

Remove all aliases.

```shell
algokit task wallet reset [OPTIONS]
```

### Options


### -f, --force
Allow removing all aliases without confirmation.
