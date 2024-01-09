# AlgoKit Task Wallet

Manage your Algorand addresses and accounts effortlessly with the AlgoKit Wallet feature. This feature allows you to create short aliases for your addresses and accounts on AlgoKit CLI.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task wallet
Usage: algokit task wallet [OPTIONS] COMMAND [ARGS]...

Create short aliases for your addresses and accounts on AlgoKit CLI.

Options:
-h, --help Show this message and exit.

Commands:
add Add an address or account to be stored against a named alias.
get Get an address or account stored against a named alias.
list List all addresses and accounts stored against a named alias.
remove Remove an address or account stored against a named alias.
reset Remove all aliases.
```

## Commands

### Add

This command adds an address or account to be stored against a named alias. If the `--mnemonic` flag is used, it will prompt the user for a mnemonic phrase interactively using masked input. If the `--force` flag is used, it will allow overwriting an existing alias. Maximum number of aliases that can be stored at a time is 50.

```bash
$ algokit wallet add [OPTIONS] ALIAS_NAME
```

> Please note, the command is not designed to be used in CI scope, there is no option to skip interactive masked input of the mnemonic, if you want to alias an `Account` (both private and public key) entity.

#### Options

- `--address, -a TEXT`: Specifies the address of the account. This option is required.
- `--mnemonic, -m`: If specified, it prompts the user for a mnemonic phrase interactively using masked input.
- `--force, -f`: If specified, it allows overwriting an existing alias without interactive confirmation prompt.

### Get

This command retrieves an address or account stored against a named alias.

```bash
$ algokit wallet get ALIAS
```

### List

This command lists all addresses and accounts stored against a named alias. If a record contains a `private_key` it will show a boolean flag indicating whether it exists, actual private key values are never exposed. As a user you can obtain the content of the stored aliases by navigating to your dedicated password manager (see [keyring details](https://pypi.org/project/keyring/)).

```bash
$ algokit wallet list
```

### Remove

This command removes an address or account stored against a named alias.
You must confirm the prompt interactively or pass `--force` | `-f` flag to ignore the prompt.

```bash
$ algokit wallet remove ALIAS  [--force | -f]
```

### Reset

This command removes all aliases. You must confirm the prompt interactively or pass `--force` | `-f` flag to ignore the prompt.

```bash
$ algokit wallet reset [--force | -f]
```

## Keyring

AlgoKit relies on the [keyring](https://pypi.org/project/keyring/) library, which provides an easy way to interact with the operating system's password manager. This abstraction allows AlgoKit to securely manage sensitive information such as mnemonics and private keys.

When you use AlgoKit to store a mnemonic, it is never printed or exposed directly in the console. Instead, the mnemonic is converted and stored as a private key in the password manager. This ensures that your sensitive information is kept secure.

To retrieve the stored mnemonic, you will need to manually navigate to your operating system's password manager. The keyring library supports a variety of password managers across different operating systems. Here are some examples:

- On macOS, it uses the Keychain Access app.
- On Windows, it uses the Credential Manager.
- On Linux, it can use Secret Service API, KWallet, or an in-memory store depending on your setup.

> Remember, AlgoKit is designed to keep your sensitive information secure however your storage is only as secure as the device on which it is stored. Always ensure to maintain good security practices on your device, especially when dealing with mnemonics that are to be used on MainNet.

## Further Reading

For in-depth details, visit the [wallet section](../../cli/index.md#wallet) in the AlgoKit CLI reference documentation.
