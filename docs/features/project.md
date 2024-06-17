# AlgoKit Project

`algokit project` is a collection of commands and command groups useful for managing algokit compliant [project workspaces](./init.md#workspaces).

## Overview

The `algokit project` command group is designed to simplify the management of AlgoKit projects. It provides a suite of tools to initialize, deploy, link, list, and run various components within a project workspace. This command group ensures that developers can efficiently handle the lifecycle of their projects, from bootstrapping to deployment and beyond.

### What is a Project?

In the context of AlgoKit, a "project" refers to a structured standalone or monorepo workspace that includes all the necessary components for developing, testing, and deploying Algorand applications. This may include smart contracts, frontend applications, and any associated configurations. In the context of the CLI, the `algokit project` commands help manage these components cohesively.

The orchestration between workspaces, standalone projects, and custom commands is designed to provide a seamless development experience. Below is a high-level overview of how these components interact within the AlgoKit ecosystem.

```mermaid
graph TD;
A[AlgoKit Project] --> B["Workspace (.algokit.toml)"];
A --> C["Standalone Project (.algokit.toml)"];
B --> D["Sub-Project 1 (.algokit.toml)"];
B --> E["Sub-Project 2 (.algokit.toml)"];
C --> F["Custom Commands defined in .algokit.toml"];
D --> F;
E --> F;
```

- **AlgoKit Project**: The root command that encompasses all project-related functionalities.
- **Workspace**: A root folder that is managing multiple related sub-projects.
- **Standalone Project**: An isolated project structure for simpler applications.
- **Custom Commands**: Commands defined by the user in the `.algokit.toml` and automatically injected into the `algokit project run` command group.

## Features

Dive into the features of the `algokit project` command group:

- [bootstrap](./project/bootstrap.md) - Bootstrap your project with AlgoKit.
- [deploy](./project/deploy.md) - Deploy your smart contracts effortlessly to various networks.
- [link](./project/link.md) - Powerful feature designed to streamline the integration between `frontend` and `contract` projects
- [list](./project/list.md) - Enumerate all projects within an AlgoKit workspace.
- [run](./project/run.md) - Define custom commands and manage their execution via `algokit` cli.
