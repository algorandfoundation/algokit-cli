# AlgoKit Doctor

The AlgoKit Doctor feature allows you to check the Algokit installation along with its dependencies.

## Functionality

The AlgoKit Doctor allows you to make sure that your system has the dependencies minimum right version are installed. All passed checks will appear in your command line natural color while non-critical error will be in yellow color and the critical results will be in red. The critical services for AlgoKit to run are: Docker, docker compose and git.

Please run this command to if you are facing a issue running AlgoKit. It is recommend to run it before submitting an issue to AlgoKit team. You can copy the contents of the Doctor command message (in Markdown format) to your clipboard by providing the `-c` flag to the command as follows `algokit doctor -c`

# Examples

For example, running `algokit doctor` with all prerequisites installed will result of the following output:

```
timestamp: 2023-01-05T02:50:49+00:00
AlgoKit: 0.1.0
AlgoKit Python: 3.11.0 (main, Oct 26 2022, 19:06:18) [Clang 14.0.0 (clang-1400.0.29.202)] (location: /Users/me/.local/pipx/venvs/algokit)
OS: macOS-13.1-arm64-arm-64bit
docker: 20.10.21
docker compose: 2.13.0
git: 2.37.1
python: 3.10.0 (location: /Library/Frameworks/Python.framework/Versions/3.10/bin/python3)
python3: 3.11.0 (location: /Library/Frameworks/Python.framework/Versions/3.11/bin/python3)
pipx: 1.1.0
poetry: 1.2.2
node: 18.12.1
npm: 8.19.3
brew: 3.6.16

If you are experiencing a problem with AlgoKit, feel free to submit an issue via:
https://github.com/algorandfoundation/algokit-cli/issues/new
Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`
```

For example, if there is a newer AlgoKit version, the doctor command will result in a line as follows:

```
AlgoKit: 1.2.3 (latest: 4.5.6)
```

For example, unsupported version of docker compose will result of the following line:

```
docker compose: 2.1.3
  Docker Compose 2.5.0 required to run `algokit sandbox command`;
  install via https://docs.docker.com/compose/install/
```

For more details about `AlgoKit doctor` command, please refer to [AlgoKit CLI](../cli/index.md)
