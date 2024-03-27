# AlgoKit Project Bootstrap

The AlgoKit Project Bootstrap feature allows you to bootstrap different project dependencies by looking up specific files in your current directory and immediate sub directories by convention.

This is useful to allow for expedited initial setup for each developer e.g. when they clone a repository for the first time. It's also useful to provide a quick getting started experience when initialising a new project via [AlgoKit Init](./init.md) and meeting our goal of "nothing to debugging code in 5 minutes".

It can bootstrap one or all of the following (with other options potentially being added in the future):

- Python Poetry projects - Installs Poetry via pipx if its not present and then runs `poetry install`
- Node.js project - Checks if npm is installed and runs `npm install`
- dotenv (.env) file - Checks for `.env.template` files, copies them to `.env` (which should be in `.gitignore` so developers can safely make local specific changes) and prompts for any blank values (so the developer has an easy chance to fill in their initial values where there isn't a clear default).

> **Note**: Invoking bootstrap from `algokit bootstrap` is not recommended. Please prefer using `algokit project bootstrap` instead.

## Usage

Available commands and possible usage as follows:

```
$ ~ algokit project bootstrap
Usage: algokit project bootstrap [OPTIONS] COMMAND [ARGS]...

Options:
  -h, --help  Show this message and exit.

Commands:
  all     Bootstrap all aspects of the current directory and immediate sub directories by convention.
  env     Bootstrap .env file in the current working directory.
  npm     Bootstrap Node.js project in the current working directory.
  poetry  Bootstrap Python Poetry and install in the current working directory.
```

## Functionality

### Bootstrap .env file

The command `algokit project bootstrap env` runs two main tasks in the current directory:

- Searching for `.env.template` file in the current directory and use it as template to create a new `.env` file in the same directory.
- Prompting the user to enter a value for any empty token values in the `env.` including printing the comments above that empty token

For instance, a sample `.env.template` file as follows:

```
SERVER_URL=https://myserver.com
# This is a mandatory field to run the server, please enter a value
# For example: 5000
SERVER_PORT=
```

Running the `algokit project bootstrap env` command while the above `.env.template` file in the current directory will result in the following:

```
$ ~ algokit project bootstrap env
Copying /Users/me/my-project/.env.template to /Users/me/my-project/.env and prompting for empty values
# This is a mandatory field to run the server, please enter a value value
# For example: 5000

? Please provide a value for SERVER_PORT:
```

And when the user enters a value for `SERVER_PORT`, a new `.env` file will be created as follows (e.g. if they entered `4000` as the value):

```
SERVER_URL=https://myserver.com
# This is a mandatory field to run the server, please enter a value
# For example: 5000
SERVER_PORT=4000
```

### Bootstrap Node.js project

The command `algokit project bootstrap npm` installs Node.js project dependencies if there is a `package.json` file in the current directory by running `npm install` command to install all node modules specified in that file. If you don't have npm available it will show a clear error message and resolution instructions.

Here is an example outcome of running `algokit project bootstrap npm` command:

```
$ ~ algokit project bootstrap npm
Installing npm dependencies
npm:
npm: added 17 packages, and audited 18 packages in 3s
npm:
npm: 2 packages are looking for funding
npm: run `npm fund` for details
npm:
npm: found 0 vulnerabilities
```

### Bootstrap Python poetry project

The command `algokit project bootstrap poetry` does two main actions:

- Checking for Poetry version by running `poetry --version` and upgrades it if required
- Installing Python dependencies and setting up Python virtual environment via Poetry in the current directory by running `poetry install`.

Here is an example of running `algokit project bootstrap poetry` command:

```
$ ~ algokit project bootstrap poetry
Installing Python dependencies and setting up Python virtual environment via Poetry
poetry:
poetry: Installing dependencies from lock file
poetry:
poetry: Package operations: 1 installs, 1 update, 0 removals
poetry:
poetry: • Installing pytz (2022.7)
poetry: • Updating copier (7.0.1 -> 7.1.0a0)
poetry:
poetry: Installing the current project: algokit (0.1.0)
```

### Bootstrap all

Execute `algokit project bootstrap all` to initiate `algokit project bootstrap env`, `algokit project bootstrap npm`, and `algokit project bootstrap poetry` commands within the current directory and all its immediate sub-directories. This comprehensive command is automatically triggered following the initialization of a new project through the [AlgoKit Init](./init.md) command.

#### Filtering Options

The `algokit project bootstrap all` command includes flags for more granular control over the bootstrapping process within [AlgoKit workspaces](../init.md#workspaces):

- `--project-name`: This flag allows you to specify one or more project names to bootstrap. Only projects matching the provided names will be bootstrapped. This is particularly useful in monorepos or when working with multiple projects in the same directory structure.

- `--type`: Use this flag to limit the bootstrapping process to projects of a specific type (e.g., `frontend`, `backend`, `contract`). This option streamlines the setup process by focusing on relevant project types, reducing the overall bootstrapping time.

These new flags enhance the flexibility and efficiency of the bootstrapping process, enabling developers to tailor the setup according to project-specific needs.

## Further Reading

To learn more about the `algokit project bootstrap` command, please refer to [bootstrap](../../cli/index.md#bootstrap) in the AlgoKit CLI reference documentation.
