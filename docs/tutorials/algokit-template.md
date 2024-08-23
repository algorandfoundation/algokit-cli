# Creating AlgoKit Templates

This README serves as a guide on how to create custom templates for AlgoKit, a tool for initializing Algorand smart contract projects.
Creating templates in AlgoKit involves the use of various configuration files and a templating engine to generate project structures that are tailored to your needs.
This guide will cover the key concepts and best practices for creating templates in AlgoKit.
We will also refer to the official [`algokit-python-template`](https://github.com/algorandfoundation/algokit-python-template) as an example.

## Table of Contents

- [Quick Start](#quick-start)
- [Overview of AlgoKit Templates](#overview-of-algokit-templates)
  - [Copier/Jinja](#copierjinja)
  - [AlgoKit Functionality with Templates](#algokit-functionality-with-templates)
- [Key Concepts](#key-concepts)
  - [.algokit.toml](#algokittoml)
  - [Python Support: pyproject.toml](#python-support-pyprojecttoml)
  - [TypeScript Support: package.json](#typescript-support-packagejson)
  - [Bootstrap Option](#bootstrap-option)
  - [Predefined Copier Answers](#predefined-copier-answers)
  - [Default Behaviors](#default-behaviors)
  - [Generators](#generators)
- [Recommendations](#recommendations)
- [Conclusion](#conclusion)

## Quick Start

For users who are keen on getting started with creating AlgoKit templates, you can follow these quick steps:

1. Click on `Use this template`->`Create a new repository` on [algokit-python-template](https://github.com/algorandfoundation/algokit-python-template) Github page. This will create a new reference repository with clean git history, allowing you to start modifying and transforming the base python template into your own custom template.
2. Modify the cloned template according to your specific needs. You can refer to the remainder of this tutorial for an understanding of expected behaviors from the AlgoKit side, Copier - the templating framework, and key concepts related to the default files you will encounter in the reference template.

## Overview of AlgoKit Templates

AlgoKit templates are essentially project scaffolds that can be used to initialize new smart contract projects. These templates can include code files, configuration files, and scripts. AlgoKit uses Copier along with the Jinja templating engine to create new projects based on these templates.

### Copier/Jinja

AlgoKit uses Copier templates. Copier is a library that allows you to create project templates that can be easily replicated and customized. It's often used along with Jinja. Jinja is a modern and designer-friendly templating engine for Python programming language. It's used in Copier templates to substitute variables in files and file names. You can find more information in the [Copier documentation](https://copier.readthedocs.io/) and [Jinja documentation](https://jinja.palletsprojects.com/).

### AlgoKit Functionality with Templates

AlgoKit provides the `algokit init` command to initialize a new project using a template. You can either pass the template name using the `-t` flag or select a template from a list.

## Key Concepts

### .algokit.toml

This file is the AlgoKit configuration file for this project which can be used to specify the minimum version of the AlgoKit. This is essential to ensure that projects created with your template are always compatible with the version of AlgoKit they are using.

Example from `algokit-python-template`:

```toml
[algokit]
min_version = "v1.1.0-beta.4"
```

This specifies that the template requires at least version `v1.1.0-beta.4` of AlgoKit.

### Python Support: `pyproject.toml`

Python projects in AlgoKit can leverage a wide range of tools for dependency management and project configuration. While Poetry and the `pyproject.toml` file are common choices, they are not the only options.
If you opt to use Poetry, you'll rely on the pyproject.toml file to define the project's metadata and dependencies. This configuration file can utilize the Jinja templating syntax for customization.

Example snippet from `algokit-python-template`:

```toml
[tool.poetry]
name = "{{ project_name }}"
version = "0.1.0"
description = "Algorand smart contracts"
authors = ["{{ author_name }} <{{ author_email }}>"]
readme = "README.md"

...
```

This example shows how project metadata and dependencies are defined in `pyproject.toml`, using Jinja syntax to allow placeholders for project metadata.

### TypeScript Support: `package.json`

For TypeScript projects, the `package.json` file plays a similar role as `pyproject.toml` can do for Python projects. It specifies metadata about the project and lists the dependencies required for smart contract development.

Example snippet:

```json
{
  "name": "{{ project_name }}",
  "version": "1.0.0",
  "description": "{{ project_description }}",
  "scripts": {
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^4.2.4",
    "tslint": "^6.1.3",
    "tslint-config-prettier": "^1.18.0"
  }
}
```

This example shows how Jinja syntax is used within `package.json` to allow placeholders for project metadata and dependencies.

### Bootstrap Option

When instantiating your template via AlgoKit CLI it will optionally prompt the user to automatically run [algokit bootstrap](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/bootstrap.md) after the project is initialized and can perform various setup tasks like installing dependencies or setting up databases.

- `env`: Searches for and copies an `.env*.template` file to an equivalent `.env*` file in the current working directory, prompting for any unspecified values. This feature is integral for securely managing environment variables, as it prevents sensitive data from inadvertently ending up in version control.
  By default, Algokit will scan for network-prefixed `.env` variables (e.g., `.env.localnet`), which can be particularly useful when relying on the [Algokit deploy command](https://github.com/algorandfoundation/algokit-cli/blob/deploy-command/docs/features/deploy.md). If no such prefixed files are located, Algokit will then attempt to load default `.env` files. This functionality provides greater flexibility for different network configurations.

- `poetry`: If your Python project uses Poetry for dependency management, the `poetry` command installs Poetry (if not present) and runs `poetry install` in the current working directory to install Python dependencies.
- `npm`: If you're developing a JavaScript or TypeScript project, the `npm` command runs npm install in the current working directory to install Node.js dependencies.
- `all`: The `all` command runs all the aforementioned bootstrap sub-commands in the current directory and its subdirectories. This command is a comprehensive way to ensure all project dependencies and environment variables are properly set up.

### Predefined Copier Answers

When initializing a new project, Copier can prompt the user for input, which is then passed to the template as variables. This is useful for customizing the new project based on user input.

Example:

```yaml
# copier.yaml
project_name:
  type: str
  help: What is the name of this project.
  placeholder: "algorand-app"
```

This would prompt the user for the project name, and the input can then be used in the template using the Jinja syntax `{{ project_name }}`.

#### Default Behaviors

When creating an AlgoKit template, there are a few default behaviors that you can expect to be provided by algokit-cli itself without introducing any extra code to your templates:

- **Git**: If Git is installed on the user's system and the user's working directory is a Git repository, AlgoKit CLI will commit the newly created project as a new commit in the repository. This feature helps to maintain a clean version history for the project. If you wish to add a specific commit message for this action, you can specify a `commit_message` in the `_commit` option in your `copier.yaml` file.

- **VSCode**: If the user has Visual Studio Code (VSCode) installed and the path to VSCode is added to their system's PATH, AlgoKit CLI will automatically open the newly created VSCode window unless user provides specific flags into the init command.

- **Bootstrap**: AlgoKit CLI is equipped to execute a bootstrap script after a project has been initialized. This script, included in AlgoKit templates, can be automatically run to perform various setup tasks, such as installing dependencies or setting up databases. This is managed by AlgoKit CLI and not within the user-created codebase. By default, if a `bootstrap` task is defined in the `copier.yaml`, AlgoKit CLI will execute it, unless the user opts out during the prompt.

By combining predefined Copier answers with these default behaviors, you can create a smooth, efficient, and intuitive initialization experience for the users of your template.

### Executing Python Tasks in Templates

If you need to use Python scripts as tasks within your Copier templates, ensure that you have Python installed on the host machine.
By convention, AlgoKit automatically detects the Python installation on your machine and fills in the `python_path` variable accordingly.
This process ensures that any Python scripts included as tasks within your Copier templates will execute using the system's Python interpreter.
It's important to note that the use of `_copier_python` is not recommended. Here's an example of specifying a Python script execution in your `copier.yaml` without needing to explicitly use `_copier_python`:

```yaml
- "{{ python_path }} your_python_script.py"
```

If you'd like your template to be backwards compatible with versions of `algokit-cli` older than `v1.11.3` when executing custom python scripts via `copier` tasks, you can use a conditional statement to determine the Python path:

```yaml
- "{{ python_path if python_path else _copier_python }} your_python_script.py"
# _copier_python above is used for backwards compatibility with versions < v1.11.3 of the algokit cli
```

And to define `python_path` in your Copier questions:

```yaml
# Auto determined by algokit-cli from v1.11.3 to allow execution of python script
# in binary mode.
python_path:
  type: str
  help: Path to the sys.executable.
  when: false
```

### Working with Generators

After mastering the use of `copier` and building your templates based on the official AlgoKit template repositories, you can enhance your proficiency by learning to define `custom generators`. Essentially, generators are smaller-scope `copier` templates designed to provide additional functionality after a project has been initialized from the template.

For example, the official [`algokit-python-template`](https://github.com/algorandfoundation/algokit-python-template/tree/main/template_content) incorporates a generator in the `.algokit/generators` directory. This generator can be utilized to execute auxiliary tasks on AlgoKit projects that are initiated from this template, like adding new smart contracts to an existing project. For a comprehensive understanding, please consult the [`architecture decision record`](../architecture-decisions/2023-07-19_advanced_generate_command.md) and [`algokit generate documentation`](../features/generate.md).

#### How to Create a Generator

Outlined below are the fundamental steps to create a generator. Although `copier` provides complete autonomy in structuring your template, you may prefer to define your generator to meet your specific needs. Nevertheless, as a starting point, we suggest:

1. Generate a new directory hierarchy within your template directory under the `.algokit/generators` folder (this is merely a suggestion, you can define your custom path if necessary and point to it via the algokit.toml file).
2. Develop a `copier.yaml` file within the generator directory and outline the generator's behavior. This file bears similarities with the root `copier.yaml` file in your template directory, but it is exclusively for the generator. The `tasks` section of the `copier.yaml` file is where you can determine the generator's behavior. Here's an example of a generator that copies the `smart-contract` directory from the template to the current working directory:

```yaml
_task:
  - "echo '==== Successfully initialized new smart contract 🚀 ===='"

contract_name:
  type: str
  help: Name of your new contract.
  placeholder: "my-new-contract"
  default: "my-new-contract"

_templates_suffix: ".j2"
```

Note that `_templates_suffix` must be different from the `_templates_suffix` defined in the root `copier.yaml` file. This is because the generator's `copier.yaml` file is processed separately from the root `copier.yaml` file.

3. Develop your `generator` copier content and, when ready, test it by initiating a new project for your template and executing the generator command:

```bash
algokit generate
```

This should dynamically load and display your generator as an optional `cli` command that your template users can execute.

## Recommendations

- **Modularity**: Break your templates into modular components that can be combined in different ways.
- **Documentation**: Include README files and comments in your templates to explain how they should be used.
- **Versioning**: Use `.algokit.toml` to specify the minimum compatible version of AlgoKit.
- **Testing**: Include test configurations and scripts in your templates to encourage testing best practices.
- **Linting and Formatting**: Integrate linters and code formatters in your templates to ensure code quality.
- **Algokit Principle**: for details on generic principles on designing templates refer to [algokit design principles](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles).

## Conclusion

Creating custom templates in AlgoKit is a powerful way to streamline your development workflow for Algorand smart contracts, whether you are using Python or TypeScript. Leveraging Copier and Jinja for templating, and incorporating best practices for modularity, documentation, and coding standards, can result in robust, flexible, and user-friendly templates that can be a valuable asset to both your own projects and the broader Algorand community.

Happy coding!
