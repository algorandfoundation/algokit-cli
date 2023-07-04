# Creating AlgoKit Templates

This README serves as a guide on how to create custom templates for AlgoKit, a tool for initializing Algorand smart contract projects. 
Creating templates in AlgoKit involves the use of various configuration files and a templating engine to generate project structures that are tailored to your needs.
This guide will cover the key concepts and best practices for creating templates in AlgoKit.
We will also refer to the official [`algokit-beaker-default-template`](https://github.com/algorandfoundation/algokit-beaker-default-template) as an example.
## Table of Contents

- [Overview of AlgoKit Templates](#overview-of-algokit-templates)
  - [Copier/Jinja](#copierjinja)
  - [AlgoKit Functionality with Templates](#algokit-functionality-with-templates)
- [Key Concepts](#key-concepts)
  - [.algokit.toml](#algokittoml)
  - [Python Support: pyproject.toml](#python-support-pyprojecttoml)
  - [TypeScript Support: package.json](#typescript-support-packagejson)
  - [Bootstrap Option](#bootstrap-option)
  - [Template Answers and Variables](#template-answers-and-variables)
- [Recommendations](#recommendations)
- [Conclusion](#conclusion)

## Overview of AlgoKit Templates

AlgoKit templates are essentially project scaffolds that can be used to initialize new smart contract projects. These templates can include code files, configuration files, and scripts. AlgoKit uses Copier along with the Jinja templating engine to create new projects based on these templates.

### Copier/Jinja

AlgoKit uses Copier templates. Copier is a library that allows you to create project templates that can be easily replicated and customized. It's often used along with Jinja. Jinja is a modern and designer-friendly templating engine for Python programming language. It's used in Copier templates to substitute variables in files and file names. You can find more information in the [Copier documentation](https://copier.readthedocs.io/) and [Jinja documentation](https://jinja.palletsprojects.com/).

### AlgoKit Functionality with Templates

AlgoKit provides the `algokit init` command to initialize a new project using a template. You can either pass the template name using the `-t` flag or select a template from a list. 

## Key Concepts

### .algokit.toml

This file is the AlgoKit configuration file for this project which can be used to specify the minimum version of the AlgoKit. This is essential to ensure that projects created with your template are always compatible with the version of AlgoKit they are using.

Example from `algokit-beaker-default-template`:
```toml
[algokit]
min_version = "v1.1.0-beta.4"
```
This specifies that the template requires at least version `v1.1.0-beta.4` of AlgoKit.

### Python Support: `pyproject.toml`

Python projects in AlgoKit can leverage a wide range of tools for dependency management and project configuration. While Poetry and the `pyproject.toml` file are common choices, they are not the only options.
If you opt to use Poetry, you'll rely on the pyproject.toml file to define the project's metadata and dependencies. This configuration file can utilize the Jinja templating syntax for customization.


Example snippet from `algokit-beaker-default-template`:

```toml
[tool.poetry]
name = "{{ project_name }}"
version = "0.1.0"
description = "Algorand smart contracts"
authors = ["{{ author_name }} <{{ author_email }}>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
beaker-pyteal = "^1.0.0"
algokit-utils = "^1.3"
python-dotenv = "^1.0.0"
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

AlgoKit templates can include a bootstrap script. This script is automatically run after the project is initialized and can perform various setup tasks like installing dependencies or setting up databases.

- `env`: Copies an `.env.template` file to `.env` in the current working directory and prompts for any unspecified values. This is a critical aspect of managing environment variables securely, ensuring that sensitive data doesn't accidentally end up in version control.
- `poetry`: If your Python project uses Poetry for dependency management, the `poetry` command installs Poetry (if not present) and runs `poetry install` in the current working directory to install Python dependencies.
- `npm`: If you're developing a JavaScript or TypeScript project, the `npm` command runs npm install in the current working directory to install Node.js dependencies.
- `all`: The `all` command runs all the aforementioned bootstrap sub-commands in the current directory and its subdirectories. This command is a comprehensive way to ensure all project dependencies and environment variables are properly set up.

### Predefined copier answers

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
When creating an AlgoKit template, there are a few default behaviors that you can include to improve the development experience:

- **Git**: If Git is installed on the user's system and the user's working directory is a Git repository, Copier will commit the newly created project as a new commit in the repository. This feature helps to maintain a clean version history for the project. If you wish to add a specific commit message for this action, you can specify a `commit_message` in the `_commit` option in your `copier.yaml` file.

- **VSCode**: If the user has Visual Studio Code (VSCode) installed and the path to VSCode is added to their system's PATH, Copier can automatically open the newly created project in a new VSCode window. This is triggered by adding `vscode: true` in your `copier.yam` file.

- **Bootstrap**: As previously mentioned, AlgoKit templates can include a bootstrap script that is automatically run after the project is initialized. This script can perform various setup tasks like installing dependencies or setting up databases. By default, if a `bootstrap` task is defined in the `copier.yaml`, it will be executed unless the user opts out during the prompt.

By combining predefined Copier answers with these default behaviors, you can create a smooth, efficient, and intuitive initialization experience for the users of your template.
## Recommendations

- **Modularity**: Break your templates into modular components that can be combined in different ways.
- **Documentation**: Include README files and comments in your templates to explain how they should be used.
- **Versioning**: Use `.algokit.toml` to specify the minimum compatible version of AlgoKit.
- **Testing**: Include test configurations and scripts in your templates to encourage testing best practices.
- **Linting and Formatting**: Integrate linters and code formatters in your templates to ensure code quality.
- **Algokit Principle**: for details on generic principles on designing templates refer to algo kit design principles
## Conclusion

Creating custom templates in AlgoKit is a powerful way to streamline your development workflow for Algorand smart contracts, whether you are using Python or TypeScript. Leveraging Copier and Jinja for templating, and incorporating best practices for modularity, documentation, and coding standards, can result in robust, flexible, and user-friendly templates that can be a valuable asset to both your own projects and the broader Algorand community.

Happy coding!
