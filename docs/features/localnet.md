# AlgoKit LocalNet

The AlgoKit LocalNet feature allows you to manage (start, stop, reset, manage) a locally sandboxed private Algorand network. This allows you to interact and deploy changes against your own Algorand network without needing to worry about funding TestNet accounts, information you submit being publicly visible or being connected to an active Internet connection (once the network has been started).

AlgoKit LocalNet uses Docker images that are optimised for a great dev experience. This means the Docker images are small and start fast. It also means that features suited to developers are enabled such as KMD (so you can programmatically get faucet private keys).

The philosophy we take with AlgoKit LocalNet is that you should treat it as an ephemeral network. This means assume it could be reset at any time - don't store data on there that you can't recover / recreate. We have optimised the AlgoKit LocalNet experience to minimise situations where the network will get reset to improve the experience, but it can and will still happen in a number of situations.

## Prerequisites

AlgoKit LocalNet relies on Docker and Docker Compose being present and running on your system.

You can install Docker by following the [official installation instructions](https://docs.docker.com/get-docker/). Most of the time this will also install Docker Compose, but if not you can [follow the instructions](https://docs.docker.com/compose/install/) for that too.

If you are on Windows then you will need WSL 2 installed first, for which you can find the [official installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install). If you are using Windows 10 then ensure you are on the latest version to reduce likelihood of installation problems.

## Known issues

The AlgoKit LocalNet is built with 30,000 participation keys generated and after 30,000 rounds is reached it will no longer be able to add rounds. At this point you can simply reset the LocalNet to continue development. Participation keys are slow to generate hence why they are pre-generated to improve experience.

If you haven't issued any transactions and you restart the indexer container (or execute `algokit localnet stop` then `algokit localnet start`, or restart your computer and execute `algokit localnet start`) then the indexer will be stuck in an infinite starting loop. This is a [known issue in Algorand Sandbox](https://github.com/algorand/sandbox/issues/163) that should be resolved in the future. If this happens you can simply reset the sandbox via `algokit localnet reset`.

## Supported operating environments

We publish DockerHub images for `arm64` and `amd64`, which means that AlgoKit LocalNet is supported on Windows, Linux and Mac on Intel and AMD chipsets (including Mac M1).

## Functionality

### Creating / starting the LocalNet

To create / start your AlgoKit LocalNet instance you can run `algokit localnet start`. This will:

- Detect if you have Docker and Docker Compose installed
- Detect if you have the Docker engine running
- Create a new Docker Compose deployment for AlgoKit LocalNet if it doesn't already exist
- (Re-)Start the containers

If it's the first time running it on your machine then it will download the following images from DockerHub:

- [`makerxau/algorand-sandbox-dev`](https://hub.docker.com/r/makerxau/algorand-sandbox-dev) (~150-200 MB)
- [`makerxau/algorand-indexer-dev`](https://hub.docker.com/r/makerxau/algorand-indexer-dev) (~25 MB)
- [`postgres:13-alpine`](https://hub.docker.com/_/postgres) (~80 MB)

Once they have downloaded, it won't try and re-download images unless you perform a `algokit localnet reset`.

Once the LocalNet has started, the following endpoints will be available:

- [algod](https://developer.algorand.org/docs/rest-apis/algod/v2/):
  - address: http://localhost:4001
  - token: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- [kmd](https://developer.algorand.org/docs/rest-apis/kmd/):
  - address: http://localhost:4002
  - token: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- [indexer](https://developer.algorand.org/docs/rest-apis/indexer/):
  - address: http://localhost:8980
- tealdbg port:
  - address: http://localhost:9392

### Stopping and Resetting the LocalNet

To stop the LocalNet you can execute `algokit localnet stop`. This will turn off the containers, but keep them ready to be started again in the same state by executing `algokit localnet start`.

To reset the LocalNet you can execute `algokit localnet reset`, which will tear down the existing containers, refresh the container definition from the latest stored within AlgoKit and update to the latest Docker images. If you want to keep the same container spec and versions as you currently have, but quickly tear down and start a new instance then run `algokit localnet reset --no-update`.

### Viewing transactions in the LocalNet

You can see a web-based user interface of the current state of your LocalNet including all transactions by using the [AlgoKit Explore](./explore.md) feature, e.g. by executing `algokit localnet explore`.

### Executing goal commands against AlgoKit LocalNet

See the [AlgoKit Goal](./goal.md) feature. You can also execute `algokit localnet console` to open a [Bash shell which allows you to run the goal commandline](./goal.md#running-multiple-commands).

### Getting access to the private key of the faucet account

If you want to use the LocalNet then you need to get the private key of the initial wallet so you can transfer ALGOs out of it to other accounts you create.

There are two ways to do this:

**Option 1: Manually via goal**

```
algokit goal account list
algokit goal account export -a {address_from_an_online_account_from_above_command_output}
```

**Option 2: Automatically via kmd API**

Needing to do this manual step every time you spin up a new development environment or reset your LocalNet is frustrating. Instead, it's useful to have code that uses the Sandbox APIs to automatically retrieve the private key of the default account. The following `getSandboxDefaultAccount` function will help you achieve that. It's written in TypeScript, but the equivalent will work with [the Algorand SDK in other languages](https://developer.algorand.org/).

```typescript
// account.ts
import algosdk, { Account, Algodv2 } from "algosdk";
import { getKmdClient } from "./client";

export async function isSandbox(client: Algodv2): Promise<boolean> {
  const params = await client.getTransactionParams().do();

  return params.genesisID === "devnet-v1" || params.genesisID === "sandnet-v1";
}

export function getAccountFromMnemonic(mnemonic: string): Account {
  return algosdk.mnemonicToSecretKey(mnemonic);
}

export async function getSandboxDefaultAccount(
  client: Algodv2
): Promise<Account> {
  if (!(await isSandbox(client))) {
    throw "Can't get default account from non Sandbox network";
  }

  const kmd = getKmdClient();
  const wallets = await kmd.listWallets();

  // Sandbox starts with a single wallet called 'unencrypted-default-wallet', with heaps of tokens
  const defaultWalletId = wallets.wallets.filter(
    (w: any) => w.name === "unencrypted-default-wallet"
  )[0].id;

  const defaultWalletHandle = (await kmd.initWalletHandle(defaultWalletId, ""))
    .wallet_handle_token;
  const defaultKeyIds = (await kmd.listKeys(defaultWalletHandle)).addresses;

  // When you create accounts using goal they get added to this wallet so check for an account that's actually a default account
  let i = 0;
  for (i = 0; i < defaultKeyIds.length; i++) {
    const key = defaultKeyIds[i];
    const account = await client.accountInformation(key).do();
    if (account.status !== "Offline" && account.amount > 1000_000_000) {
      break;
    }
  }

  const defaultAccountKey = (
    await kmd.exportKey(defaultWalletHandle, "", defaultKeyIds[i])
  ).private_key;

  const defaultAccountMnemonic = algosdk.secretKeyToMnemonic(defaultAccountKey);
  return getAccountFromMnemonic(defaultAccountMnemonic);
}
```

To get the `Kmd` instance you can use something like this (tweak it based on where you retrieve your ALGOD token and server from):

```typescript
// client.ts
import { Kmd } from "algosdk";

// KMD client allows you to export private keys, which is useful to get the default account in a sandbox network
export function getKmdClient(): Kmd {
  return new Kmd(
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "http://localhost",
    "4002"
  );
}
```

For more details about the `AlgoKit localnet` command, please refer to the [AlgoKit CLI reference documentation](../cli/index.md#localnet).
