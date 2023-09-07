# AlgoKit TestNet Dispenser

The AlgoKit Dispenser feature allows you to interact with the AlgoKit TestNet Dispenser. This feature is essential for funding your wallet with TestNet ALGOs, refunding ALGOs back to the dispenser wallet, and getting information about current fund limits on your account.

## Usage

```zsh
$ algokit dispenser [OPTIONS] COMMAND [ARGS]...
```

This command provides a set of subcommands to interact with the AlgoKit TestNet Dispenser.
Subcommands

- `login`: Login to your Dispenser API account.
- `logout`: Logout of your Dispenser API account.
- `fund`: Fund your wallet address with TestNet ALGOs.
- `refund`: Refund ALGOs back to the dispenser wallet address.
- `limit`: Get information about current fund limits on your account.

## Login

```zsh
$ algokit dispenser login [OPTIONS]
```

This command logs you into your Dispenser API account. If you are already logged in, it will notify you that you are already logged in.
Options

- `--ci`: Generate an access token for CI. Issued for 30 days.
- `--output`, -o: Output filename where you want to store the generated access token. Defaults to ci_token.txt. Only applicable when --ci flag is set.

## Logout

```zsh
$ algokit dispenser logout
```

This command logs you out of your Dispenser API account. If you are not logged in, it will notify you to login first.

## Fund

```zsh
$ algokit dispenser fund [OPTIONS]
```

This command funds your wallet address with TestNet ALGOs.
Options

- `--receiver`, -r: Receiver address to fund with TestNet ALGOs. This option is required.
- `--amount`, -a: Amount to fund. Defaults to microAlgos. This option is required.
- `--whole-units`: Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.
- `--ci`: Enable/disable interactions with Dispenser API via CI access token.

## Refund

```zsh
$ algokit dispenser refund [OPTIONS]
```

This command refunds ALGOs back to the dispenser wallet address.
Options

- `--txID`, -t: Transaction ID of your refund operation. This option is required.
- `--ci`: Enable/disable interactions with Dispenser API via CI access token.

## Limit

```zsh
$ algokit dispenser limit [OPTIONS]
```

This command gets information about current fund limits on your account. The limits reset daily.
Options

- `--whole-units`: Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.
- `--ci`: Enable/disable interactions with Dispenser API via CI access token.

## Further Reading

For in-depth details, visit the [dispenser section](../cli/index.md#dispenser) in the AlgoKit CLI reference documentation.
