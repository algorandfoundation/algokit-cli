# AlgoKit Task Asset opt-(in|out)

AlgoKit Task Asset opt-(in|out) allows you to opt-in or opt-out of Algorand Asset(s). This task supports single or multiple assets.

## Usage

Available commands and possible usage as follows:

### Opt-in

```bash
Usage: algokit task opt-in [OPTIONS] ASSET_IDS...

  Opt-in to an asset(s). This is required before you can receive an asset.
  Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.

Options:
  --account, -a TEXT  Address or alias of the signer account.  [required]
  -n, --network [localnet|testnet|mainnet]
                      Network to use. Refers to `localnet` by default.
```

### Opt-out

```bash
Usage: algokit task opt-out [OPTIONS] [ASSET_IDS]...

  Opt-out of an asset(s). You can only opt out of an asset with a zero balance.
  Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.

Options:
  --account, -a TEXT  Address or alias of the signer account.  [required]
  --all                Opt-out of all assets with zero balance.
  -n, --network [localnet|testnet|mainnet]
                      Network to use. Refers to `localnet` by default.
```

## Options

- `ASSET_IDS`: Specifies the asset IDs to opt-in or opt-out. To supply multiple asset IDs, separate them with a whitespace.
- `--account`, `-a` TEXT: Specifies the address or alias of the signer account. This option is required.
- `--all`: Specifies to opt-out of all assets with zero balance.
- `-n`, `--network` [localnet|testnet|mainnet]: Specifies the network to use. Refers to localnet by default.

## Example

Example

To opt-in to an asset(s), you can use the opt-in command as follows:

```bash
$ algokit task opt-in --account {YOUR_ACCOUNT} {ASSET_ID_1} {ASSET_ID_2} {ASSET_ID_3} ...
```

To opt-out of an asset(s), you can use the opt-out command as follows:

```bash
$ algokit task opt-out --account {YOUR_ACCOUNT} {ASSET_ID_1} {ASSET_ID_2} ...
```

To opt-out of all assets with zero balance, you can use the opt-out command with the `--all` flag:

```bash
$ algokit task opt-out --account {YOUR_ACCOUNT} --all
```

> Please note, the account must have sufficient balance to cover the transaction fees.

## Further Reading

For in-depth details, visit the [opt-in](../../cli/index.md#opt-in) and [opt-out](../../cli/index#opt-out) sections in the AlgoKit CLI reference documentation.
