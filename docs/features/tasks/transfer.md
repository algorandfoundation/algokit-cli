# AlgoKit Task Transfer

The AlgoKit Transfer feature allows you to transfer algos and assets between two accounts.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task transfer
Usage: algokit task transfer [OPTIONS] [[localnet|testnet|mainnet]]

Options:
  -s, --sender TEXT      Address or alias of the sender account  [required]
  -r, --receiver TEXT    Address to an account that will receive the asset(s)  [required]
  --asset, --id INTEGER  ASA asset id to transfer (defaults to 0, Algos)
  -a, --amount INTEGER   Amount to transfer  [required]
  --whole-units          Use whole units (Algos | ASAs) instead of smallest divisible units (for example, microAlgos).
                         Disabled by default.
  -h, --help             Show this message and exit.
```

> Please note, when supplying `sender` argument as a wallet address, you will be prompted for a masked input of the mnemonic phrase.
> If you would prefer to use a wallet alias, refer to [wallet aliasing](wallet.md) task for details on creating and using wallet aliases.

## Examples

### Transfer algo between accounts

```bash
$ ~ algokit task transfer -s {SENDER_ALIAS OR SENDER_ADDRESS} -r {RECEIVER_ADDRESS} -a {AMOUNT}
```

By default, the amount is in microAlgos. To use whole units, use the `--whole-units` flag.

### Transfer asset between accounts

```bash
$ ~ algokit task transfer -s {SENDER_ALIAS OR SENDER_ADDRESS} -r {RECEIVER_ADDRESS} -a {AMOUNT} --id {ASSET_ID}
```

By default, the amount is in smallest divisible unit of given asset (if exists). To use whole units, use the `--whole-units` flag.
