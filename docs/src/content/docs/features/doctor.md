---
title: "AlgoKit Doctor"
---

The AlgoKit Doctor feature allows you to check your AlgoKit installation along with its dependencies. This is useful for diagnosing potential issues with using AlgoKit.

## Functionality

The AlgoKit Doctor allows you to make sure that your system has the correct dependencies installed and that they satisfy the minimum required versions. All passed checks will appear in your command line natural color while warnings will be in yellow (warning) and errors or missing critical services will be in red (error). The critical services that AlgoKit will check for (since they are [directly used by certain commands](../../README.md#prerequisites)): Docker, docker compose and git.

Please run this command to if you are facing an issue running AlgoKit. It is recommended to run it before [submitting an issue to AlgoKit](https://github.com/algorandfoundation/algokit-cli/issues/new). You can copy the contents of the Doctor command message (in Markdown format) to your clipboard by providing the `-c` flag to the command as follows `algokit doctor -c`.

> NOTE: You can also use the `--verbose` or `-v` flag to show additional information including package dependencies of the AlgoKit CLI: `algokit -v doctor`. This only works when `algokit` is installed as a Python package (e.g., via `uv tool install algokit`).

# Examples

For example, running `algokit doctor` with all prerequisites installed will result in output similar to the following:

```
$ ~ algokit doctor
timestamp: 2023-03-29T03:58:05+00:00
AlgoKit: 2.10.2
AlgoKit Python: 3.12.11 (location: ~/.local/share/uv/tools/algokit)
OS: macOS-15.0-arm64-arm-64bit
docker: 27.5.1
docker compose: 2.32.4
git: 2.47.0
python: 3.12.11 (location: ~/.local/share/uv/python/cpython-3.12.11)
python3: 3.12.11 (location: ~/.local/share/uv/python/cpython-3.12.11)
uv: 0.10.7
node: 22.14.0
npm: 10.9.2

If you are experiencing a problem with AlgoKit, feel free to submit an issue via:
https://github.com/algorandfoundation/algokit-cli/issues/new
Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`
```

The doctor command will indicate if there is any issues to address, for example:

If AlgoKit detects a newer version, this will be indicated next to the AlgoKit version

```bash
AlgoKit: 1.2.3 (latest: 4.5.6)
```

If the detected version of docker compose is unsupported, this will be shown:

```bash
docker compose: 2.1.3
  Docker Compose 2.5.0 required to run `algokit localnet command`;
  install via https://docs.docker.com/compose/install/
```

For more details about the `AlgoKit doctor` command, please refer to the [AlgoKit CLI reference documentation](/algokit-cli/cli/#doctor).
