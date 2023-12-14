# AlgoKit Task Mint

The AlgoKit Mint feature allows you to mint new fungible or non-fungible assets on the Algorand blockchain. This feature supports the creation of assets, validation of asset parameters, and uploading of asset metadata and image to IPFS using the Piñata provider. Immutable assets are compliant with [ARC3](https://arc.algorand.foundation/ARCs/arc-0003), while mutable are based using [ARC19](https://arc.algorand.foundation/ARCs/arc-0019) standard.

## Usage

Available commands and possible usage as follows:

```bash
Usage: algokit task mint [OPTIONS]

  Mint new fungible or non-fungible assets on Algorand.

Options:
  --creator TEXT                  Address or alias of the asset creator.  [required]
  -n, --name TEXT                 Asset name.  [required]
  -u, --unit TEXT                 Unit name of the asset.  [required]
  -t, --total INTEGER             Total supply of the asset. Defaults to 1.
  -d, --decimals INTEGER          Number of decimals. Defaults to 0.
  -i, --image FILE                Path to the asset image file to be uploaded to IPFS.  [required]
  -m, --metadata FILE             Path to the ARC19 compliant asset metadata file to be uploaded to IPFS. If not
                                  provided, a default metadata object will be generated automatically based on asset-
                                  name, decimals and image. For more details refer to
                                  https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema.
  --mutable / --immutable         Whether the asset should be mutable or immutable. Refers to `ARC19` by default.
  --nft / --ft                    Whether the asset should be validated as NFT or FT. Refers to NFT by default and
                                  validates canonical definitions of pure or fractional NFTs as per ARC3 standard.
  -n, --network [localnet|testnet|mainnet]
                                  Network to use. Refers to `localnet` by default.
  -h, --help                      Show this message and exit.
```

## Options

- `--creator TEXT`: Specifies the address or alias of the asset creator. This option is required.
- `-n, --name TEXT`: Specifies the asset name. This option is required.
- `-u, --unit TEXT`: Specifies the unit name of the asset. This option is required.
- `-t, --total INTEGER`: Specifies the total supply of the asset. Defaults to 1.
- `-d, --decimals INTEGER`: Specifies the number of decimals. Defaults to 0.
- `-i, --image PATH`: Specifies the path to the asset image file to be uploaded to IPFS. This option is required.
- `-m, --metadata PATH`: Specifies the path to the ARC19 compliant asset metadata file to be uploaded to IPFS. If not provided, a default metadata object will be generated automatically based on asset-name, decimals and image.
- `--mutable / --immutable`: Specifies whether the asset should be mutable or immutable. Refers to `ARC19` by default.
- `--nft / --ft`: Specifies whether the asset should be validated as NFT or FT. Refers to NFT by default and validates canonical definitions of pure or fractional NFTs as per ARC3 standard.
- `-n, --network [localnet|testnet|mainnet]`: Specifies the network to use. Refers to `localnet` by default.

## Example

To mint a new asset in interactive mode, you can use the mint command as follows:

```bash
$ algokit task mint
```

This will interactively prompt you for the required information, upload the asset image and metadata to IPFS using the Piñata provider and mint a new asset on the Algorand blockchain. The [asset's metadata](https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema) will be generated automatically based on the provided asset name, decimals, and image.

If you want to provide a custom metadata file, you can use the --metadata flag:

```bash
$ algokit task mint --metadata {PATH_TO_METADATA}
```

If the minting process is successful, the asset ID and transaction ID will be output to the console.

For non interactive mode, refer to usage section above for available options.

> Please note, creator account must have at least 0.2 Algos available to cover minimum balance requirements.

## Further Reading

For in-depth details, visit the [mint section](../../cli/index.md#mint) in the AlgoKit CLI reference documentation.
