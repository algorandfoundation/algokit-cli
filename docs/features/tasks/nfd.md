# AlgoKit Task NFD Lookup

The AlgoKit NFD Lookup feature allows you to perform a lookup via NFD domain or address, returning the associated address or domain respectively using the AlgoKit CLI. The feature is powered by [NFDomains MainNet API](https://api-docs.nf.domains/).

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task nfd-lookup
Usage: algokit task nfd-lookup [OPTIONS] VALUE

Perform a lookup via NFD domain or address, returning the associated address or domain respectively.

Options:
-o, --output [full|tiny|address] Output format for NFD API response. Defaults to address|domain resolved.
-h, --help                       Show this message and exit.
```

## Options

- `VALUE`: Specifies the NFD domain or Algorand address to lookup. This argument is required.
- `--output, -o [full|tiny|address]`: Specifies the output format for NFD API response. Defaults to address|domain resolved.

> When using the `full` and `tiny` output formats, please be aware that these match the [views in get requests of the NFD API](https://api-docs.nf.domains/quick-start#views-in-get-requests). The `address` output format, which is used by default, refers to the respective domain name or address resolved and outputs it as a string (if found).

## Example

To perform a lookup, you can use the nfd-lookup command as follows:

```bash
$ algokit task nfd-lookup {NFD_DOMAIN_OR_ALGORAND_ADDRESS}
```

This will perform a lookup and return the associated address or domain. If you want to specify the output format, you can use the --output flag:

```bash
$ algokit task nfd-lookup {NFD_DOMAIN_OR_ALGORAND_ADDRESS} --output full
```

If the lookup is successful, the result will be output to the console in a JSON format.

## Further Reading

For in-depth details, visit the [nfd-lookup section](../../cli/index.md#nfd-lookup) in the AlgoKit CLI reference documentation.
