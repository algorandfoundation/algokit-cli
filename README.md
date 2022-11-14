# AlgoKit CLI

The Algorand AlgoKit CLI is the one-stop shop tool for developers building on the Algorand network.

AlgoKit CLI gets developers of all levels up and running with a familiar, fun and productive development environment in five minutes. It helps developers build and launch secure, fully automated production ready applications in weeks rather than months.

## Use Cases

TODO: List some example user stories

## Roadmap

This tool is currently in early development. Feel free to explore the repository and install the tool, but be aware that this is a work in progress and features may not be stable at this stage.

TODO: list outcomes as intended features and basic summary of each

## Guiding Principles

Algorand AlgoKit CLI is guided by the following solution principles which flow through to the applications created by developers.

1. **Cohesive dev tool suite**: Using AlgoKit should feel professional and cohesive, like it was designed to work together, for the developer; not against them. Developers are guided towards delivering end-to-end, high quality outcomes on MainNet so they and Algorand are more likely to be successful.
1. **Seamless onramp**: New developers have a seamless experience to get started and they are guided into a pit of success with best practices, supported by great training collateral; you should be able to go from nothing to debugging code in 5 minutes.
1. **Leverage existing ecosystem**: AlgoKit functionality gets into the hands of Algorand developers quickly by building on top of the existing ecosystem wherever possible and aligned to these principles.
1. **Sustainable**: Software ages like fish (not wine) - it needs to be maintained. Updates to latest patches, match Algorand protocol development and accept community contributions and feedback are all important. The solution has to have a plan for long-term sustainability.
1. **Secure by default**: Include defaults, patterns and tooling (e.g. static analysis, mnemonic handling) that help developers write secure code and reduce the likelihood of security incidents in the Algorand ecosystem. This solution should help Algorand be the most secure Blockchain ecosystem.
1. **Extensible**: Be extensible for community contribution rather than stifling innovation, bottlenecking all changes through the Algorand Foundation and preventing the opportunity for other ecosystems being represented (e.g. Go, Rust, etc.). This helps make devs feel welcome and is part of the dev experience, plus it makes it easier to add features sustainably.
1. **Meet devs where they are**: Make Blockchain development mainstream by giving all developers an idiomatic development experience in the operating system, IDE and language they are comfortable with so they can dive in quickly and have less they need to learn before being productive.
1. **Modular components**: Solution components should be modular and loosely coupled to facilitate efficient parallel development by small, effective teams, reduced architectural complexity and allowing developers to pick and choose the specific tools and capabilities they want to use based on their needs and what they are comfortable with.

## Is this for me?

The target audience for this tool is software developers building applications on the Algorand network. A working knowledge of using a command line interfaces and experience using the supported programming languages is assumed.

## Contributing

This is an open source project managed by the Algorand Foundation. See the [contributing page](CONTRIBUTING.MD) to learn about making improvements to the CLI tool itself.

# User Guide

## ⚠️ Pre-Alpha Software ⚠️

### This software may break your computer or (more likely) just not do anything useful yet and be a general pain to install.

Still not deterred?

Here's how to test it out and maybe even start hacking, assuming you have access to this repo.

### Install

1. Ensure [Python](https://www.python.org/downloads/) 3.10 or higher is installed on your system and available on your `PATH`
   - Note there is probably a better way to install Python than to download it directly, e.g. your friendly local Linux package manager, Homebrew on macOS, chocolatey on Windows
2. Install [pipx](https://pypa.github.io/pipx/)
   - Make sure to follow _all_ the instructions for your OS, there will be two commands, the first to install, and the second to ensure your path is setup. Make sure to read the output of this second command as well, as it'll probably tell you to relaunch your terminal.
3. Checkout this repo e.g. with git clone
4. If you want to start hacking on algokit-cli, run `poetry install` to install dependencies (including dev dependencies) and activate the virtual environment it creates in `.venv` in your checkout (you can run `poetry shell` or just activate it directly if you know what you're doing). If you're using an IDE it should probably do that for you though.
5. Optionally, if you want to rest running `algokit`, then:
   1. Run `poetry build` in the checkout (you shouldn't need to activate the venv first). This will output a "source distribution" (a tar.gz file) and a "binary distribution" (a .whl file) in the `dist/` directory.
   2. Run `pipx install ./dist/algokit-<TAB>-<TAB>` (ie the .whl file)
   3. You can now run `algokit` and should see a help message! 🎉
