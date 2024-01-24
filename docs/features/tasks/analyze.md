# AlgoKit Task Analyze

The `analyze` task is a command-line utility that analyzes TEAL programs for common vulnerabilities using [Tealer](https://github.com/crytic/tealer) integration. It allows you to detect a range of common vulnerabilities in code written in TEAL. For full list of vulnerability detectors refer to [Tealer documentation](https://github.com/crytic/tealer?tab=readme-ov-file#detectors).

## Usage

```bash
algokit task analyze INPUT_PATHS [OPTIONS]
```

### Arguments

- `INPUT_PATHS`: Paths to the TEAL files or directories containing TEAL files to be analyzed. This argument is required.

### Options

- `-r, --recursive`: Recursively search for all TEAL files within any provided directories.
- `--force`: Force verification without the disclaimer confirmation prompt.
- `--diff`: Exit with a non-zero code if differences are found between current and last reports.
- `-o, --output OUTPUT_PATH`: Directory path where to store the reports of the static analysis.
- `-e, --exclude DETECTORS`: Exclude specific vulnerabilities from the analysis. Supports multiple exclusions in a single run.

## Example

```bash
algokit task analyze ./contracts -r --exclude rekey-to --exclude missing-fee-check
```

This command will recursively analyze all TEAL files in the `contracts` directory and exclude the `missing-fee-check` vulnerability from the analysis.

## Security considerations

This task uses [`tealer`](https://github.com/crytic/tealer), a third-party tool, to suggest improvements for your TEAL programs, but remember to always test your smart contracts code, follow modern software engineering practices and use the [guidelines for smart contract development](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/guidelines/). This should not be used as a substitute for an actual audit.
