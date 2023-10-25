# AlgoKit Task Send

The AlgoKit Send feature allows you to send signed Algorand transaction(s) to a specified network using the AlgoKit CLI. This feature supports sending single or multiple transactions, either provided directly as a base64 encoded string or from a binary file.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task send
Usage: algokit task send [OPTIONS]

  Send a signed transaction to the given network.

Options:
  -f, --file FILE                 Single or multiple message pack encoded signed transactions from binary file to
                                  send. Option is mutually exclusive with transaction.
  -t, --transaction TEXT          Base64 encoded signed transaction to send. Option is mutually exclusive with file.
  -n, --network [localnet|testnet|mainnet]
                                  Network to use. Refers to `localnet` by default.
  -h, --help                      Show this message and exit.
```

## Options

- `--file, -f PATH`: Specifies the path to a binary file containing single or multiple message pack encoded signed transactions to send. Mutually exclusive with `--transaction` option.
- `--transaction, -t TEXT`: Specifies a single base64 encoded signed transaction to send. Mutually exclusive with `--file` option.
- `--network, -n [localnet|testnet|mainnet]`: Specifies the network to which the transactions will be sent. Refers to `localnet` by default.

> Please note, `--transaction` flag only supports sending a single transaction. If you want to send multiple transactions, you can use the `--file` flag to specify a binary file containing multiple transactions.

## Example

To send a transaction, you can use the `send` command as follows:

```bash
$ algokit task send --file {PATH_TO_BINARY_FILE_CONTAINING_SIGNED_TRANSACTIONS}
```

This will send the transactions to the default `localnet` network. If you want to send the transactions to a different network, you can use the `--network` flag:

```bash
$ algokit task send --transaction {YOUR_BASE64_ENCODED_SIGNED_TRANSACTION} --network testnet
```

You can also pipe in the `stdout` of `algokit sign` command:

```bash
$ algokit task sign --account {YOUR_ACCOUNT_ALIAS OR YOUR_ADDRESS} --file {PATH_TO_BINARY_FILE_CONTAINING_TRANSACTIONS} --force | algokit task send --network {network_name}
```

If the transaction is successfully sent, the transaction ID (txid) will be output to the console. You can check the transaction status at the provided transaction explorer URL.

## Goal Compatibility

Please note, at the moment this feature only supports [`goal clerk`](https://developer.algorand.org/docs/clis/goal/clerk/clerk/) compatible transaction objects.

## Further Reading

For in-depth details, visit the [send section](../../cli/index.md#send) in the AlgoKit CLI reference documentation.
