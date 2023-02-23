# AlgoKit Init

The `algokit init` [command](../cli/index.md#init) is used to quickly initialize new projects using official Algorand Templates or community provided templates. It supports a fully guided command line wizard experience, as well as fully scriptable / non-interactive functionality via command options.

## Quick start

For a quick start template with all of the defaults you can run: `algokit init --name my_project --template beaker --git --defaults` and then you can run `cd my_project && code .` and you should immediately be able to hit F5 to compile the hello world smart contract to the `smart_contracts/artifacts` folder (with breakpoint debugging - try setting a breakpoint in `smart_contracts/helloworld.py`) and open the `smart_contracts/helloworld.py` file and get linting, automatic formatting and syntax highlighting.

## Prerequisites

Git is a prerequisite for the init command as it is used to clone templates and initialize git repos. Please consult the [README](../../README.md#prerequisites) for installation instructions.

## Functionality

The simplest use of the command is to just run `algokit init` and you will then be guided through selecting a template and configuring options for that template. e.g.

```
$ ~ algokit init
? Name of project / directory to create the project in:  my-smart-contract
? Select a project template:  beaker
🎤 Package author name
   Algorand Foundation
🎤 Package author email
   info@algorand.foundation
🎤 Do you want to add VSCode configuration?
   Yes
🎤 Do you want to use a Python linter?
   Ruff
🎤 Do you want to use a Python formatter (via Black)?
   Yes
🎤 Do you want to use a Python type checker (via mypy)?
   Yes
🎤 Do you want to include unit tests (via pytest)?
   Yes
🎤 Do you want to include Python dependency vulnerability scanning (via pip-audit)?
   Yes
```

If you want to accept the default for each option simply hit [enter] or alternatively to speed things up you can run `algokit init --defaults` and they will be auto-accepted.

## Bootstrapping

You will also be prompted if you wish to run the [bootstrap](../cli/index.md#bootstrap) command, this is useful if you plan to immediately begin developing in the new project. If you passed in `--defaults` or `--bootstrap` then it will automatically run bootstrapping unless you passed in `--no-bootstrap`.

```
? Do you want to run `algokit bootstrap` to bootstrap dependencies for this new project so it can be run immediately? Yes
Installing Python dependencies and setting up Python virtual environment via Poetry
poetry: Creating virtualenv my-smart-contract in /Users/algokit/algokit-init/my-smart-contract/.venv
poetry: Updating dependencies
poetry: Resolving dependencies...
poetry:
poetry: Writing lock file
poetry:
poetry: Package operations: 53 installs, 0 updates, 0 removals
poetry:
poetry: • Installing pycparser (2.21)

---- other output omitted for brevity ----

poetry: • Installing ruff (0.0.171)
Copying /Users/algokit/algokit-init/my-smart-contract/smart_contracts/.env.template to /Users/algokit/algokit-init/my-smart-contract/smart_contracts/.env and prompting for empty values
? Would you like to initialise a git repository and perform an initial commit? Yes
🎉 Performed initial git commit successfully! 🎉
🙌 Project initialized at `my-smart-contract`! For template specific next steps, consult the documentation of your selected template 🧐
Your selected template comes from:
➡️  https://github.com/algorandfoundation/algokit-beaker-default-template
As a suggestion, if you wanted to open the project in VS Code you could execute:
> cd my-smart-contract && code .
```

After bootstrapping you are also given the opportunity to initialize a git repo, upon successful completion of the init command the project is ready to be used. If you pass in `--git` it will automatically initialise the git repository and if you pass in `--no-git` it won't.

## Options

There are a number of options that can be used to provide answers to the template prompts. Some of the options requiring further explanation are detailed below, but consult the CLI reference for all available [options](../cli/index.md#init).

## Community Templates

As well as the official Algorand templates shown when running the init command, community templates can also be provided by providing a URL via the prompt or the `--template-url` option.

e.g. `algokit init --template-url https://github.com/algorandfoundation/algokit-beaker-default-template` (that being the url of the official beaker template, the same as `algokit init -t beaker`).

The `--template-url` option can be combined with `--template-url-ref` to specify a specific commit, branch or tag 

e.g. `algokit init --template-url https://github.com/algorandfoundation/algokit-beaker-default-template --template-url-ref 9985005b7389c90c6afed685d75bb8e7608b2a96` 

If the URL is not an official template there is a potential security risk and so to continue you must either acknowledge this prompt, or if you are in a non-interactive environment you can pass the `--UNSAFE-SECURITY-accept-template-url` option (but we generally don't recommend this option so users can review the warning message first) e.g.

```
Community templates have not been reviewed, and can execute arbitrary code.
Please inspect the template repository, and pay particular attention to the values of _tasks, _migrations and _jinja_extensions in copier.yml
? Continue anyway? Yes
```

If you want to create a community template, you can use the [beaker template](https://github.com/algorandfoundation/algokit-beaker-default-template) and [Copier documentation](https://copier.readthedocs.io/en/stable/) as a starting point.

## Template Answers

Answers to specific template prompts can be provided with the `--answer {key} {value}` option, which can be used multiple times for each prompt. Quotes can be used for values with spaces e.g. `--answer author_name "Algorand Foundation"`.

To find out the key for a specific answer you can either look at `.copier-answers.yml` in the root folder of a project created via `algokit init` or in the `copier.yaml` file of a template repo e.g. for the [beaker template](https://github.com/algorandfoundation/algokit-beaker-default-template/blob/main/copier.yaml).

## Non-interactive project initialization

By combining a number of options, it is possible to initialize a new project without any interaction. For example, to create a project named `my-smart-contract` using the `beaker` template with no git, no bootstrapping, the author name of `Algorand Foundation`, and defaults for all other values, you could execute the following:

```
$ ~ algokit init -n my-smart-contract -t beaker --no-git --no-bootstrap --answer author_name "Algorand Foundation" --defaults
🙌 Project initialized at `my-smart-contract`! For template specific next steps, consult the documentation of your selected template 🧐
Your selected template comes from:
➡️  https://github.com/algorandfoundation/algokit-beaker-default-template
As a suggestion, if you wanted to open the project in VS Code you could execute:
> cd my-smart-contract && code .
```

For more details about the `AlgoKit init` command, please refer to the [AlgoKit CLI reference documentation](../cli/index.md#init).
