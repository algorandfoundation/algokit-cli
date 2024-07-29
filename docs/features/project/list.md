# AlgoKit Project List Command

The `algokit project list` command is designed to enumerate all projects within an AlgoKit workspace. This command is particularly useful in workspace environments where multiple projects are managed under a single root directory. It provides a straightforward way to view all the projects that are part of the workspace.

## Usage

To use the `list` command, execute the following **anywhere** within an AlgoKit workspace:

```sh
$ algokit project list [OPTIONS] [WORKSPACE_PATH]
```

- `WORKSPACE_PATH` is an optional argument that specifies the path to the workspace. If not provided, the current directory (`.`) is used as the default workspace path.

## How It Works

1. **Workspace Verification**: Initially, the command checks if the specified directory (or the current directory by default) is an AlgoKit workspace. This is determined by looking for a `.algokit.toml` configuration file and verifying if the `project.type` is set to `workspace`.

2. **Project Enumeration**: If the directory is confirmed as a workspace, the command proceeds to enumerate all projects within the workspace. This is achieved by scanning the workspace's subdirectories for `.algokit.toml` files and extracting project names.

3. **Output**: The names of all discovered projects are printed to the console. If the `-v` or `--verbose` option is used, additional details about each project are displayed.

## Example Output

```sh
workspace: {path_to_workspace} 📁
  - myapp ({path_to_myapp}) 📜
  - myproject-app ({path_to_myproject_app}) 🖥️
```

## Error Handling

If the command is executed in a directory that is not recognized as an AlgoKit workspace, it will issue a warning:

```sh
WARNING: No AlgoKit workspace found. Check [project.type] definition at .algokit.toml
```

This message indicates that either the current directory does not contain a `.algokit.toml` file or the `project.type` within the file is not set to `workspace`.

## Further Reading

To learn more about the `algokit project list` command, please refer to [list](../../cli/index.md#list) in the AlgoKit CLI reference documentation.
