# AlgoKit LocalNet

The AlgoKit LocalNet feature allows you to manage (start, stop, reset, manage) a locally sandboxed private Algorand network. This allows you to interact and deploy changes against your own Algorand network without needing to worry about funding TestNet accounts, information you submit being publicly visible or being connected to an active Internet connection (once the network has been started).

AlgoKit LocalNet uses Docker images that are optimised for a great dev experience. This means the Docker images are small and start fast. It also means that features suited to developers are enabled such as KMD (so you can programmatically get faucet private keys).

The philosophy we take with AlgoKit LocalNet is that you should treat it as an ephemeral network. This means assume it could be reset at any time - don't store data on there that you can't recover / recreate. We have optimised the AlgoKit LocalNet experience to minimise situations where the network will get reset to improve the experience, but it can and will still happen in a number of situations.

## Prerequisites

AlgoKit LocalNet relies on Docker and Docker Compose being present and running on your system.

You can install Docker by following the [official installation instructions](https://docs.docker.com/get-docker/). Most of the time this will also install Docker Compose, but if not you can [follow the instructions](https://docs.docker.com/compose/install/) for that too.

If you are on Windows then you will need WSL 2 installed first, for which you can find the [official installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install). If you are using Windows 10 then ensure you are on the latest version to reduce likelihood of installation problems.

Alternatively, the Windows 10/11 Pro+ supported [Hyper-V backend](https://docs.docker.com/desktop/install/windows-install/) for Docker can be used instead of the WSL 2 backend.

## Known issues

The AlgoKit LocalNet is built with 30,000 participation keys generated and after 30,000 rounds is reached it will no longer be able to add rounds. At this point you can simply reset the LocalNet to continue development. Participation keys are slow to generate hence why they are pre-generated to improve experience.

## Supported operating environments

We rely on the official Algorand docker images for Indexer, Conduit and Algod, which means that AlgoKit LocalNet is supported on Windows, Linux and Mac on Intel and AMD chipsets (including Apple Silicon).

## Functionality

### Creating / Starting the LocalNet

To create / start your AlgoKit LocalNet instance you can run `algokit localnet start`. This will:

- Detect if you have Docker and Docker Compose installed
- Detect if you have the Docker engine running
- Create a new Docker Compose deployment for AlgoKit LocalNet if it doesn't already exist
- (Re-)Start the containers

If it's the first time running it on your machine then it will download the following images from DockerHub:

- [`algorand/algod`](https://hub.docker.com/r/algorand/algod) (~500 MB)
- [`algorand/indexer`](https://hub.docker.com/r/algorand/indexer) (~96 MB)
- [`algorand/conduit`](https://hub.docker.com/r/algorand/conduit) (~98 MB)
- [`postgres:13-alpine`](https://hub.docker.com/_/postgres) (~80 MB)

Once they have downloaded, it won't try and re-download images unless you perform a `algokit localnet reset`.

Once the LocalNet has started, the following endpoints will be available:

- [algod](https://developer.algorand.org/docs/rest-apis/algod/v2/):
  - address: <http://localhost:4001>
  - token: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- [kmd](https://developer.algorand.org/docs/rest-apis/kmd/):
  - address: <http://localhost:4002>
  - token: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- [indexer](https://developer.algorand.org/docs/rest-apis/indexer/):
  - address: <http://localhost:8980>
- tealdbg port:
  - address: <http://localhost:9392>

### Creating / Starting a Named LocalNet

AlgoKit manages the default LocalNet environment and automatically keeps the configuration updated with any upstream changes. As a result, configuration changes are reset automatically by AlgoKit, so that developers always have access to a known good LocalNet configuration. This works well for the majority of scenarios, however sometimes developers need the control to make specific configuration changes for specific scenarios.

When you want more control, named LocalNet instances can be used by running `algokit localnet start --name {name}`. This command will set up and run a named LocalNet environment (based off the default), however AlgoKit will not update the environment or configuration automatically. From here developers are able to modify their named environment in any way they like, for example setting `DevMode: false` in `algod_network_template.json`.

Once you have a named LocalNet running, the AlgoKit LocalNet commands will target this instance.
If at any point you'd like to switch back to the default LocalNet, simply run `algokit localnet start`.

### Named LocalNet Configuration Directory

When running `algokit localnet start --name {name}`, AlgoKit stores configuration files in a specific directory on your system. The location of this directory depends on your operating system:

- **Windows**: We use the value of the `APPDATA` environment variable to determine the directory to store the configuration files. This is usually `C:\Users\USERNAME\AppData\Roaming`.
- **Linux or Mac**: We use the value of the `XDG_CONFIG_HOME` environment variable to determine the directory to store the configuration files. If `XDG_CONFIG_HOME` is not set, the default location is `~/.config`.

Assuming you have previously used a default LocalNet, the path `./algokit/sandbox/` will exist inside the configuration directory, containing the configuration settings for the default LocalNet instance. Additionally, for each named LocalNet instance you have created, the path `./algokit/sandbox_{name}/` will exist, containing the configuration settings for the respective named LocalNet instances.

It is important to note that only the configuration files for a named LocalNet instance should be changed. Any changes made to the default LocalNet instance will be reverted by AlgoKit.

### Stopping and Resetting the LocalNet

To stop the LocalNet you can execute `algokit localnet stop`. This will turn off the containers, but keep them ready to be started again in the same state by executing `algokit localnet start`.

To reset the LocalNet you can execute `algokit localnet reset`, which will tear down the existing containers, refresh the container definition from the latest stored within AlgoKit and update to the latest Docker images. If you want to keep the same container spec and versions as you currently have, but quickly tear down and start a new instance then run `algokit localnet reset --no-update`.

### Viewing transactions in the LocalNet

You can see a web-based user interface of the current state of your LocalNet including all transactions by using the [AlgoKit Explore](./explore.md) feature, e.g. by executing `algokit localnet explore`.

### Executing goal commands against AlgoKit LocalNet

See the [AlgoKit Goal](./goal.md) feature. You can also execute `algokit localnet console` to open a [Bash shell which allows you to run the goal commandline](./goal.md#running-multiple-commands).

Note: if you want to copy files into the container so you can access them via goal then you can use the following:

```
docker cp foo.txt algokit_algod:/root
```

### Getting access to the private key of the faucet account

If you want to use the LocalNet then you need to get the private key of the initial wallet so you can transfer ALGOs out of it to other accounts you create.

There are two ways to do this:

**Option 1: Manually via goal**

```
algokit goal account list
algokit goal account export -a {address_from_an_online_account_from_above_command_output}
```

**Option 2: Automatically via kmd API**

Needing to do this manual step every time you spin up a new development environment or reset your LocalNet is frustrating. Instead, it's useful to have code that uses the Sandbox APIs to automatically retrieve the private key of the default account.

AlgoKit Utils provides methods to help you do this:

- TypeScript - [`ensureFunded`](https://github.com/algorandfoundation/algokit-utils-ts/blob/main/docs/capabilities/transfer.md#ensurefunded) and [`getDispenserAccount`](https://github.com/algorandfoundation/algokit-utils-ts/blob/main/docs/capabilities/transfer.md#dispenser)
- Python - [`ensure_funded`](https://algorandfoundation.github.io/algokit-utils-py/html/apidocs/algokit_utils/algokit_utils.html#algokit_utils.ensure_funded) and [`get_dispenser_account`](https://algorandfoundation.github.io/algokit-utils-py/html/apidocs/algokit_utils/algokit_utils.html#algokit_utils.get_dispenser_account)

For more details about the `AlgoKit localnet` command, please refer to the [AlgoKit CLI reference documentation](../cli/index.md#localnet).
