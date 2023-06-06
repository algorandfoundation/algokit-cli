# AlgoKit Generate

The `algokit generate` [command](../cli/index.md#generate) is used to generate components used in an AlgoKit project.

## Client

The `algokit generate client` [command](../cli/index.md#client) can be used to generate a typed client from an [ARC-0032](https://arc.algorand.foundation/ARCs/arc-0032) application specification with 
both Python and TypeScript available as target languages.

### Prerequisites

To generate Python clients AlgoKit itself is the only dependency.
To generate TypeScript clients an installation of Node.js and npx is also required.

Each generated client will also have a dependency on `algokit-utils` libraries for the target language:

* Python clients require: `algokit-utils@^1.2`
* TypeScript clients require: `@algorandfoundation/algokit-utils@^2.0`

### Output tokens

The output path is interpreted as relative to the current working directory, however an absolute path may also be specified e.g.
`algokit generate client application.json --output /absolute/path/to/client.py`

There are two tokens available for use with the `-o`, `--output` [option](../cli/index.md#-o---output-):
* `{contract_name}`: This will resolve to a name based on the ARC-0032 contract name, formatted appropriately for the target language.
* `{app_spec_dir}`: This will resolve to the parent directory of an `application.json` which can be useful to output a client relative to its source application.json.


### Examples

To output a single application.json to a python typed client:
`algokit generate client path/to/application.json --output client.py`

To process multiple application.json in a directory structure and output to a typescript client for each in the current directory:
`algokit generate client smart_contracts/artifacts --output {contract_name}.ts`

To process multiple application.json in a directory structure and output to a python client alongside each application.json:
`algokit generate client smart_contracts/artifacts --output {app_spec_path}/client.py`

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
