# AlgoKit Bootstrap

The AlgoKit Bootstrap feature allows you to bootstrap different project dependencies by looking up specific files in your current directory and immediate sub directories by convention. It can bootstrap one or all of three options which are Python poetry project, Node.js project or env file.

Available commands and possible usage as follows:

```
Usage: algokit bootstrap [OPTIONS] COMMAND [ARGS]...

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

The command `algokit bootstrap env` runs two main tasks:

- Searching for `.env.template` file in the current directory and use it as template to create a new `.env` file in the same directory.
- Prompting the user to enter a value for any empty token values in the `env.` including printing the comments above that empty token

For instance, a sample `.env.template` file as follows:

```t
SERVER_URL=http://myserver.com.au
# This is a mandatory field to run the server, please enter a value
# For example: 5000
SERVER_PORT=
```

Running the command `algokit bootstrap env` using the above `.env.template` will result in the following:

```
Copying /Users/me/algokit-cli/.env.template to /Users/me/algokit-cli/.env and prompting for empty values
# This is a mandatory field to run the server, please enter a value value
# For example: 5000

? Please provide a value for SERVER_PORT:
```

And when the user enters a value for `SERVER_PORT`, a new `.env` file will be created as follows

```t
SERVER_URL=http://myserver.com.au
# This is a mandatory field to run the server, please enter a value
# For example: 5000
SERVER_PORT=4000
```

### Bootstrap Node.js project

The command `algokit bootstrap npm` installs Node.js project dependencies by searching for `package.json` file in the current directory and running `npm install` command to install all node modules specified in that file.

Here is an example outcome of running `algokit bootstrap npm` command:

```
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

The command `algokit bootstrap poetry` does two main jobs:

- Checking for Poetry version by running `poetry --version` and upgrades it if required
- Installing Python dependencies and setting up Python virtual environment via Poetry by running `poetry install` in the current directory

Here is an example outcome of running `algokit bootstrap poetry` command:

```
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

You can run `algokit bootstrap all` which will run all three commands `env`, `npm` and `poetry` inside the current directory and all immediate sub-directories.

To know more about `algokit bootstrap` command, please refer to [bootstrap](../cli/index.md#bootstrap) in the AlgoKit CLI documentation
