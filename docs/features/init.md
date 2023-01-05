# AlgoKit Init

The `algokit init` [command](../cli/index.md#init) is used to quickly initialize new projects using official Algorand Templates or community provided templates. It supports a fully guided command line experience, as well as non-interactive functionality via command options.

## Prerequisites
Git is a prerequisite for the init command as it is used to clone templates and initialize git repos. Please consult the [README](../../README.md#install) for install instructions.

## Functionality

The simplest use of the command is to just run `algokit init` and you will then be guided through selecting a template and configuring options for that template e.g.

```
? Name of project / directory to create the project in:  my-smart-contract
? Select a project template:  beaker
🎤 Package author name
   Algorand Foundation
🎤 Package author email
   al@algorand.foundation
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

You will also be prompted if you wish to run the [bootstrap](../cli/index.md#bootstrap) command, this is useful if you plan to immediately begin developing in the new project.

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

After bootstrapping you are also given the opportunity to initialize a git repo, upon successful completion of the init command the project is ready to be used.

## Options

There are a number of options that can be used to provide answers to the template prompts. Some of the options requiring further explanation are detailed below, but consult the CLI reference for all available [options](../cli/index.md#options-5)

### Community Templates

As well as the official Algorand templates shown when running the init command, community templates can also be provided by providing a URL via the prompt or the `--template-url` option.

If the URL is not an official template there is a potential security risk and so to continue you must either acknowledge this prompt, or pass the `--UNSAFE-SECURITY-accept-template-url` option e.g.

```
Community templates have not been reviewed, and can execute arbitrary code.
Please inspect the template repository, and pay particular attention to the values of _tasks, _migrations and _jinja_extensions in copier.yml
? Continue anyway? Yes
```

or `algokit init --template-url https://github.com/algorandfoundation/algokit-beaker-default-template --UNSAFE-SECURITY-accept-template-url`

### Answers

Answers to specific template prompts can be provided with the `--answer key value` option, which can be used multiple times for each prompt. Quotes can be used for values with spaces e.g. `--answer author_name "Algorand Foundation"`

To find out the key for a specific answer you can either look at `.copier-answers.yml` in the root folder of a project created via `algokit init` or in the `copier.yaml` file of a template repo e.g. for the [beaker template](https://github.com/algorandfoundation/algokit-beaker-default-template/blob/main/copier.yaml)

## Non-interactive project initialization

By combining a number of options it is possible to initialize a new project without any interaction. For example to create a project named `my-smart-contract` using the `beaker` template, no git, no bootstrapping, the author name of `Algorand Foundation`, and defaults for all other values you could execute the following.

`algokit init -n my-smart-contract -t beaker --no-git --no-bootstrap --answer author_name "Algorand Foundation" --defaults`

Which outputs

```
🙌 Project initialized at `my-smart-contract`! For template specific next steps, consult the documentation of your selected template 🧐
Your selected template comes from:
➡️  https://github.com/algorandfoundation/algokit-beaker-default-template
As a suggestion, if you wanted to open the project in VS Code you could execute:
> cd my-smart-contract && code .
```
