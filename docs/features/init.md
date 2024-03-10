# AlgoKit Init

The `algokit init` [command](../cli/index.md#init) is used to quickly initialize new projects using official Algorand Templates or community provided templates. It supports a fully guided command line wizard experience, as well as fully scriptable / non-interactive functionality via command options.

## Quick start

For a quick start template with all of the defaults you can run: `algokit init` which will interactively guide you through picking the right stack to build your AlgoKit project. Afterwards, you should immediately be able to hit F5 to compile the hello world smart contract to the `smart_contracts/artifacts` folder (with breakpoint debugging - try setting a breakpoint in `smart_contracts/helloworld.py`) and open the `smart_contracts/helloworld.py` file and get linting, automatic formatting and syntax highlighting.

## Prerequisites

Git is a prerequisite for the init command as it is used to clone templates and initialize git repos. Please consult the [README](../../README.md#prerequisites) for installation instructions.

## Functionality

As outlined in [quick start](#quick-start), the simplest use of the command is to just run `algokit init` and you will then be guided through selecting a template and configuring options for that template. e.g.

```
$ ~ algokit init
? Which of these options best describes the project you want to start? `Smart Contract` | `Dapp Frontend` | `Smart Contract & Dapp Frontend` | `Custom`
? Name of project / directory to create the project in:  my-cool-app
```

Once above 2 questions are answered, the `cli` will start instantiating the project and will start asking questions specific to the template you are instantiating. By default official templates such as `puya`, `fullstack`, `react`, `beaker` include a notion of a `preset`. If you want to skip all questions and let the tool preset the answers tailored for a starter project you can pick `Starter`, for a more advanced project that includes unit tests, CI automation and other advanced features, pick `Production`. Lastly, if you prefer to modify the experience and tailor the template to your needs, pick the `Custom` preset.

If you want to accept the default for each option simply hit [enter] or alternatively to speed things up you can run `algokit init --defaults` and they will be auto-accepted.

### Workspaces vs Standalone Projects

AlgoKit supports two distinct project structures: Workspaces and Standalone Projects. This flexibility allows developers to choose the most suitable approach for their project's needs.

### Workspaces

Workspaces are designed for managing multiple related projects under a single root directory. This approach is beneficial for complex applications that consist of multiple sub-projects, such as a smart contract and a corresponding frontend application. Workspaces help in organizing these sub-projects in a structured manner, making it easier to manage dependencies and shared configurations.

To initialize a project within a workspace, use the `--workspace` flag. If a workspace does not already exist, AlgoKit will create one for you by default (unless you disable it via `--no-workspace` flag). Once established, new projects can be added to this workspace, allowing for centralized management.

To mark your project as `workspace` fill in the following in your `.algokit.toml` file:

```toml
[project]
type = 'workspace' # type specifying if the project is a workspace or standalone
projects_root_path = 'projects' # path to the root folder containing all sub-projects in the workspace
```

#### GitHub folder merging

When using the `--workspace` flag with AlgoKit's init command, it enables a workspace setup, ideal for handling multiple projects under one directory. This setup is especially useful for complex applications that involve different components like smart contracts and frontend applications.

#### Handling of the `.github` Folder

A key aspect of using the `--workspace` flag is how the `.github` folder is managed. This folder, which contains GitHub-specific configurations such as workflows and issue templates, is moved from the project directory to the root of the workspace. This move is necessary because GitHub does not recognize workflows located in subdirectories.

Here's a simplified overview of what happens:

1. If a `.github` folder is found in your project, its contents are transferred to the workspace's root `.github` folder.
2. Files with matching names in the destination are not overwritten; they're skipped.
3. The original `.github` folder is removed if it's left empty after the move.
4. A notification is displayed, advising you to review the moved `.github` contents to ensure everything is in order.

This process ensures that your GitHub configurations are properly recognized at the workspace level, allowing you to utilize GitHub Actions and other features seamlessly across your projects.

### Standalone Projects

Standalone projects are suitable for simpler applications or when working on a single component. This structure is straightforward, with each project residing in its own directory, independent of others. Standalone projects are ideal for developers who prefer simplicity or are focusing on a single aspect of their application and are sure that they will not need to add more sub-projects in the future.

To create a standalone project, use the `--no-workspace` flag during initialization. This instructs AlgoKit to bypass the workspace structure and set up the project as an isolated entity.

Both workspaces and standalone projects are fully supported by AlgoKit's suite of tools, ensuring developers can choose the structure that best fits their workflow without compromising on functionality.

To mark your project as a standalone project fill in the following in your `.algokit.toml` file:

```toml
[project]
type = {'backend' | 'contract' | 'frontend'} # currently support 3 generic categories for standalone projects
name = 'my-project' # unique name for the project inside workspace
```

> We recommend using workspaces for most projects (hence enabled by default), as it provides a more organized and scalable approach to managing multiple sub-projects. However, standalone projects are a great choice for simple applications or when you are certain that you will not need to add more sub-projects in the future, for such cases simply append `--no-workspace` when using `algokit init` command.

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
➡️ https://github.com/algorandfoundation/algokit-beaker-default-template
As a suggestion, if you wanted to open the project in VS Code you could execute:

> cd my-smart-contract && code .

```

After bootstrapping you are also given the opportunity to initialize a git repo, upon successful completion of the init command the project is ready to be used. If you pass in `--git` it will automatically initialise the git repository and if you pass in `--no-git` it won't.

> Please note, when using `--no-workspaces`, algokit init will assume a max lookup depth of 1 for a fresh template based project. Otherwise it will assume a max depth of 2, since default algokit workspace structure is at most 2 levels deep.

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
Please inspect the template repository, and pay particular attention to the values of \_tasks, \_migrations and \_jinja_extensions in copier.yml
? Continue anyway? Yes

```

If you want to create a community template, you can use the [AlgoKit guidelines on template building](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/tutorials/algokit-template.md#creating-algokit-templates) and [Copier documentation](https://copier.readthedocs.io/en/stable/) as a starting point.

## Template Answers

Answers to specific template prompts can be provided with the `--answer {key} {value}` option, which can be used multiple times for each prompt. Quotes can be used for values with spaces e.g. `--answer author_name "Algorand Foundation"`.

To find out the key for a specific answer you can either look at `.copier-answers.yml` in the root folder of a project created via `algokit init` or in the `copier.yaml` file of a template repo e.g. for the [beaker template](https://github.com/algorandfoundation/algokit-beaker-default-template/blob/main/copier.yaml).

## Non-interactive project initialization

By combining a number of options, it is possible to initialize a new project without any interaction. For example, to create a project named `my-smart-contract` using the `beaker` template with no git, no bootstrapping, the author name of `Algorand Foundation`, and defaults for all other values, you could execute the following:

```

$ ~ algokit init -n my-smart-contract -t puya --no-git --no-bootstrap --answer author_name "Algorand Foundation" --defaults
🙌 Project initialized at `my-smart-contract`! For template specific next steps, consult the documentation of your selected template 🧐
Your selected template comes from:
➡️ https://github.com/algorandfoundation/algokit-beaker-default-template
As a suggestion, if you wanted to open the project in VS Code you could execute:

> cd my-smart-contract && code .

```

For more details about the `AlgoKit init` command, please refer to the [AlgoKit CLI reference documentation](../cli/index.md#init).

```

```

```

```

```

```
