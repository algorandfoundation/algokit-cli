# AlgoKit Task IPFS

The AlgoKit IPFS feature allows you to interact with the IPFS [InterPlanetary File System](https://ipfs.tech/) using the [Web3 Storage provider](https://web3.storage/). This feature supports logging in and out of the Web3 Storage provider, and uploading files to IPFS.

## Usage

Available commands and possible usage as follows:

```bash
$ ~ algokit task ipfs
Usage: algokit task ipfs [OPTIONS]

Upload files to IPFS using Web3 Storage provider.

Options:
  -f, --file PATH Path to the file to upload. [required]
  -n, --name TEXT Human readable name for this upload, for use in file listings.
  -h, --help Show this message and exit.
```

## Options

- `--file, -f PATH`: Specifies the path to the file to upload. This option is required.
- `--name, -n TEXT`: Specifies a human readable name for this upload, for use in file listings.

## Prerequisites

Before you can use this feature, you need to ensure that you have signed up for a Web3 Storage account and have an API token. You can sign up for a Web3 Storage account by reading [quickstart](https://web3.storage/docs/intro/#quickstart).

## Login

Please note, you need to login to the Web3 Storage provider before you can upload files. You can do this using the `login` command:

```bash
$ algokit task ipfs login
```

This will prompt you to enter your Web3 Storage API token. Once you are logged in, you can upload files to IPFS.

## Upload

To upload a file to IPFS, you can use the `ipfs` command as follows:

```bash
$ algokit task ipfs --file {PATH_TO_YOUR_FILE}
```

This will upload the file to IPFS using the Web3 Storage provider and return the CID (Content Identifier) of the uploaded file.

## Logout

If you want to logout from the Web3 Storage provider, you can use the `logout` command:

```bash
$ algokit task ipfs logout
```

This will remove your Web3 Storage API token from the keyring.

## File Size Limit

Please note, the maximum file size that can be uploaded is 100MB. If you try to upload a file larger than this, you will receive an error.
