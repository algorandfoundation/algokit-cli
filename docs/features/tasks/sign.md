# AlgoKit Task Sign

The AlgoKit Sign feature allows you to sign Algorand transaction(s) using the AlgoKit CLI. This feature supports signing single or multiple transactions, either provided directly as a base64 encoded string or from a binary file.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task sign
Usage: algokit task sign [OPTIONS]

Sign goal clerk compatible Algorand transaction(s).

Options:
-a, --account TEXT Address or alias of the signer account. [required]
-f, --file PATH Single or multiple message pack encoded transactions from binary file to sign.
-t, --transaction TEXT Single base64 encoded transaction object to sign.
-o, --output PATH The output file path to store signed transaction(s).
--force Force signing without confirmation.
-h, --help Show this message and exit.
```

## Options

- `--account, -a TEXT`: Specifies the address or alias of the signer account. This option is required.
- `--file, -f PATH`: Specifies the path to a binary file containing single or multiple message pack encoded transactions to sign. Mutually exclusive with `--transaction` option.
- `--transaction, -t TEXT`: Specifies a single base64 encoded transaction object to sign. Mutually exclusive with `--file` option.
- `--output, -o PATH`: Specifies the output file path to store signed transaction(s).
- `--force`: If specified, it allows signing without interactive confirmation prompt.

> Please note, `--transaction` flag only supports signing a single transaction. If you want to sign multiple transactions, you can use the `--file` flag to specify a binary file containing multiple transactions.

## Example

To sign a transaction, you can use the `sign` command as follows:

```bash
$ algokit task sign --account {YOUR_ACCOUNT_ALIAS OR YOUR_ADDRESS} --file {PATH_TO_BINARY_FILE_CONTAINING_TRANSACTIONS}
```

This will prompt you to confirm the transaction details before signing. If you want to bypass the confirmation, you can use the `--force` flag:

```bash
$ algokit task sign --account {YOUR_ACCOUNT_ALIAS OR YOUR_ADDRESS} --transaction {YOUR_BASE64_ENCODED_TRANSACTION} --force
```

If the transaction is successfully signed, the signed transaction will be output to the console in a JSON format. If you want to write the signed transaction to a file, you can use the `--output` option:

```bash
$ algokit task sign --account {YOUR_ACCOUNT_ALIAS OR YOUR_ADDRESS} --transaction {YOUR_BASE64_ENCODED_TRANSACTION} --output /path/to/output/file
```

This will write the signed transaction to the specified file.

## Goal Compatibility

Please note, at the moment this feature only supports [`goal clerk`](https://developer.algorand.org/docs/clis/goal/clerk/clerk/) compatible transaction objects.

When `--output` option is not specified, the signed transaction(s) will be output to the console in a following JSON format:

```
[
  {transaction_id: "TRANSACTION_ID", content: "BASE64_ENCODED_SIGNED_TRANSACTION"},
]
```

On the other hand, when `--output` option is specified, the signed transaction(s) will be stored to a file as a message pack encoded binary file.

### Encoding transactins for signing

Algorand provides a set of options in [py-algorand-sdk](https://github.com/algorand/py-algorand-sdk) and [js-algorand-sdk](https://github.com/algorand/js-algorand-sdk) to encode transactions for signing.

Encoding simple txn object in python:

```py
# Encoding single transaction as a base64 encoded string
algosdk.encoding.msgpack_encode({"txn": {YOUR_TXN_OBJECT}.dictify()}) # Resulting string can be passed directy to algokit task sign with --transaction flag

# Encoding multiple transactions as a message pack encoded binary file
algosdk.transaction.write_to_file([{YOUR_TXN_OBJECT}], "some_file.txn") # Resulting file path can be passed directly to algokit sign with --file flag
```

Encoding simple txn object in javascript:

```ts
Buffer.from(algosdk.encodeObj({ txn: txn.get_obj_for_encoding() })).toString(
  "base64"
); // Resulting string can be passed directy to algokit task sign with --transaction flag
```

## Further Reading

For in-depth details, visit the [sign section](../../cli/index.md#sign) in the AlgoKit CLI reference documentation.
