# AlgoKit Config

The `algokit config` command allows you to manage various global settings used by AlgoKit CLI. This feature is essential for customizing your AlgoKit environment to suit your needs.

## Usage

This command group provides a set of subcommands to configure AlgoKit settings.
Subcommands

- `version-prompt`: Configure the version prompt settings.
- `container-engine`: Configure the container engine settings.
- `js-package-manager`: Configure the default JavaScript package manager.
- `py-package-manager`: Configure the default Python package manager.

### Version Prompt Configuration

```zsh
$ algokit config version-prompt [OPTIONS]
```

This command configures the version prompt settings for AlgoKit.

- `--enable`: Enable the version prompt.
- `--disable`: Disable the version prompt.

### Container Engine Configuration

```zsh
$ algokit config container-engine [OPTIONS] [ENGINE]
```

This command configures the container engine settings for AlgoKit.

- `--force`, `-f`: Skip confirmation prompts. Defaults to 'yes' to all prompts.
- `ENGINE`: Optional argument to specify the container engine (docker or podman).

### JavaScript Package Manager Configuration

```zsh
$ algokit config js-package-manager [OPTIONS] [PACKAGE_MANAGER]
```

This command configures the default JavaScript package manager used by AlgoKit's bootstrap command.

- `PACKAGE_MANAGER`: Optional argument to specify the package manager (npm or pnpm).

If no package manager is specified, AlgoKit will prompt you to select one interactively.

### Python Package Manager Configuration

```zsh
$ algokit config py-package-manager [OPTIONS] [PACKAGE_MANAGER]
```

This command configures the default Python package manager used by AlgoKit's bootstrap command.

- `PACKAGE_MANAGER`: Optional argument to specify the package manager (poetry or uv).

If no package manager is specified, AlgoKit will prompt you to select one interactively.

## Further Reading

For in-depth details, visit the [configuration section](../cli/index.md#config) in the AlgoKit CLI reference documentation.
