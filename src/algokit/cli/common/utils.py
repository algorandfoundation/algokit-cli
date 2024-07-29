# Cli/Click related helper functions and classes


import typing as t

import click

from algokit.cli.common.constants import ExplorerEntityType


class MutuallyExclusiveOption(click.Option):
    """
    A Click option that defines mutually exclusive command line options.

    Args:
        *args: Positional arguments passed to the parent class constructor.
        **kwargs: Keyword arguments passed to the parent class constructor.
            not_required_if (list): A list of options that the current option is mutually exclusive with.

    Attributes:
        not_required_if (list): A list of options that the current option is mutually exclusive with.

    Raises:
        AssertionError: If the `not_required_if` parameter is not provided.

    Example:
        ```python
        @click.command()
        @click.option('--option1', help='Option 1')
        @click.option('--option2', help='Option 2')
        @click.option('--option3', help='Option 3', cls=MutuallyExclusiveOption, not_required_if=['option1', 'option2'])
        def my_command(option1, option2, option3):
            # Command logic here
            pass
        ```

        In the example above, the `MutuallyExclusiveOption` class is used to define the `option3` command line option.
        This option is mutually exclusive with `option1` and `option2`,
        meaning that if either `option1` or `option2` is provided, `option3` cannot be used.
        If `option3` is provided along with `option1` or `option2`, a `click.UsageError` is raised.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.not_required_if: list = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (
            kwargs.get("help", "") + " Option is mutually exclusive with " + ", ".join(self.not_required_if) + "."
        ).strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: click.Context, opts: t.Mapping[str, t.Any], args: list[str]
    ) -> tuple[t.Any, list[str]]:
        """
        Overrides the `handle_parse_result` method of the `click.Option` class.

        This method checks if the current option is present in the provided options (`opts`)
        and if any of the mutually exclusive options are also present.
        If both the current option and a mutually exclusive option are present, it raises a `click.UsageError`.
        Otherwise, it returns the result of the parent `handle_parse_result` method.

        Args:
            ctx (click.Context): The Click context object.
            opts (dict): The dictionary of parsed options.
            args (list): The list of remaining arguments.

        Returns:
            The result of the parent `handle_parse_result` method.

        Raises:
            click.UsageError: If the current option and a mutually exclusive option are both present.
        """

        current_opt: bool = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError(
                        "Illegal usage: '" + str(self.name) + "' is mutually exclusive with " + str(mutex_opt) + "."
                    )
                self.prompt = None
        return super().handle_parse_result(ctx, opts, args)


def get_explorer_url(identifier: str | int, network: str, entity_type: ExplorerEntityType) -> str:
    """
    Returns a URL for exploring a specified type (transaction, asset, address) on the specified network.

    Args:
        identifier (str | int): The ID of the transaction, asset, or address to explore.
        network (str): The name of the network (e.g., "localnet", "testnet", "mainnet").
        entity_type (ExplorerEntityType): The type to explore (e.g., ExplorerEntityType.TRANSACTION,
        ExplorerEntityType.ASSET, ExplorerEntityType.ADDRESS).

    Returns:
        str: The URL for exploring the specified type on the specified network.

    Raises:
        ValueError: If the network or explorer type is invalid.
    """

    return f"https://explore.algokit.io/{network}/{entity_type.value}/{identifier}"
