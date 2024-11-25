# AlgoKit Generate

The `algokit generate` [command](../cli/index.md#generate) is used to generate components used in an AlgoKit project. It also allows for custom generate commands which are loaded from the .algokit.toml file in your project directory.

## 1. Typed clients

The `algokit generate client` [command](../cli/index.md#client) can be used to generate a typed client from an [ARC-0032](https://arc.algorand.foundation/ARCs/arc-0032) or [ARC-0056](https://github.com/algorandfoundation/ARCs/pull/258) application specification with both Python and TypeScript available as target languages.

### Prerequisites

To generate Python clients an installation of pip and pipx is required.
To generate TypeScript clients an installation of Node.js and npx is also required.

Each generated client will also have a dependency on `algokit-utils` libraries for the target language.

### Input file / directory

You can either specify a path to an ARC-0032 JSON file, an ARC-0056 JSON file or to a directory that is recursively scanned for `application.json`, `*.arc32.json`, `*.arc56.json` file(s).

### Output tokens

The output path is interpreted as relative to the current working directory, however an absolute path may also be specified e.g.
`algokit generate client application.json --output /absolute/path/to/client.py`

There are two tokens available for use with the `-o`, `--output` [option](../cli/index.md#-o---output-):

- `{contract_name}`: This will resolve to a name based on the ARC-0032/ARC-0056 contract name, formatted appropriately for the target language.
- `{app_spec_dir}`: This will resolve to the parent directory of the `application.json`, `*.arc32.json`, `*.arc56.json` file which can be useful to output a client relative to its source file.

### Version Pinning

If you want to ensure typed client output stability across different environments and additionally protect yourself from any potential breaking changes introduced in the client generator packages, you can specify a version you'd like to pin to.

To make use of this feature, pass `-v`, `--version`, for example `algokit generate client --version 1.2.3 path/to/application.json`.

Alternatively, you can achieve output stability by installing the underlying [Python](https://github.com/algorandfoundation/algokit-client-generator-py) or [TypeScript](https://github.com/algorandfoundation/algokit-client-generator-ts) client generator package either locally in your project (via `poetry` or `npm` respectively) or globally on your system (via `pipx` or `npm` respectively). AlgoKit will search for a matching installed version before dynamically resolving.

### Usage

Usage examples of using a generated client are below, typed clients allow your favourite IDE to provide better intellisense to provide better discoverability
of available operations and parameters.

#### Python

```python
# A similar working example can be seen in the algokit python template, when using Python deployment
from smart_contracts.artifacts.HelloWorldApp.client import (
    HelloWorldAppClient,
)

app_client = HelloWorldAppClient(
    algod_client,
    creator=deployer,
    indexer_client=indexer_client,
)
deploy_response = app_client.deploy(
    on_schema_break=OnSchemaBreak.ReplaceApp,
    on_update=OnUpdate.UpdateApp,
    allow_delete=True,
    allow_update=True,
)

response = app_client.hello(name="World")
```

#### TypeScript

```typescript
// A similar working example can be seen in the algokit python template with typescript deployer, when using TypeScript deployment
import { HelloWorldAppClient } from "./artifacts/HelloWorldApp/client";

const appClient = new HelloWorldAppClient(
  {
    resolveBy: "creatorAndName",
    findExistingUsing: indexer,
    sender: deployer,
    creatorAddress: deployer.addr,
  },
  algod
);
const app = await appClient.deploy({
  allowDelete: isLocal,
  allowUpdate: isLocal,
  onSchemaBreak: isLocal ? "replace" : "fail",
  onUpdate: isLocal ? "update" : "fail",
});
const response = await appClient.hello({ name: "world" });
```

### Examples

To output a single application.json to a python typed client:
`algokit generate client path/to/application.json --output client.py`

To process multiple application.json in a directory structure and output to a typescript client for each in the current directory:
`algokit generate client smart_contracts/artifacts --output {contract_name}.ts`

To process multiple application.json in a directory structure and output to a python client alongside each application.json:
`algokit generate client smart_contracts/artifacts --output {app_spec_path}/client.py`

## 2. Using Custom Generate Commands

Custom generate commands are defined in the `.algokit.toml` file within the project directory, typically supplied by community template builders or official AlgoKit templates. These commands are specified under the `generate` key and serve to execute a generator at a designated path with provided answer key/value pairs.

### Understanding `Generators`

A `generator` is essentially a compact, self-sufficient `copier` template. This template can optionally be defined within the primary `algokit templates` to offer supplementary functionality after a project is initialized from the template. For instance, the official [`algokit-python-template`](https://github.com/algorandfoundation/algokit-python-template/tree/main/template_content) provides a generator within the `.algokit/generators` directory. This generator can be employed for executing extra tasks on AlgoKit projects that have been initiated from this template, such as adding new smart contracts to an existing project. For a comprehensive explanation, please refer to the [`architecture decision record`](../architecture-decisions/2023-07-19_advanced_generate_command.md).

### Requirements

To utilize custom generate commands, you must have `copier` installed. This installation is included by default in the AlgoKit CLI. Therefore, no additional installation is necessary if you have already installed the `algokit cli`.

### How to Use

A custom command can be defined in the `.algokit.toml` as shown:

```toml
[generate.my_generator]
path = "path/to/my_generator"
description = "A brief description of the function of my_generator"
```

Following this, you can execute the command as follows:

`algokit generate my_generator --answer key value --path path/to/my_generator`

If no `path` is given, the command will use the path specified in the `.algokit.toml`. If no `answer` is provided, the command will initiate an interactive `copier` prompt to request answers (similar to `algokit init`).

The custom command employs the `copier` library to duplicate the files from the generator's path to the current working directory, substituting any values from the `answers` dictionary.

### Examples

As an example, let's use the `smart-contract` generator from the `algokit-python-template` to add new contract to an existing project based on that template. The `smart-contract` generator is defined as follows:

```toml
[algokit]
min_version = "v1.3.1"

... # other keys

[generate.smart_contract]
description = "Adds a new smart contract to the existing project"
path = ".algokit/generators/create_contract"
```

To execute this generator, ensure that you are operating from the same directory as the `.algokit.toml` file, and then run:

```bash
$ algokit generate

# The output will be as follows:
# Note how algokit dynamically injects a new `smart-contract` command based
# on the `.algokit.toml` file

Usage: algokit generate [OPTIONS] COMMAND [ARGS]...

  Generate code for an Algorand project.

Options:
  -h, --help  Show this message and exit.

Commands:
  client          Create a typed ApplicationClient from an ARC-32 application.json
  smart-contract  Adds a new smart contract to the existing project
```

To execute the `smart-contract` generator, run:

```bash
$ algokit generate smart-contract

# or

$ algokit generate smart-contract -a contract_name "MyCoolContract"
```

#### Third Party Generators

It is important to understand that by default, AlgoKit will always prompt you before executing a generator to ensure it's from a trusted source. If you are confident about the source of the generator, you can use the `--force` or `-f` option to execute the generator without this confirmation prompt. Be cautious while using this option and ensure the generator is from a trusted source. At the moment, a trusted source for a generator is defined as _a generator that is included in the official AlgoKit templates (e.g. `smart-contract` generator in `algokit-python-template`)_
