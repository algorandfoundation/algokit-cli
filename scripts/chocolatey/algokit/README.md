# Chocolatey Package

This directory contains the nuspec file to define the [Chocolatey](https://chocolatey.org/) repository package for Windows and various associate powershell scripts.

# Installing

> __Note__
> This will install the most recent python3 version through chocolatey. If you already have python installed, you may prefer to use `pipx install algokit` as explained in [Installing](../../../README.md).

1. Ensure chocolatey is installed - https://chocolatey.org/install
2. Run `choco install algokit` from an administrator powershell/cmd/terminal window
3. Test algokit is installed `algokit --version`

# Development

## Building and publishing locally

1. Ensure wheel file is built `poetry build` (make sure there's only a single file in _dist_ directory)
2. Set version field in _algokit.nuspec_
   > __Note__
   > Versions with a pre-release suffix such as 1.2.3-beta are automatically designated as pre-release packages by chocolatey
3. `cd .\scripts\chocolatey\algokit`
4. `choco pack`
5. `choco apikey --api-key [API_KEY_HERE] -source https://push.chocolatey.org/`
6. `choco push --source https://push.chocolatey.org/`

Also see [Chocolatey docs](https://docs.chocolatey.org/en-us/create/create-packages).

## Installing from local packages

- `cd .\scripts\chocolatey\algokit`
- Install - `choco install algokit -pre --source "'.;https://community.chocolatey.org/api/v2/'" -y`
- Uninstall - `choco uninstall algokit -y`
- Upgrade - `choco upgrade algokit -pre --source "'.;https://community.chocolatey.org/api/v2/'" -y`

# Issues

- Chocolatey doesn't support full sematic release v2 versions yet. This means version identifiers with dot notation are not supported (1.2.3-beta.12). See [this issue](https://github.com/chocolatey/choco/issues/1610).
- Installing using the `-pre` tag on will also install pre-release verisons of dependencies. At the time of development, this installed python 3.12.0-a2 which has errors installing algokit. Solution is to `choco install python3` prior to `choco install algokit -pre`. See [nuspec](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning#pre-release-versions) for clarification.
