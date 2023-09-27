# AlgoKit Task Vanity Address

The AlgoKit Vanity Address feature allows you to generate a vanity Algorand address. A vanity address is an address that contains a specific keyword in it. The keyword can only include uppercase letters A-Z and numbers 2-7. The longer the keyword, the longer it may take to generate a matching address.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task wallet
Usage: algokit task vanity-address [OPTIONS] KEYWORD

  Generate a vanity Algorand address. Your KEYWORD can only include letters A - Z and numbers 2 - 7. Keeping your
  KEYWORD under 5 characters will usually result in faster generation. Note: The longer the KEYWORD, the longer it may
  take to generate a matching address. Please be patient if you choose a long keyword.

Options:
  -m, --match [start|anywhere|end] Location where the keyword will be included. Default is start.
  -o, --output [stdout|alias|file] How the output will be presented.
  -a, --alias TEXT                 Alias for the address. Required if output is "alias".
  -f, --output-file PATH           File to dump the output. Required if output is "file".
  -h, --help                       Show this message and exit.
```

## Examples

Generate a vanity address with the keyword "ALGO" at the start of the address with default output to `stdout`:

```bash
$ ~ algokit task vanity-address ALGO
```

Generate a vanity address with the keyword "ALGO" at the start of the address with output to a file:

```bash
$ ~ algokit task vanity-address ALGO -o file -f vanity-address.txt
```

Generate a vanity address with the keyword "ALGO" anywhere in the address with output to a file:

```bash
$ ~ algokit task vanity-address ALGO -m anywhere -o file -f vanity-address.txt
```
