# AlgoKit Project Deploy

Deploy your smart contracts effortlessly to various networks with the algokit project deploy feature. This feature is essential for automation in CI/CD pipelines and for seamless deployment to various Algorand network environments.

> **Note**: Invoking deploy from `algokit deploy` is not recommended. Please prefer using `algokit project deploy` instead.

## Usage

```sh
$ algokit project deploy [OPTIONS] [ENVIRONMENT_NAME] [EXTRA_ARGS]
```

This command deploys smart contracts from an AlgoKit compliant repository to the specified network.

### Options

- `--command, -C TEXT`: Specifies a custom deploy command. If this option is not provided, the deploy command will be loaded from the `.algokit.toml` file.
- `--interactive / --non-interactive, --ci`: Enables or disables the interactive prompt for mnemonics. When the CI environment variable is set, it defaults to non-interactive.
- `--path, -P DIRECTORY`: Specifies the project directory. If not provided, the current working directory will be used.
- `--deployer`: Specifies the deployer alias. If not provided and if the deployer is specified in `.algokit.toml` file its mnemonic will be prompted.
- `--dispenser`: Specifies the dispenser alias. If not provided and if the dispenser is specified in `.algokit.toml` file its mnemonic will be prompted.
- `-p, --project-name`: (Optional) Projects to execute the command on. Defaults to all projects found in
  the current directory. Option is mutually exclusive with `--command`.
- `-h, --help`: Show this message and exit.
- `[EXTRA_ARGS]...`: Additional arguments to pass to the deploy command. For instance, `algokit project deploy -- {custom args}`. This will ensure that the extra arguments are passed to the deploy command specified in the `.algokit.toml` file or directly via `--command` option.

## Environment files

AlgoKit `deploy` employs both a general and network-specific environment file strategy. This allows you to set environment variables that are applicable across all networks and others that are specific to a given network.

The general environment file (`.env`) should be placed at the root of your project. This file will be used to load environment variables that are common across deployments to all networks.

For each network you're deploying to, you can optionally have a corresponding `.env.[network_name]` file. This file should contain environment variables specific to that network. Network-specific environment variables take precedence over general environment variables.

The directory layout would look like this:

```md
.
├── ... (your project files and directories)
├── .algokit.toml # Configuration file for AlgoKit
├── .env # (OPTIONAL) General environment variables common across all deployments
└── .env.[{mainnet|testnet|localnet|betanet|custom}] # (OPTIONAL) Environment variables specific to deployments to a network
```

> ⚠️ Please note that creating `.env` and `.env.[network_name]` files is only necessary if you're deploying to a custom network or if you want to override the default network configurations provided by AlgoKit. AlgoKit comes with predefined configurations for popular networks like `TestNet`, `MainNet`, `BetaNet`, or AlgoKit's `LocalNet`.

The logic for loading environment variables is as follows:

- If a `.env` file exists, the environment variables contained in it are loaded first.
- If a `.env.[network_name]` file exists, the environment variables in it are loaded, overriding any previously loaded values from the `.env` file for the same variables.

### Default Network Configurations

The `deploy` command assumes default configurations for `mainnet`, `localnet`, and `testnet` environments. If you're deploying to one of these networks and haven't provided specific environment variables, AlgoKit will use these default values:

- **Localnet**:

  - `ALGOD_TOKEN`: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  - `ALGOD_SERVER`: "http://localhost"
  - `ALGOD_PORT`: "4001"
  - `INDEXER_TOKEN`: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  - `INDEXER_SERVER`: "http://localhost"
  - `INDEXER_PORT`: "8980"

- **Mainnet**:

  - `ALGOD_SERVER`: "https://mainnet-api.algonode.cloud"
  - `INDEXER_SERVER`: "https://mainnet-idx.algonode.cloud"

- **Testnet**:
  - `ALGOD_SERVER`: "https://testnet-api.algonode.cloud"
  - `INDEXER_SERVER`: "https://testnet-idx.algonode.cloud"

These default values are used when no specific `.env.[network_name]` file is present and the corresponding environment variables are not set. This feature simplifies the deployment process for these common networks, reducing the need for manual configuration in many cases.

If you need to override these defaults or add additional configuration for these networks, you can still do so by creating the appropriate `.env.[network_name]` file or setting the environment variables explicitly or via generic `.env` file.

## AlgoKit Configuration File

AlgoKit uses a configuration file called `.algokit.toml` in the root of your project. The configuration file can be created using the `algokit init` command. This file will define the deployment commands for the various network environments that you want to target.

