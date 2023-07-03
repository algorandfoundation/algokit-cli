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

This file is used to specify the minimum version of AlgoKit that is compatible with your template. This is essential to ensure that projects created with your template are always compatible with the version of AlgoKit they are using.

Example from `algokit-beaker-default-template`:
```toml
[algokit]
min_version = "v1.1.0-beta.4"
```
This specifies that the template requires at least version `v1.1.0-beta.4` of AlgoKit.

### Python Support: `pyproject.toml`

For Python projects, the `pyproject.toml` file is crucial. It specifies metadata about the project and lists the dependencies required. Poetry is used for Python dependency management. This can be templated using Jinja syntax.

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

For TypeScript projects, the `package.json` file plays a similar role as `pyproject.toml` for Python projects. It specifies metadata about the project and lists the dependencies required for smart contract development.

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

### Template Answers and Variables

When initializing a new project, Copier can prompt the user for input, which is then passed to the template as variables. This is useful for customizing the new project based on user input.

Example:

```yaml
# copier.yaml
project_name:
  type: str
  help: What is the name of your project?
```
This would prompt the user for the project name, and the input can then be used in the template using the Jinja syntax `{{ project_name }}`.

## Recommendations

- **Modularity**: Break your templates into modular components that can be combined in different ways.
- **Documentation**: Include README files and comments in your templates to explain how they should be used.
- **Versioning**: Use `.algokit.toml` to specify the minimum compatible version of AlgoKit.
- **Testing**: Include test configurations and scripts in your templates to encourage testing best practices.
- **Linting and Formatting**: Integrate linters and code formatters in your templates to ensure code quality.

## Conclusion

Creating custom templates in AlgoKit is a powerful way to streamline your development workflow for Algorand smart contracts, whether you are using Python or TypeScript. Leveraging Copier and Jinja for templating, and incorporating best practices for modularity, documentation, and coding standards, can result in robust, flexible, and user-friendly templates that can be a valuable asset to both your own projects and the broader Algorand community.

Happy coding!
