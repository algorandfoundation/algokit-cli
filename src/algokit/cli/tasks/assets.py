import logging

import click
from algokit_utils import opt_in, opt_out
from algosdk import error
from algosdk.v2client.algod import AlgodClient

from algokit.cli.common.constants import AlgorandNetwork, ExplorerEntityType
from algokit.cli.common.utils import get_explorer_url
from algokit.cli.tasks.utils import (
    get_account_info,
    get_account_with_private_key,
    load_algod_client,
    validate_account_balance_to_opt_in,
    validate_address,
)

logger = logging.getLogger(__name__)


def _get_zero_balanced_assets(
    *, provided_asset_ids: tuple[int], address: str, algod_client: AlgodClient, all_assets: bool = False
) -> list[int]:
    asset_ids_list = []
    if all_assets:
        account_info = get_account_info(algod_client, address)
        for asset in account_info.get("assets", []):
            if asset.get("amount", 0) == 0:
                asset_ids_list.append(int(asset["asset-id"]))
    else:
        for asset_id in provided_asset_ids:
            asset_ids_list.append(asset_id)

    return asset_ids_list


@click.command(
    name="opt-in",
    help="Opt-in to an asset(s). This is required before you can receive an asset. "
    "Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.",
)
@click.argument("asset_ids", type=click.INT, required=True, nargs=-1)
@click.option("--account", "-a", type=click.STRING, required=True, help="Address or alias of the signer account.")
@click.option(
    "-n",
    "--network",
    type=click.Choice(AlgorandNetwork.to_list()),
    default=AlgorandNetwork.LOCALNET,
    required=False,
    help=f"Network to use. Refers to `{AlgorandNetwork.LOCALNET}` by default.",
)
def opt_in_command(asset_ids: tuple[int], account: str, network: AlgorandNetwork) -> None:
    asset_ids_list = list(asset_ids)

    opt_in_account = get_account_with_private_key(account)
    validate_address(opt_in_account.address)
    algod_client = load_algod_client(network)

    validate_account_balance_to_opt_in(algod_client, opt_in_account, len(asset_ids_list))
    try:
        click.echo("Performing opt-in. This may take a few seconds...")
        response = opt_in(algod_client=algod_client, account=opt_in_account, asset_ids=asset_ids_list)
        click.echo("Successfully performed opt-in.")
        if len(response) > 1:
            account_url = get_explorer_url(opt_in_account.address, network, ExplorerEntityType.ADDRESS)
            click.echo(f"Check latest transactions on your account at: {account_url}")
        else:
            for asset_id, txn_id in response.items():
                explorer_url = get_explorer_url(txn_id, network, ExplorerEntityType.ASSET)
                click.echo(f"Check opt-in status for asset {asset_id} at: {explorer_url}")
    except error.AlgodHTTPError as err:
        raise click.ClickException(str(err)) from err
    except ValueError as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException(str(err)) from err
    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform opt-in") from err


@click.command(
    name="opt-out",
    help="opt-out of an asset(s). You can only opt out of an asset with a zero balance. "
    "Use -n to specify localnet, testnet, or mainnet. To supply multiple asset IDs, separate them with a whitespace.",
)
@click.argument("asset_ids", type=click.INT, required=False, nargs=-1)
@click.option("--account", "-a", type=click.STRING, required=True, help="Address or alias of the signer account.")
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
    type=click.Choice(AlgorandNetwork.to_list()),
    default=AlgorandNetwork.LOCALNET,
    required=False,
    help=f"Network to use. Refers to `{AlgorandNetwork.LOCALNET}` by default.",
)
def opt_out_command(*, asset_ids: tuple[int], account: str, network: AlgorandNetwork, all_assets: bool) -> None:
    if not (all_assets or asset_ids):
        raise click.UsageError("asset_ids or --all must be specified")
    opt_out_account = get_account_with_private_key(account)
    validate_address(opt_out_account.address)
    algod_client = load_algod_client(network)
    asset_ids_list = []
    try:
        asset_ids_list = _get_zero_balanced_assets(
            provided_asset_ids=asset_ids,
            address=opt_out_account.address,
            algod_client=algod_client,
            all_assets=all_assets,
        )

        if not asset_ids_list:
            raise click.ClickException("No assets to opt-out of.")

        click.echo("Performing opt-out. This may take a few seconds...")
        response = opt_out(algod_client=algod_client, account=opt_out_account, asset_ids=asset_ids_list)
        click.echo("Successfully performed opt-out.")
        if len(response) > 1:
            account_url = get_explorer_url(opt_out_account.address, network, ExplorerEntityType.ADDRESS)
            click.echo(f"Check latest transactions on your account at: {account_url}")
        else:
            asset_id, txn_id = response.popitem()
            transaction_url = get_explorer_url(txn_id, network, ExplorerEntityType.TRANSACTION)
            click.echo(f"Check opt-in status for asset {asset_id} at: {transaction_url}")
    except error.AlgodHTTPError as err:
        raise click.ClickException(str(err)) from err
    except ConnectionRefusedError as err:
        raise click.ClickException(str(err)) from err
    except ValueError as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException(str(err)) from err
    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform opt-out.") from err
