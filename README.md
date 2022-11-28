# AlgoKit CLI

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network.

AlgoKit gets developers of all levels up and running with a familiar, fun and productive development environment in minutes. The goal of AlgoKit is to help developers build and launch secure, automated production-ready applications rapidly.

## Use Cases

- Building and deploying Algorand PyTEAL smart contracts

## Features

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

# User Guide

## ⚠️ Pre-Alpha Software ⚠️

**Work In Progress:** This guide is an initial version targeted at developing the CLI tool itself. The structure of this guide will change over time to be more end user focused. We anticipate this guide will eventually get an end user running AlgoKit CLI with the most basic commands. It will then link out to separate Algorand foundation documentation for a full user guide.

**This software may break your computer or (more likely) just not do anything useful yet and be a general pain to install.**

Still not deterred?

Here's how to test it out and maybe even start hacking, assuming you have access to this repo.

### Install

1. Ensure [Python](https://www.python.org/downloads/) 3.10 or higher is installed on your system and available on your `PATH`
   - Note there is probably a better way to install Python than to download it directly, e.g. your friendly local Linux package manager, Homebrew on macOS, chocolatey on Windows
2. Install [pipx](https://pypa.github.io/pipx/)
   - Make sure to follow _all_ the instructions for your OS, there will be two commands, the first to install, and the second to ensure your path is setup so you can execute `pipx`. Make sure to read the output of this second command as well, as it'll probably tell you to relaunch your terminal.
3. Either:

   - Install via Git:

     1. `pipx install git+https://github.com/algorandfoundation/algokit-cli`
        - You can specify a tag using appending i.e. `pipx install git+https://github.com/algorandfoundation/algokit-cli@v.13-beta`
        - If you have trouble running this check you can execute `git clone https://github.com/algorandfoundation/algokit-cli`
        - In the future, when this is published publicly you will be able to simply execute `pipx install algokit`
     2. You can now run `algokit` and should see a help message! 🎉

   - Install via source:

     1. Checkout this repository e.g. with git clone
     2. Ensure you have Poetry installed
     3. Run `poetry build` in the checkout (you shouldn't need to activate the venv first). This will output a "source distribution" (a tar.gz file) and a "binary distribution" (a .whl file) in the `dist/` directory.
     4. Run `pipx install ./dist/algokit-<TAB>-<TAB>` (ie the .whl file)
     5. You can now run `algokit` and should see a help message! 🎉

### Update

To update a previous algokit installation you can simply run `pipx reinstall algokit` and it'll grab the latest from wherever it was installed from. Note: If you installed a specific version e.g. `pipx install git+https://github.com/algorandfoundation/algokit-cli@v.13-beta` then this command won't have any effect since that repository tag will point to the same version.
