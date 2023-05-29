# AlgoKit Generate

The `algokit generate` [command](../cli/index.md#generate) is used to generate components used in an AlgoKit project.

## Client

The `algokit generate client` [command](../cli/index.md#client) can be used to generate a typed client from an ARC-32 application specification with 
both Python and TypeScript available as target languages.

### Prerequisites

To generate Python clients AlgoKit itself is the only dependency.
To generate TypeScript clients an install of Node.js and npx is also required.

Each generated client will also have a dependency on `algosdk` and `algokit-utils` libraries using the Python or JavaScript versions of both as appropriate.

### Output tokens

The output path is interpreted as relative to the current working directory, however an absolute path may also be specified e.g.
`algokit generate client application.json --output /absolute/path/to/client.py`

There are two tokens available for use with the `-o`, `--output` [option](../cli/index.md#-o---output-):
* `{contract_name}`: This will resolve to a name based on the ARC-32 contract name, formatted appropriately for the target language.
* `{app_spec_dir}`: This will resolve to the parent directory of an `application.json` which can be useful to output a client relative to its source application.json.


### Examples

To output a single application.json to a python typed client:
`algokit generate client path/to/application.json --output client.py`

To process multiple application.json in a directory structure and output to a typescript client for each in the current directory:
`algokit generate client smart_contracts/artifacts --output {contract_name}.ts`

To process multiple application.json in a directory structure and output to a python client alongside each application.json:
`algokit generate client smart_contracts/artifacts --output {app_spec_path}/client.py`
