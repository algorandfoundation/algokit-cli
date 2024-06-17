# AlgoKit Config

The `algokit config` command allows you to manage various global settings used by AlgoKit CLI. This feature is essential for customizing your AlgoKit environment to suit your needs.

## Usage

This command group provides a set of subcommands to configure AlgoKit settings.
Subcommands

- `version-prompt`: Configure the version prompt settings.
- `container-engine`: Configure the container engine settings.

### Version Prompt Configuration

```zsh
$ algokit config version-prompt [OPTIONS]
```

This command configures the version prompt settings for AlgoKit.

- `--enable`: Enable the version prompt.
- `--disable`: Disable the version prompt.

### Container Engine Configuration

```zsh
$ algokit config container-engine [OPTIONS]
```

This command configures the container engine settings for AlgoKit.

- `--engine`, -e: Specify the container engine to use (e.g., Docker, Podman). This option is required.
- `--path`, -p: Specify the path to the container engine executable. Optional.

## Further Reading

For in-depth details, visit the [configuration section](../cli/index.md#config) in the AlgoKit CLI reference documentation.
