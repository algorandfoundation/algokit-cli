# AlgoKit CLI

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network.

AlgoKit gets developers of all levels up and running with a familiar, fun and productive development environment in minutes. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

[Install AlgoKit](#install)

## Use Cases

- Building and deploying Algorand PyTEAL smart contracts

## Features

- [AlgoKit Bootstrap](docs/features/bootstrap.md) - Bootstrap AlgoKit project dependencies
- [AlgoKit Completions](docs/features/completions.md) - Install shell completions for AlgoKit
- [AlgoKit Doctor](docs/features/doctor.md) - Check AlgoKit installation and dependencies
- [AlgoKit Explore](docs/features/explore.md) - Explore Algorand Blockchains using Dappflow
- [AlgoKit Sandbox](docs/features/sandbox.md) - Manage a locally sandboxed private Algorand network

## Roadmap

This tool is currently in early development. Feel free to explore the repository and install the tool, but be aware that this is a work in progress and features may not be stable at this stage.

- Building and deploying Algorand dApps

## Guiding Principles

Algorand AlgoKit is guided by the following solution principles which flow through to the applications created by developers.

1. **Cohesive dev tool suite**: Using AlgoKit should feel professional and cohesive, like it was designed to work together, for the developer; not against them. Developers are guided towards delivering end-to-end, high quality outcomes on MainNet so they and Algorand are more likely to be successful.
2. **Seamless onramp**: New developers have a seamless experience to get started and they are guided into a pit of success with best practices, supported by great training collateral; you should be able to go from nothing to debugging code in 5 minutes.
3. **Leverage existing ecosystem**: AlgoKit functionality gets into the hands of Algorand developers quickly by building on top of the existing ecosystem wherever possible and aligned to these principles.
4. **Sustainable**: AlgoKit should be built in a flexible fashion with long-term maintenance in mind. Updates to latest patches in dependencies, Algorand protocol development updates, and community contributions and feedback will all feed in to the evolution of the software.
5. **Secure by default**: Include defaults, patterns and tooling that help developers write secure code and reduce the likelihood of security incidents in the Algorand ecosystem. This solution should help Algorand be the most secure Blockchain ecosystem.
6. **Extensible**: Be extensible for community contribution rather than stifling innovation, bottlenecking all changes through the Algorand Foundation and preventing the opportunity for other ecosystems being represented (e.g. Go, Rust, etc.). This helps make devs feel welcome and is part of the dev experience, plus it makes it easier to add features sustainably.
7. **Meet devs where they are**: Make Blockchain development mainstream by giving all developers an idiomatic development experience in the operating system, IDE and language they are comfortable with so they can dive in quickly and have less they need to learn before being productive.
8. **Modular components**: Solution components should be modular and loosely coupled to facilitate efficient parallel development by small, effective teams, reduced architectural complexity and allowing developers to pick and choose the specific tools and capabilities they want to use based on their needs and what they are comfortable with.

## Is this for me?

The target audience for this tool is software developers building applications on the Algorand network. A working knowledge of using a command line interfaces and experience using the supported programming languages is assumed.

## Contributing

This is an open source project managed by the Algorand Foundation. See the [contributing page](CONTRIBUTING.MD) to learn about making improvements to the CLI tool itself, including developer setup instructions.

# Install

## ⚠️ Beta Software ⚠️

**Work In Progress:** This tool is currently in the early stages of development, use at your own risk and please provide us feedback as you use it so we can make it better!

## Prerequisites

AlgoKit has some runtime dependencies that also need to be available for particular commands.

Note: You can install and use AlgoKit without these dependencies and AlgoKit will tell you if you are missing one for a given command.

- Git - Git is used when creating and updating projects from templates
- Docker - Docker is used to run the AlgoKit Sandbox environment

AlgoKit can be installed using OS specific package managers, or using the python tool [pipx](https://pypa.github.io/pipx/) see below for specific installation instructions.

- [Windows](#install-algokit-on-windows)
- [Mac](#install-algokit-on-mac)
- [Linux](#install-algokit-on-linux)
- [pipx](#install-algokit-with-pipx-on-any-os)

## Install AlgoKit on Windows

NOTE: this method will install the most recent python3 version through chocolatey. If you already have python installed, you may prefer to use `pipx install algokit` as explained [here](#install-algokit-with-pipx-on-any-os).

1. Ensure Prerequisites are installed

   - [Chocolatey](https://chocolatey.org/install)
   - [Git](https://github.com/git-guides/install-git#install-git-on-windows) (or `choco install git`)
   - [Docker](https://docs.docker.com/desktop/install/windows-install/) (or `choco install docker-desktop`)

2. Install using Chocolatey

   - Install AlgoKit: `choco install algokit`
   - Update AlgoKit: `choco upgrade algokit`
   - Remove AlgoKit: `choco uninstall algokit`

3. [Verify installation](#verify-installation)

## Install AlgoKit on Mac

NOTE: this method will install Python 3.10 as a dependency via Brew. If you already have python installed, you may prefer to use `pipx install algokit` as explained [here](#install-algokit-with-pipx-on-any-os).

1. Ensure Prerequisites are installed

   - [Brew](https://docs.brew.sh/Installation)
   - [Git](https://github.com/git-guides/install-git#install-git-on-mac) should already be available if brew is installed
   - [Docker](https://docs.docker.com/desktop/install/mac-install/) (or `brew install --cask docker-desktop`)

2. Install using Brew

   - Install AlgoKit: `brew install algorandfoundation/tap/algokit`
   - Update AlgoKit: `brew upgrade algokit`
   - Remove AlgoKit: `brew uninstall algokit`

3. [Verify installation](#verify-installation)

## Install AlgoKit on Linux

1. Ensure Prerequisites are installed

   - [Git](https://github.com/git-guides/install-git#install-git-on-linux)
   - [Docker](https://docs.docker.com/desktop/install/linux-install/)
   - [Python 3.10+](https://www.python.org/downloads/)

     NOTE: There is probably a better way to install Python than to download it directly, e.g. your local Linux package manager

   - [pipx](https://pypa.github.io/pipx/#on-linux-install-via-pip-requires-pip-190-or-later)

2. Continue with step 2 in the following section to install via [pipx](#install-algokit-with-pipx-on-any-os)

## Install AlgoKit with pipx on any OS

1. Ensure Prerequisites are installed

   - [Git](https://github.com/git-guides/install-git)
   - [Docker](https://docs.docker.com/get-docker/)
   - [Python 3.10+](https://www.python.org/downloads/)
   - [pipx](https://pypa.github.io/pipx/installation/)

2. Install using pipx

   - Install AlgoKit: `pipx install algokit`
   - Update AlgoKit: `pipx upgrade algokit`
   - Remove AlgoKit: `pipx uninstall algokit`

3. [Verify installation](#verify-installation)

## Verify installation

Verify AlgoKit is installed correctly by running `algokit --version` and you should see output similar to

```
algokit, version 0.8.0
```

It is also recommended to run `algokit doctor` to verify there are no issues in your local environment

```
timestamp: 2023-01-03T06:41:10+00:00
AlgoKit: 0.1.0
AlgoKit Python: 3.11.0 (main, Oct 26 2022, 19:06:18) [Clang 14.0.0 (clang-1400.0.29.202)] (location: /Users/algokit/.local/pipx/venvs/algokit)
OS: macOS-13.1-arm64-arm-64bit
docker: 20.10.21
docker compose: 2.13.0
git: 2.37.1
python: 3.10.9 (location:  /opt/homebrew/bin/python)
python3: 3.10.9 (location:  /opt/homebrew/bin/python3)
pipx: 1.1.0
poetry: 1.2.2
node: 18.12.1
npm: 8.19.2
brew: 3.6.16

If you are experiencing a problem with AlgoKit, feel free to submit an issue via:
https://github.com/algorandfoundation/algokit-cli/issues/new
Please include this output, if you want to populate this message in your clipboard, run `algokit doctor -c`
```
