# AlgoKit CLI for contributors

## Commits

We are using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary) standard for commit messages. This allows us to automatically generate release notes and version numbers. We do this via [Python Semantic Release](https://python-semantic-release.readthedocs.io/en/latest/) and [GitHub actions](.github/workflows/cd.yaml).

## Setup (AlgoKit CLI development)

### Initial setup

1. Clone this repository: `git clone https://github.com/algorandfoundation/algokit-cli`
2. Install pre-requisites:

   - Manually:
     - Install `Python` - [Link](https://www.python.org/downloads/): The minimum required version is `3.10`.
     - Install `Poetry` - [Link](https://python-poetry.org/docs/#installation): The minimum required version is `1.2`.
     - If you're not using PyCharm, then run `poetry install` in the root directory (this should set up `.venv` and install all Python dependencies - PyCharm will do this for you on startup)
   - Via automated script:

     - For your convenience, we provide an opinionated way to _quickly_ get the prerequisites up and running via pyenv and Poetry, which is handy if you are less familiar with Python or feeling lazy.
     - These scripts are idempotent and re-entrant so safe to run again and again if they come across a problem on your system that needs to get resolved to run them to completion.
     - To execute them:

       - Bash (e.g. Linux (Debian, Ubuntu) or Mac OSX): `./scripts/setup.sh`
       - Windows

         1. Ensure you have [Powershell Core (7+)](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.2) e.g. via `winget install --id Microsoft.Powershell --source winget` or `choco install pwsh -y`
         2. `./scripts/setup.ps1` (or if you want to confirm each step `./scripts/setup.ps1 -Confirm`)

     - These scripts will:

       - Install Python 3.10 if not present (via `pyenv`, after installing pyenv if it's not present)
       - Install Poetry (via `pyenv`)
       - Install Python dependencies and setup Python venv (to `./.venv/`) (via `poetry install`)
       - (On Windows, if you execute the script as admin) Set up `.venv/bin` as a symlink to `.venv/Scripts` to provide a consistent path to reference the Python interpreter (optional, makes for a slightly smoother getting started experience in VS Code)
       - 
3. Install pre-commit hooks (optional but recommended):

    [pre-commit](https://pre-commit.com/) is configured in this repository, so once `poetry install` has been run,
    execute `pre-commit install` inside the virtual-env, and git will ensure formatting, linting, and static typing (via `mypy`)
    is correct when you perform a commit.

4. Open the project and start debugging / developing via:

   - VS Code

     1. Open the repository root in VS Code
     2. Install recommended extensions
     3. Hit F5 (or whatever you have debug mapped to) and it should start running with breakpoint debugging

        (**NOTE:** The first time you run, VS Code may prompt you to select the Python Interpreter. Select python from the .venv path)

   - IDEA (e.g. PyCharm)
     1. Open the repository root in the IDE
     2. Hit Shift+F9 (or whatever you have debug mapped to) and it should start running with breakpoint debugging
   - Other
     1. Open the repository root in your text editor of choice
     2. In a terminal run `poetry shell`
     3. Run `./debug.py` through your debugger of choice
   - In each of the above cases, an `args.in` file will be created in the source root.
     Each line will be executed in order, with the arguments passed to the cli.
     For example, you could have:
     ```
     version
     --help
     version --help
     ```
     Not a terribly useful sequence of commands, but hopefully this helps illustrate the usage.

### Subsequently

1. If you update to the latest source code and there are new dependencies you will need to run `poetry install` again
2. Follow step 3 above

### Libraries and Tools

AlgoKit uses Python as a main language and many Python libraries and tools. This section lists all of them with a tiny brief.

- [Poetry](https://python-poetry.org/): Python packaging and dependency management.
- [pipx](https://github.com/pypa/pipx): Install and Run Python Applications in Isolated Environments
- [Click](https://palletsprojects.com/p/click/): A Python package for creating beautiful command line interfaces.
- [Black](https://github.com/psf/black): A Python code formatter.
- [Tox](https://tox.wiki/en/latest/): Automate and standardize testing in Python.

## Architecture decisions

As part of developing AlgoKit we are documenting key architecture decisions using [Architecture Decision Records (ADRs)](https://adr.github.io/). The following are the key decisions that have been made thus far:

- [2022-11-14: AlgoKit sandbox approach](docs/architecture-decisions/2022-11-14_sandbox-approach.md)
- [2022-11-22: Beaker testing strategy](docs/architecture-decisions/2022-11-22_beaker-testing-strategy.md)
