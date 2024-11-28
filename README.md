<div align="center">
<a href="https://github.com/algorandfoundation/algokit-cli"><img src="https://ipfs.algonode.xyz/ipfs/QmZqt55wHXrZzhBihSVzXDvwp9rguvLAvFhUm1qJR6GYeQ" width=60%></a>
</div>

<p align="center">
    <a target="_blank" href="https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md"><img src="https://img.shields.io/badge/docs-repository-00dc94?logo=github&style=flat.svg" /></a>
    <a target="_blank" href="https://developer.algorand.org/algokit/"><img src="https://img.shields.io/badge/learn-AlgoKit-00dc94?logo=algorand&mac=flat.svg" /></a>
    <a target="_blank" href="https://github.com/algorandfoundation/algokit-cli"><img src="https://img.shields.io/github/stars/algorandfoundation/algokit-cli?color=00dc94&logo=star&style=flat" /></a>
    <a target="_blank" href="https://developer.algorand.org/algokit/"><img  src="https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2Falgorandfoundation%2Falgokit-cli&countColor=%2300dc94&style=flat" /></a>
</p>

---

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the [Algorand network](https://www.algorand.com/).

AlgoKit gets developers of all levels up and running with a familiar, fun and productive development environment in minutes. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

[Install AlgoKit](#install) | [Quick Start Tutorial](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/tutorials/intro.md) | [Documentation](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md)

## What is AlgoKit?

AlgoKit compromises of a number of components that make it the one-stop shop tool for developers building on the [Algorand network](https://www.algorand.com/).

![AlgoKit components](https://raw.githubusercontent.com/algorandfoundation/algokit-cli/main/docs/imgs/algokit-map.png)

AlgoKit can help you [**learn**](#learn), [**develop**](#develop) and [**operate**](#operate) Algorand solutions. It consists of [a number of repositories](https://github.com/search?q=org%3Aalgorandfoundation+algokit-&type=repositories), including this one.

### Learn

There are many learning resources on the [Algorand Developer Portal](https://developer.algorand.org/) and the [AlgoKit landing page](https://developer.algorand.org/algokit) has a range of links to more learning materials. In particular, check out the [quick start tutorial](https://developer.algorand.org/docs/get-started/algokit/) and the [AlgoKit detailed docs page](https://developer.algorand.org/docs/get-details/algokit/).

If you need help you can access both the [Algorand Discord](https://discord.gg/84AActu3at) (pro-tip: check out the algokit channel!) and the [Algorand Forum](https://forum.algorand.org/).

We have also developed an [AlgoKit video series](https://www.youtube.com/@algodevs/playlists).

### Develop

AlgoKit helps you develop Algorand solutions:

- **Interaction**: AlgoKit exposes a number of interaction methods, namely:
  - [**AlgoKit CLI**](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md): A Command Line Interface (CLI) so you can quickly access AlgoKit capabilities
  - [VS Code](https://code.visualstudio.com/): All AlgoKit project templates include VS Code configurations so you have a smooth out-of-the-box development experience using VS Code
  - [lora](https://lora.algokit.io/): AlgoKit has integrations with lora; a web-based user interface that let's you visualise and interact with an Algorand network
- **Getting Started**: AlgoKit helps you get started quickly when building new solutions:
  - [**AlgoKit Templates**](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/init.md): Template libraries to get you started faster and quickly set up a productive dev experience
- **Development**: AlgoKit provides SDKs, tools and libraries that help you quickly and effectively build high quality Algorand solutions:
  - **AlgoKit Utils** ([Python](https://github.com/algorandfoundation/algokit-utils-py#readme) | [TypeScript](https://github.com/algorandfoundation/algokit-utils-ts#readme)): A set of utility libraries so you can develop, test, build and deploy Algorand solutions quickly and easily
    - [algosdk](https://developer.algorand.org/docs/sdks/) ([Python](https://github.com/algorand/py-algorand-sdk#readme) | [TypeScript](https://github.com/algorand/js-algorand-sdk#readme)) - The core Algorand SDK providing Algorand protocol API calls, which AlgoKit Utils wraps, but still exposes for advanced scenarios
  - [**Algorand Python**](https://github.com/algorandfoundation/puya): A semantically and syntactically compatible, typed Python language that works with standard Python tooling and allows you to express smart contracts (apps) and smart signatures (logic signatures) for deployment on the Algorand Virtual Machine (AVM).
  - [**TEALScript**](https://github.com/algorandfoundation/TEALScript): A subset of TypeScript that can be used to express smart contracts (apps) and smart signatures (logic signatures) for deployment on the Algorand Virtual Machine (AVM).
  - [**AlgoKit LocalNet**](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/localnet.md): A local isolated Algorand network so you can simulate real transactions and workloads on your computer

### Operate

AlgoKit can help you deploy and operate Algorand solutions.

AlgoKit comes with out-of-the-box [Continuous Integration / Continuous Deployment (CI/CD) templates](https://github.com/algorandfoundation/algokit-python-template) that help you rapidly set up best-practice software delivery processes that ensure you build quality in and have a solution that can evolve

## What can AlgoKit help me do?

The set of capabilities supported by AlgoKit will evolve over time, but currently includes:

- Quickly run, explore and interact with an isolated local Algorand network (LocalNet)
- Building, testing, deploying and calling [Algorand Python](https://github.com/algorandfoundation/puya) / [TEALScript](https://github.com/algorandfoundation/TEALScript) smart contracts

For a user guide and guidance on how to use AlgoKit, please refer to the [docs](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md).

Future capabilities are likely to include:

- Quickly deploy [standardised](https://github.com/algorandfoundation/ARCs/#arcs-algorand-requests-for-comments), audited smart contracts
- Building and deploying Algorand dApps

## Is this for me?

The target audience for this tool is software developers building applications on the Algorand network. A working knowledge of using a command line interfaces and experience using the supported programming languages is assumed.

## How can I contribute?

This is an open source project managed by the Algorand Foundation. See the [contributing page](https://github.com/algorandfoundation/algokit-cli/blob/main/CONTRIBUTING.md) to learn about making improvements to the CLI tool itself, including developer setup instructions.

# Install

> **Note** Refer to [Troubleshooting](#troubleshooting) for more details on mitigation of known edge cases when installing AlgoKit.

## Prerequisites

The key required dependency is Python 3.10+, but some of the installation options below will install that for you. We recommend using Python 3.12+, as the `algokit compile python` command requires this version.

> **Note**
> You can still install and use AlgoKit without these dependencies, and AlgoKit will tell you if you are missing one for a given command.

- **Git**: Essential for creating and updating projects from templates. Installation guide available at [Git Installation](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).
- **Docker**: Necessary for running the AlgoKit LocalNet environment. Docker Compose version 2.5.0 or higher is required. See [Docker Installation](https://docs.docker.com/get-docker/).
- **Node.js**: For those working on frontend templates or building contracts using TEALScript. **Minimum required versions are Node.js `v18` and npm `v9`**. Instructions can be found at [Node.js Installation](https://nodejs.org/en/download/).

> **Note**
> If you have previously installed AlgoKit using `pipx` and would like to switch to a different installation method, please ensure that
> you first uninstall the existing version by running `pipx uninstall algokit`. Once uninstalled, you can follow the installation instructions for your preferred platform.

## Cross-platform installation

AlgoKit can be installed using OS specific package managers, or using the python tool [pipx](https://pypa.github.io/pipx/).
See below for specific installation instructions.

### Installation Methods

- [Windows](#install-algokit-on-windows)
- [Mac](#install-algokit-on-mac)
- [Linux](#install-algokit-on-linux)
- [pipx](#install-algokit-with-pipx-on-any-os)

## Install AlgoKit on Windows

> **Note**
> AlgoKit is supported on Windows 10 1709 (build 16299) and later.
> We only publish an x64 binary, however it also runs on ARM devices by default using the built in x64 emulation feature.

1. Ensure prerequisites are installed

   - [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/) (should be installed by default on recent Windows 10 or later)
   - [Git](https://github.com/git-guides/install-git#install-git-on-windows) (or `winget install git.git`)
   - [Docker](https://docs.docker.com/desktop/install/windows-install/) (or `winget install docker.dockerdesktop`)
     > **Note**
     > See [our LocalNet documentation](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/localnet.md#prerequisites) for more tips on installing Docker on Windows
   - [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

2. Install using winget

   ```shell
   winget install algokit
   ```

3. [Verify installation](#verify-installation)

### Maintenance

Some useful commands for updating or removing AlgoKit in the future.

- To update AlgoKit: `winget upgrade algokit`
- To remove AlgoKit: `winget uninstall algokit`

## Install AlgoKit on Mac

> **Note**
> AlgoKit is supported on macOS Big Sur (11) and later for both x64 and ARM (Apple Silicon)

1. Ensure prerequisites are installed

   - [Homebrew](https://docs.brew.sh/Installation)
   - [Git](https://github.com/git-guides/install-git#install-git-on-mac) (should already be available if `brew` is installed)
   - [Docker](https://docs.docker.com/desktop/install/mac-install/), (or `brew install --cask docker`)
     > **Note**
     > Docker requires MacOS 11+

2. Install using Homebrew

   ```shell
   brew install algorandfoundation/tap/algokit
   ```

3. Restart the terminal to ensure AlgoKit is available on the path
4. [Verify installation](#verify-installation)

### Maintenance

Some useful commands for updating or removing AlgoKit in the future.

- To update AlgoKit: `brew upgrade algokit`
- To remove AlgoKit: `brew uninstall algokit`

## Install AlgoKit on Linux

> **Note**
> AlgoKit is compatible with Ubuntu 16.04 and later, Debian, RedHat, and any distribution that supports [Snap](https://snapcraft.io/docs/installing-snapd), but it is only supported on x64 architecture; ARM is not supported.

1. Ensure prerequisites are installed

   - [Snap](https://snapcraft.io/docs/installing-snapd) (should be installed by default on Ubuntu 16.04.4 LTS (Xenial Xerus) or later)
   - [Git](https://github.com/git-guides/install-git#install-git-on-linux)
   - [Docker](https://docs.docker.com/desktop/install/linux-install/)

2. Install using snap

   ```shell
   sudo snap install algokit --classic
   ```

   > For detailed guidelines per each supported linux distro, refer to [Snap Store](https://snapcraft.io/algokit).

3. [Verify installation](#verify-installation)

### Maintenance

Some useful commands for updating or removing AlgoKit in the future.

- To update AlgoKit: `snap refresh algokit`
- To remove AlgoKit: `snap remove --purge algokit`

## Install AlgoKit with pipx on any OS

1. Ensure desired prerequisites are installed

   - [Python 3.10+](https://www.python.org/downloads/)
   - [pipx](https://pypa.github.io/pipx/installation/)
   - [Git](https://github.com/git-guides/install-git)
   - [Docker](https://docs.docker.com/get-docker/)

2. Install using pipx

   ```shell
   pipx install algokit
   ```

3. Restart the terminal to ensure AlgoKit is available on the path
4. [Verify installation](#verify-installation)

### Maintenance

Some useful commands for updating or removing AlgoKit in the future.

- To update AlgoKit: `pipx upgrade algokit`
- To remove AlgoKit: `pipx uninstall algokit`

## Verify installation

Verify AlgoKit is installed correctly by running `algokit --version` and you should see output similar to:

```
algokit, version 1.0.1
```

> **Note**
> If you get receive one of the following errors:
>
> - `command not found: algokit` (bash/zsh)
> - `The term 'algokit' is not recognized as the name of a cmdlet, function, script file, or operable program.` (PowerShell)
>
> Then ensure that `algokit` is available on the PATH by running `pipx ensurepath` and restarting the terminal.

It is also recommended that you run `algokit doctor` to verify there are no issues in your local environment and to diagnose any problems if you do have difficulties running AlgoKit. The output of this command will look similar to:

```
timestamp: 2023-03-27T01:23:45+00:00
AlgoKit: 1.0.1
AlgoKit Python: 3.11.1 (main, Dec 23 2022, 09:28:24) [Clang 14.0.0 (clang-1400.0.29.202)] (location: /Users/algokit/.local/pipx/venvs/algokit)
OS: macOS-13.1-arm64-arm-64bit
docker: 20.10.21
docker compose: 2.13.0
git: 2.37.1
python: 3.10.9 (location:  /opt/homebrew/bin/python)
python3: 3.10.9 (location:  /opt/homebrew/bin/python3)
pipx: 1.1.0
poetry: 1.3.2
node: 18.12.1
npm: 8.19.2
brew: 3.6.18

If you are experiencing a problem with AlgoKit, feel free to submit an issue via:
https://github.com/algorandfoundation/algokit-cli/issues/new
Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`
```

Per the above output, the doctor command output is a helpful tool if you need to ask for support or [raise an issue](https://github.com/algorandfoundation/algokit-cli/issues/new).

## Troubleshooting

This section addresses specific edge cases and issues that some users might encounter when interacting with the CLI. The following table provides solutions to known edge cases:

| Issue Description                                                                                                                                   | OS(s) with observed behaviour                             | Steps to mitigate                                                                                                                                                                                                                                                                                                                      | References                                          |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| This scenario may arise if installed `python` was build without `--with-ssl` flag enabled, causing pip to fail when trying to install dependencies. | Debian 12                                                 | Run `sudo apt-get install -y libssl-dev` to install the required openssl dependency. Afterwards, ensure to reinstall python with `--with-ssl` flag enabled. This includes options like [building python from source code](https://medium.com/@enahwe/how-to-06bc8a042345) or using tools like [pyenv](https://github.com/pyenv/pyenv). | <https://github.com/actions/setup-python/issues/93> |
| `poetry install` invoked directly or via `algokit project bootstrap all` fails on `Could NOT find PkgConfig (missing: PKG_CONFIG_EXECUTABLE)`.      | `MacOS` >=14 using `python` 3.13 installed via `homebrew` | Install dependencies deprecated in `3.13` and latest MacOS versions via `brew install pkg-config`, delete the virtual environment folder and retry the `poetry install` command invocation.                                                                                                                                            | N/A                                                 |
