import algosdk
import click
from algokit_utils import Account, get_algod_client, get_algonode_config, get_default_localnet_config, opt_in


def _validate_address(address: str) -> None:
    if not algosdk.encoding.is_valid_address(address):  # type: ignore[no-untyped-call]
        raise click.ClickException(f"{address} is an invalid account address")


# Do we need to get the private key for opt in?
def _get_private_key_from_mnemonic() -> str:
    mnemonic_phrase = click.prompt("Enter the mnemonic phrase (25 words separated by whitespace)", hide_input=True)
    try:
        return str(algosdk.mnemonic.to_private_key(mnemonic_phrase))  # type: ignore[no-untyped-call]
    except Exception as err:
        raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err


def _get_algod_client(network: str) -> algosdk.v2client.algod.AlgodClient:
    network_mapping = {
        "localnet": get_algod_client(get_default_localnet_config("algod")),
        "testnet": get_algod_client(get_algonode_config("testnet", "algod", "")),
        "mainnet": get_algod_client(get_algonode_config("mainnet", "algod", "")),
    }
    try:
        return network_mapping[network]
    except KeyError as err:
        raise click.ClickException("Invalid network") from err


def _is_opt_in(account: Account, algod_client: algosdk.v2client.algod.AlgodClient, asset_id: int) -> None:
    account_info = algod_client.account_info(account.address)
    if not isinstance(account_info, dict):
        raise click.ClickException("Invalid account info response")

    asset_record = next((asset for asset in account_info.get("assets", []) if asset["asset-id"] == asset_id), None)
    if not asset_record:
        raise click.ClickException("this account is not opted into the asset")


def _get_account(sender: str) -> Account:
    _validate_address(sender)
    pk = _get_private_key_from_mnemonic()
    return Account(address=sender, private_key=pk)


@click.command(name="opt-in", help="Opt-in to an asset. This is required before you can receive an asset. ")
@click.argument("asset_id", type=click.INT, help="Asset ID to opt-in for")
@click.argument("account", type=click.STRING, help="Alias or Wallet for the account")
@click.option(
    "--network", "-n", type=click.Choice(["localnet", "testnet", "mainnet"]), default="localnet", required=True
)
def opt_in_command(asset_id: int, account: str, network: str) -> None:
    account = (account or "").strip('"')
    # what to name the account variable?
    the_account = _get_account(account)

    algod_client = _get_algod_client(network)
    _is_opt_in(the_account, algod_client, asset_id)

    try:
        opt_in(algod_client=algod_client, account=the_account, asset_id=asset_id)
    except Exception as err:
        raise click.ClickException(f"Failed to opt-in to asset {asset_id}") from err
