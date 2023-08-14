# AlgoKit Generate

The `algokit generate` [command](../cli/index.md#generate) is used to generate components used in an AlgoKit project. It also allows for custom generate commands which are loaded from the .algokit.toml file in your project directory.

## 1. Typed clients

The `algokit generate client` [command](../cli/index.md#client) can be used to generate a typed client from an [ARC-0032](https://arc.algorand.foundation/ARCs/arc-0032) application specification with
both Python and TypeScript available as target languages.

### Prerequisites

To generate Python clients AlgoKit itself is the only dependency.
To generate TypeScript clients an installation of Node.js and npx is also required.

Each generated client will also have a dependency on `algokit-utils` libraries for the target language:

- Python clients require: `algokit-utils@^1.2`
- TypeScript clients require: `@algorandfoundation/algokit-utils@^2.0`

### Output tokens

The output path is interpreted as relative to the current working directory, however an absolute path may also be specified e.g.
`algokit generate client application.json --output /absolute/path/to/client.py`

There are two tokens available for use with the `-o`, `--output` [option](../cli/index.md#-o---output-):

- `{contract_name}`: This will resolve to a name based on the ARC-0032 contract name, formatted appropriately for the target language.
- `{app_spec_dir}`: This will resolve to the parent directory of an `application.json` which can be useful to output a client relative to its source application.json.

### Usage

Usage examples of using a generated client are below, typed clients allow your favourite IDE to provide better intellisense to provide better discoverability
of available operations and parameters.

#### Python

```python
# A similar working example can be seen in the beaker_production template, when using Python deployment
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
// A similar working example can be seen in the beaker_production template, when using TypeScript deployment
import { HelloWorldAppClient } from './artifacts/HelloWorldApp/client'

const appClient = new HelloWorldAppClient(
  {
    resolveBy: 'creatorAndName',
    findExistingUsing: indexer,
    sender: deployer,
    creatorAddress: deployer.addr,
  },
  algod,
)
const app = await appClient.deploy({
  allowDelete: isLocal,
  allowUpdate: isLocal,
  onSchemaBreak: isLocal ? 'replace' : 'fail',
  onUpdate: isLocal ? 'update' : 'fail',
})
const response = await appClient.hello({ name: 'world' })
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

A `generator` is essentially a compact, self-sufficient `copier` template. This template can optionally be defined within the primary `algokit templates` to offer supplementary functionality after a project is initialized from the template. For instance, the official [`algokit-beaker-default-template`](https://github.com/algorandfoundation/algokit-beaker-default-template/tree/main/template_content) provides a generator within the `.algokit/generators` directory. This generator can be employed for executing extra tasks on AlgoKit projects that have been initiated from this template, such as adding new smart contracts to an existing project. For a comprehensive explanation, please refer to the [`architecture decision record`](../architecture-decisions/2023-07-19_advanced_generate_command.md).

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

As an example, let's use the `smart-contract` generator from the `algokit-beaker-default-template` to add new contract to an existing project based on that template. The `smart-contract` generator is defined as follows:

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
