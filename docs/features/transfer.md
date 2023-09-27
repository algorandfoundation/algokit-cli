# AlgoKit Task Transfer

The AlgoKit Transfer feature allows you to transfer algos and assets between two accounts

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task transfer
Usage: algokit task transfer

  Transfer an amount of algo or asset between two accounts

Options:
  -s, --sender    Address of the sender account
  -r, --receiver  Address to an account that will receive the asset(s)
  -id, --asset    ASA asset id to transfer
  -a, --amount    Amount to transfer
  --whole-units   Use whole units (Algos | ASAs) instead of smallest divisible units (for example, microAlgos).
  -n, --network   Network where the transfer will be executed
```

## Examples

Transfer algo between accounts:

```bash
$ ~ algokit task transfer -s sender.addr -r receiver.addr -a amount
```

Transfer asset between accounts:

```bash
$ ~ algokit task transfer -s sender.addr -r receiver.addr -id asset-id -a amount
```
