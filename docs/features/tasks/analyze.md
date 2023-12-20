# AlgoKit Task Analyze

The `analyze` task is a command-line utility that analyzes TEAL programs for common vulnerabilities using AlgoKit [Tealer](https://github.com/crytic/tealer) integration. It allows you to detect a range of common vulnerabilities that can be encountered in code written in TEAL. For full list of vulnerability detctors refer to [Tealer documentation](https://github.com/crytic/tealer?tab=readme-ov-file#detectors).

## Usage

```bash
algokit task analyze INPUT_PATHS [OPTIONS]
```

### Arguments

- `INPUT_PATHS`: Paths to the TEAL files or directories containing TEAL files to be analyzed. This argument is required.

### Options

- `-r, --recursive`: Recursively search for all TEAL files within the provided directory.
- `--force`: Force verification without the disclaimer confirmation prompt.
- `--diff`: Exit with a non-zero code if any diffs are identified between the current and baseline reports.
- `-o, --output OUTPUT_PATH`: Directory path where to store the results of the static analysis.
- `-e, --exclude DETECTORS`: Exclude specific vulnerabilities from the analysis. Supports multiple exclusions in a single run.

## Example

```bash
algokit task analyze ./contracts -r --exclude rekey-to --exclude missing-fee-check
```

This command will recursively analyze all TEAL files in the `contracts` directory and exclude the `missing-fee-check` vulnerability from the analysis.

## Security considerations

This task uses [`tealer`](https://github.com/crytic/tealer), a third-party tool, to suggest improvements for your TEAL programs, but remember to always test your smart contracts code and follow modern software engineering practices.
