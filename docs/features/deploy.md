# AlgoKit Deploy Feature Documentation

Deploy your smart contracts effortlessly to various networks with the AlgoKit Deploy feature. This feature is essential for automation in CI/CD pipelines and for seamless deployment to mainnet or testnet networks.

## Usage

```sh
$ algokit deploy [OPTIONS] NETWORK
```

This command deploys smart contracts from an AlgoKit compliant repository to the specified network.

### Options

- `--custom-deploy-command TEXT`: Specifies a custom deploy command. If this option is not provided, the deploy command will be loaded from the `.algokit.toml` file.
- `--ci`: Skips the interactive prompt for mnemonics. When using this option, mnemonics must be set as environment variables.
- `--prod`: Skips the warning prompt for deployments to a mainnet.
- `-h, --help`: Show this message and exit.

## Functionality

AlgoKit requires certain configuration files at the root of your project to successfully perform deployment. Below is the directory layout expected by AlgoKit:

```md
.
├── ... (your project files and directories)
├── .algokit.toml # Configuration file for AlgoKit
└── .env.[{mainnet|testnet|localnet|betanet|custom}] # (OPTIONAL) Environment variables specific to deployments to a network
```

### AlgoKit Configuration File

AlgoKit allows you to define your deployment logic by adding an `.algokit.toml`, a file present at the root of your project instantiated with `algokit init`. This file should include deployment commands for the network(s) you wish to target. The syntax is as follows:

```toml
[deploy.{network_name}]
command = "deployment-command-for-{network_name}"
```

#### Example

For instance, if you're aiming to deploy to a testnet, your `.algokit.toml` file should contain:

```toml
[deploy.testnet]
command = "poetry run python -m smart_contracts deploy"
```

### Environment Files

For each network you're deploying to, you need to have a corresponding `.env.[network_name]` file. This file should contain environment variables specific to that network.

**Note**: Creating `.env.[network_name]` files is only necessary if you're deploying to a custom network or if you want to override the default network configurations provided by AlgoKit. AlgoKit comes with predefined configurations for popular networks like `TestNet`, `MainNet`, `BetaNet`, or AlgoKit's `LocalNet`.

You can examine the exact default configurations in the [constants](../../src/algokit/core/constants.py) file or visit [AlgoNode](https://algonode.io/) for more details on network configurations that AlgoKit relies on by default.

### Deploying to a Specific Network

The command requires a `NETWORK` argument, which specifies the network to which the smart contracts will be deployed. Supported networks include `localnet`, `testnet`, `betanet`, `mainnet` or **any** custom named network you prefer to deploy your contract to. The network argument is not case-sensitive.

Example:

```sh
$ algokit deploy testnet
```

This command deploys the smart contracts to the testnet.

### Custom Deploy Command

You can provide a custom deploy command using the `--custom-deploy-command` option. If this option is not provided, the deploy command will be loaded from the `.algokit.toml` file.

Example:

```sh
$ algokit deploy testnet --custom-deploy-command="your-custom-command"
```

### CI Mode

By using the `--ci` flag, you can skip the interactive prompt for mnemonics.

This is useful in CI/CD environments where user interaction is not possible. When using this flag, you need to make sure that the mnemonics are set as environment variables.

Example:

```sh
$ algokit deploy testnet --ci
```

### Production Deployment

When deploying to the mainnet, a warning prompt is displayed by default. You can skip this warning by using the `--prod` flag.

Example:

```sh
$ algokit deploy mainnet --prod
```

This will deploy the smart contracts to the mainnet without showing the warning prompt.

### Mnemonics

When not in CI mode, the deploy command will prompt for mnemonics. If deploying to a non-localnet, the deployer mnemonic is required. Optionally, you can use a dispenser account by confirming when prompted.

## Example of a Full Deployment

```sh
$ algokit deploy mainnet --custom-deploy-command="your-custom-command" --prod
```

This example shows how to deploy smart contracts to the mainnet using a custom deploy command and skipping the warning prompt.

## Further Reading

For in-depth details, visit the [deploy](../cli/index.md#deploy) section in the AlgoKit CLI reference documentation.