Here's an example of what the `.algokit.toml` file might look like. When deploying it will prompt for the `DEPLOYER_MNEMONIC` secret unless it is already defined as an environment variable or is deploying to localnet.

```toml
[algokit]
min_version = "v{lastest_version}"

[project]

... # project configuration and custom commands

[project.deploy]
command = "poetry run python -m smart_contracts deploy"
environment_secrets = [
  "DEPLOYER_MNEMONIC",
]

[project.deploy.localnet]
environment_secrets = []
```

The `command` key under each `[project.deploy.{network_name}]` section should contain a string that represents the deployment command for that particular network. If a `command` key is not provided in a network-specific section, the command from the general `[project.deploy]` section will be used.

The `environment_secrets` key should contain a list of names of environment variables that should be treated as secrets. This can be defined in the general `[project.deploy]` section, as well as in the network-specific sections. The environment-specific secrets will be added to the general secrets during deployment.

The `[algokit]` section with the `min_version` key allows you to specify the minimum version of AlgoKit that the project requires.

This way, you can define common deployment logic and environment secrets in the `[project.deploy]` section, and provide overrides or additions for specific environments in the `[project.deploy.{environment_name}]` sections.

## Deploying to a Specific Network

The command requires a `ENVIRONMENT` argument, which specifies the network environment to which the smart contracts will be deployed. Please note, the `environment` argument is case-sensitive.

Example:

```sh
$ algokit project deploy testnet
```

This command deploys the smart contracts to the testnet.

## Deploying to a Specific Network from a workspace with project name filter

The command requires a `ENVIRONMENT` argument, which specifies the network environment to which the smart contracts will be deployed. Please note, the `environment` argument is case-sensitive.

Example:

Root `.algokit.toml`:

```toml
[project]
type = "workspace"
projects_root_dir = 'projects'
```

Contract project `.algokit.toml`:

```toml
[project]
type = "contract"
name = "myproject"

[project.deploy]
command = "{custom_deploy_command}"
```

```bash
$ algokit project deploy testnet --project-name myproject
```

This command deploys the smart contracts to TestNet from a sub project named 'myproject', which is available within the current workspace. All `.env` loading logic described in [Environment files](#environment-files) is applicable, execution from the workspace root orchestrates invoking the deploy command from the working directory of each applicable sub project.

## Custom Project Directory

By default, the deploy command looks for the `.algokit.toml` file in the current working directory. You can specify a custom project directory using the `--project-dir` option.

Example:

```sh
$ algokit project deploy testnet --project-dir="path/to/project"
```

## Custom Deploy Command

You can provide a custom deploy command using the `--custom-deploy-command` option. If this option is not provided, the deploy command will be loaded from the `.algokit.toml` file.

Example:

```sh
$ algokit project deploy testnet --custom-deploy-command="your-custom-command"
```

> ⚠️ Please note, chaining multiple commands with `&&` is **not** currently supported. If you need to run multiple commands, you can defer to a custom script. Refer to [run](../project/run.md#custom-command-injection) for scenarios where multiple sub-command invocations are required.

## CI Mode

By using the `--ci` or `--non-interactive` flag, you can skip the interactive prompt for mnemonics.

This is useful in CI/CD environments where user interaction is not possible. When using this flag, you need to make sure that the mnemonics are set as environment variables.

Example:

```sh
$ algokit project deploy testnet --ci
```

## Passing Extra Arguments

You can pass additional arguments to the deploy command. These extra arguments will be appended to the end of the deploy command specified in your `.algokit.toml` file or to the command specified directly via `--command` option.

To pass extra arguments, use `--` after the AlgoKit command and options to mark the distinction between arguments used by the CLI and arguments to be passed as extras to the deploy command/script.

Example:

```sh
$ algokit project deploy testnet -- my_contract_name --some_contract_related_param
```

In this example, `my_contract_name` and `--some_contract_related_param` are extra arguments that can be utilized by the custom deploy command invocation, for instance, to filter the deployment to a specific contract or modify deployment behavior.

## Example of a Full Deployment

```sh
$ algokit project deploy testnet --custom-deploy-command="your-custom-command"
```

This example shows how to deploy smart contracts to the testnet using a custom deploy command. This also assumes that .algokit.toml file is present in the current working directory, and .env.testnet file is present in the current working directory and contains the required environment variables for deploying to TestNet environment.

## Further Reading

For in-depth details, visit the [deploy](../../cli/index.md#deploy) section in the AlgoKit CLI reference documentation.
