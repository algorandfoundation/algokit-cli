---
title: "AlgoKit Project List Command"
---

The `algokit project list` command is designed to enumerate all projects within an AlgoKit workspace. This command is particularly useful in workspace environments where multiple projects are managed under a single root directory. It provides a straightforward way to view all the projects that are part of the workspace.

## Usage

To use the `list` command, execute the following **anywhere** within an AlgoKit workspace:

```bash
algokit project list [OPTIONS] [WORKSPACE_PATH]
```

- `WORKSPACE_PATH` is an optional argument that specifies the path to the workspace. If not provided, the current directory (`.`) is used as the default workspace path.

## How It Works

1. **Workspace Verification**: Initially, the command checks if the specified directory (or the current directory by default) is an AlgoKit workspace. This is determined by looking for a `.algokit.toml` configuration file and verifying if the `project.type` is set to `workspace`. If the starting directory is not a workspace, the command walks up to two parent directories looking for one, which is why it can be invoked anywhere within a workspace.

2. **Project Enumeration**: If a workspace is found, the command enumerates its sub-projects by reading the `project.projects_root_path` defined in the workspace's `.algokit.toml`, then iterating over immediate subdirectories of that path which themselves contain an `.algokit.toml`. The results are sorted alphanumerically by directory name.

3. **Output**: The command first prints the workspace header with the resolved workspace path, followed by each sub-project's name and directory. A project's directory is shown as `this directory` only when it equals the current working directory; otherwise the absolute path is shown.

## Example Output

Run from inside the workspace root with two sub-projects (a contract and a frontend):

```bash
workspace: /path/to/workspace 📁
  - myapp (/path/to/workspace/projects/myapp) 📜
  - myproject-app (/path/to/workspace/projects/myproject-app) 🖥️
```

## Error Handling

If the command is executed in a directory that is not recognized as an AlgoKit workspace, it will issue a warning:

```bash
WARNING: No AlgoKit workspace found. Check [project.type] definition at .algokit.toml
```

This message indicates that no `.algokit.toml` with `project.type = "workspace"` was found in the target directory or its parents (up to two levels up).

If a workspace is found but contains no sub-projects, a different warning is emitted:

```bash
WARNING: No AlgoKit project(s) found in the workspace. Check [project.type] definition at .algokit.toml
```

## Further Reading

To learn more about the `algokit project list` command, please refer to [list](/algokit-cli/cli/#list) in the AlgoKit CLI reference documentation.
