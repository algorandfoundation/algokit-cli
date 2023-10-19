import logging

import click
from algokit_utils import opt_in, opt_out
from algosdk import error

from algokit.cli.tasks.utils import (
    get_account_with_private_key,
    load_algod_client,
    validate_account_balance_to_opt_in,
    validate_address,
)

logger = logging.getLogger(__name__)


@click.command(
    name="opt-in",
    help="Opt-in to an asset using <ID> <ACCOUNT>. This is required before you can receive an asset. "
    "Use -n to specify localnet, testnet, or mainnet.",
)
@click.argument("account", type=click.STRING, required=True)
@click.argument("asset_ids", type=click.STRING, required=True)
@click.option(
    "-n",
    "--network",
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def opt_in_command(asset_ids: str, account: str, network: str) -> None:
    asset_ids_list = []
    for asset_id in asset_ids.split(","):
        asset_ids_list.append(int(asset_id.strip()))

    opt_in_account = get_account_with_private_key(account)
    validate_address(opt_in_account.address)
    algod_client = load_algod_client(network)

    validate_account_balance_to_opt_in(algod_client, opt_in_account, len(asset_ids_list))
    try:
        opt_in(algod_client=algod_client, account=opt_in_account, asset_ids=asset_ids_list)
        click.echo("Successfully performed opt-in. ")
    except error.AlgodHTTPError as err:
        raise click.ClickException(str(err)) from err
    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform opt-in") from err


@click.command(
    name="opt-out",
    help="opt-out of an asset using <ID> <ACCOUNT>. You can only opt out of an asset with a zero balance. "
    "Use -n to specify localnet, testnet, or mainnet.",
)
@click.argument("account", type=click.STRING, required=True)
@click.argument("asset_ids", type=click.STRING, required=False)
@click.option(
    "--all",
    "all_assets",
    is_flag=True,
    type=click.BOOL,
    help="Opt-out of all assets with zero balance.",
)
@click.option(
    "-n",
    "--network",
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def opt_out_command(asset_ids: str, account: str, network: str, all_assets: bool) -> None:  # noqa: FBT001
    if not (all_assets or asset_ids):
        raise click.UsageError("asset_ids or --all must be specified")
    opt_out_account = get_account_with_private_key(account)
    validate_address(opt_out_account.address)
    algod_client = load_algod_client(network)
    asset_ids_list = []
    try:
        if all_assets:
            account_info = algod_client.account_info(opt_out_account.address)
            for asset in account_info.get("assets", []):  # type: ignore  # noqa: PGH003
                if asset["amount"] == 0:
                    asset_ids_list.append(int(asset["asset-id"]))
        else:
            for asset_id in asset_ids.split(","):
                asset_ids_list.append(int(asset_id.strip()))

        opt_out(algod_client=algod_client, account=opt_out_account, asset_ids=asset_ids_list)
        click.echo("Successfully performed opt-out.")

    except error.AlgodHTTPError as err:
        raise click.ClickException(str(err)) from err

    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform opt-out.") from err
