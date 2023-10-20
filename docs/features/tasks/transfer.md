# AlgoKit Task Transfer

The AlgoKit Transfer feature allows you to transfer algos and assets between two accounts.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task transfer
Usage: algokit task transfer [OPTIONS]

Transfer algos or assets from one account to another.

Options:
  -s, --sender TEXT               Address or alias of the sender account  [required]
  -r, --receiver TEXT             Address or alias to an account that will receive the asset(s)  [required]
  --asset, --id INTEGER           ASA asset id to transfer
  -a, --amount INTEGER            Amount to transfer  [required]
  --whole-units                   Use whole units (Algos | ASAs) instead of smallest divisible units (for example,
                                  microAlgos). Disabled by default.
  -n, --network [localnet|testnet|mainnet]
                                  Network to use. Refers to `localnet` by default.
  -h, --help                      Show this message and exit.
```

> Note: If you use a wallet address for the `sender` argument, you'll be asked for the mnemonic phrase. To use a wallet alias instead, see the [wallet aliasing](wallet.md) task. For wallet aliases, the sender must have a stored `private key`, but the receiver doesn't need one. This is because the sender signs and sends the transfer transaction, while the receiver reference only needs a valid Algorand address.

## Examples

### Transfer algo between accounts on LocalNet

```bash
$ ~ algokit task transfer -s {SENDER_ALIAS OR SENDER_ADDRESS} -r {RECEIVER_ALIAS OR RECEIVER_ADDRESS} -a {AMOUNT}
```

By default:

- the `amount` is in microAlgos. To use whole units, use the `--whole-units` flag.
- the `network` is `localnet`.

### Transfer asset between accounts on TestNet

```bash
$ ~ algokit task transfer -s {SENDER_ALIAS OR SENDER_ADDRESS} -r {RECEIVER_ALIAS OR RECEIVER_ADDRESS} -a {AMOUNT} --id {ASSET_ID} --network testnet
```

By default:

- the `amount` is smallest divisible unit of supplied `ASSET_ID`. To use whole units, use the `--whole-units` flag.

## Further Reading

For in-depth details, visit the [transfer section](../../cli/index.md#transfer) in the AlgoKit CLI reference documentation.
