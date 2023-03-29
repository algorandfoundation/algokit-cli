# AlgoKit Doctor

The AlgoKit Doctor feature allows you to check your AlgoKit installation along with its dependencies. This is useful for diagnosing potential issues with using AlgoKit.

## Functionality

The AlgoKit Doctor allows you to make sure that your system has the correct dependencies installed and that they satisfy the minimum required versions. All passed checks will appear in your command line natural color while warnings will be in yellow (warning) and errors or missing critical services will be in red (error). The critical services that AlgoKit will check for (since they are [directly used by certain commands](../../README.md#prerequisites)): Docker, docker compose and git.

Please run this command to if you are facing an issue running AlgoKit. It is recommended to run it before [submitting an issue to AlgoKit](https://github.com/algorandfoundation/algokit-cli/issues/new). You can copy the contents of the Doctor command message (in Markdown format) to your clipboard by providing the `-c` flag to the command as follows `algokit doctor -c`.

# Examples

For example, running `algokit doctor` with all prerequisites installed will result in output similar to the following:

```
$ ~ algokit doctor
timestamp: 2023-03-29T03:58:05+00:00
AlgoKit: 0.6.0
AlgoKit Python: 3.11.2 (main, Mar 24 2023, 00:16:47) [Clang 14.0.0 (clang-1400.0.29.202)] (location: /Users/algokit/.local/pipx/venvs/algokit)
OS: macOS-13.2.1-arm64-arm-64bit
docker: 20.10.22
docker compose: 2.15.1
git: 2.39.1
python: 3.10.9 (location: /Users/algokit/.asdf/shims/python)
python3: 3.10.9 (location: /Users/algokit/.asdf/shims/python3)
pipx: 1.2.0
poetry: 1.3.2
node: 18.12.1
npm: 8.19.2
brew: 4.0.10-34-gb753315

If you are experiencing a problem with AlgoKit, feel free to submit an issue via:
https://github.com/algorandfoundation/algokit-cli/issues/new
Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`
```

The doctor command will indicate if there is any issues to address, for example:

If AlgoKit detects a newer version, this will be indicated next to the AlgoKit version
```
AlgoKit: 1.2.3 (latest: 4.5.6)
```

If the detected version of docker compose is unsupported, this will be shown:
```
docker compose: 2.1.3
  Docker Compose 2.5.0 required to run `algokit localnet command`;
  install via https://docs.docker.com/compose/install/
```

For more details about the `AlgoKit doctor` command, please refer to the [AlgoKit CLI reference documentation](../cli/index.md#doctor).
