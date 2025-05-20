import json
import re
from pathlib import Path

import click
import pytest
from algokit.cli.tasks.mint import _get_and_validate_asset_name, _get_and_validate_decimals
from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from algosdk.mnemonic import from_private_key
from approvaltests.namer import NamerFactory
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.tasks.conftest import DUMMY_ACCOUNT, DUMMY_SUGGESTED_PARAMS
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.parametrize(("account_type", "mutability"), [("alias", "mutable"), ("address", "immutable")])
@pytest.mark.parametrize("network", ["localnet", "testnet", "mainnet"])
def test_mint_token_successful(
    *,
    mocker: MockerFixture,
    tmp_path_factory: pytest.TempPathFactory,
    mock_keyring: dict[str, str | int],
    account_type: str,
    mutability: str,
    network: str,
) -> None:
    # Arrange
    is_mutable = mutability == "mutable"
    cwd = tmp_path_factory.mktemp("cwd")
    account = ""
    prompt_input = None
    if account_type == "address":
        account = DUMMY_ACCOUNT.address
        prompt_input = from_private_key(DUMMY_ACCOUNT.private_key)  # type: ignore[no-untyped-call]
    else:
        account = "my_alias"
        mock_keyring[account] = json.dumps(
            {
                "alias": account,
                "address": DUMMY_ACCOUNT.address,
                "private_key": DUMMY_ACCOUNT.private_key,
            }
        )
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([account])
    (cwd / "image.png").touch()

    mocker.patch(
        "algokit.core.tasks.mint.mint.upload_to_pinata",
        side_effect=[
            "bafkreifax6dswcxk4us2am3jxhd3swxew32oreaxzol7dnnqzhieepqg2y",
            "bafkreiftmc4on252dnckhv7jdqnhkxjkpvlrekpevjwm3gjszygxkus5oe",
        ],
    )
    mocker.patch("algokit.core.tasks.mint.mint.wait_for_confirmation", return_value={"asset-index": 123})
    mocker.patch(
        "algokit.cli.tasks.mint.get_pinata_jwt",
        return_value="dummy_key",
    )
    mocker.patch(
        "algokit.cli.tasks.mint.validate_balance",
    )
    algod_mock = mocker.MagicMock()
    algod_mock.send_transaction.return_value = "dummy_tx_id"
    algod_mock.suggested_params.return_value = DUMMY_SUGGESTED_PARAMS
    mocker.patch("algokit.cli.tasks.mint.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke(
        f"""task mint --creator {account} --name test --unit tst --total 1 --decimals 0
        --image image.png -n {network} --{"mutable" if is_mutable else "immutable"} --nft""",
        input=prompt_input,
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 0
    if is_mutable:
        # Reserve value must be set since its a mutable asset
        assert (
            re.search(r'"reserve": ".{58}"', result.output) is not None
        ), "Reserve key not found or addr length is not 58"
    else:
        assert re.search(r'"reserve": ""', result.output) is not None, "Reserve key must be empty"
    verify(result.output, options=NamerFactory.with_parameters(account_type, is_mutable, network))


@pytest.mark.parametrize("decimals", ["decimals_given_params", "no_decimals_given"])
def test_mint_token_successful_on_decimals(
    *,
    mocker: MockerFixture,
    tmp_path_factory: pytest.TempPathFactory,
    mock_keyring: dict[str, str | int],
    decimals: str,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    if decimals == "no_decimals_given":
        include_decimals_argument = False
        prompt_input = "2"
    elif decimals == "decimals_given_params":
        include_decimals_argument = True
        prompt_input = None

    account = "my_alias"
    mock_keyring[account] = json.dumps(
        {
            "alias": account,
            "address": DUMMY_ACCOUNT.address,
            "private_key": DUMMY_ACCOUNT.private_key,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([account])

    (cwd / "image.png").touch()

    mocker.patch(
        "algokit.core.tasks.mint.mint.upload_to_pinata",
        side_effect=[
            "bafkreifax6dswcxk4us2am3jxhd3swxew32oreaxzol7dnnqzhieepqg2y",
            "bafkreiftmc4on252dnckhv7jdqnhkxjkpvlrekpevjwm3gjszygxkus5oe",
        ],
    )
    mocker.patch("algokit.core.tasks.mint.mint.wait_for_confirmation", return_value={"asset-index": 123})
    mocker.patch(
        "algokit.cli.tasks.mint.get_pinata_jwt",
        return_value="dummy_key",
    )
    mocker.patch(
        "algokit.cli.tasks.mint.validate_balance",
    )
    algod_mock = mocker.MagicMock()
    algod_mock.send_transaction.return_value = "dummy_tx_id"
    algod_mock.suggested_params.return_value = DUMMY_SUGGESTED_PARAMS
    mocker.patch("algokit.cli.tasks.mint.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke(
        f"""task mint --creator {account} --name test --unit tst --total 100
        {"--decimals 2 " if include_decimals_argument else ""}
        --image image.png -n localnet --mutable --nft""",
        input=prompt_input,
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(decimals))


def test_mint_token_pure_fractional_nft_ft_validation(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    network = "localnet"
    cwd = tmp_path_factory.mktemp("cwd")
    account = DUMMY_ACCOUNT.address
    prompt_input = from_private_key(DUMMY_ACCOUNT.private_key)  # type: ignore[no-untyped-call]
    (cwd / "image.png").touch()

    # Act
    nft_result = invoke(
        f"""task mint --creator {account} --name test --unit tst --total 222 --decimals 12
        --image image.png -n {network} --mutable --nft""",
        input=prompt_input,
        cwd=cwd,
    )

    # Assert
    assert nft_result.exit_code == 1


def test_mint_token_pinata_error(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    account = ""
    account = DUMMY_ACCOUNT.address
    prompt_input = from_private_key(DUMMY_ACCOUNT.private_key)  # type: ignore[no-untyped-call]
    (cwd / "image.png").touch()
    httpx_mock.add_response(status_code=403, json={"ok": False})

    mocker.patch(
        "algokit.cli.tasks.mint.get_pinata_jwt",
        return_value="dummy_key",
    )
    mocker.patch(
        "algokit.cli.tasks.mint.validate_balance",
    )
    algod_mock = mocker.MagicMock()
    mocker.patch("algokit.cli.tasks.mint.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke(
        f"""task mint --creator {account} --name test --unit tst --total 1 --decimals 0
        --image image.png -n localnet --mutable --nft""",
        input=prompt_input,
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)


def test_mint_token_no_pinata_jwt_error(
    mocker: MockerFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    account = ""
    account = DUMMY_ACCOUNT.address
    prompt_input = from_private_key(DUMMY_ACCOUNT.private_key)  # type: ignore[no-untyped-call]
    (cwd / "image.png").touch()

    mocker.patch(
        "algokit.cli.tasks.mint.get_pinata_jwt",
        return_value=None,
    )
    # Act
    result = invoke(
        f"""task mint --creator {account} --name test --unit tst --total 1 --decimals 0
        --image image.png -n localnet --mutable --nft""",
        cwd=cwd,
        input=prompt_input,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)


def test_mint_token_acfg_token_metadata_mismatch_on_name(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "metadata.json").write_text(
        """
        {
        "name": "test2",
        "decimals": 2,
        "description": "Stars",
        "properties": {
            "author": "Al",
            "traits": {
            "position": "center",
            "colors": 4
            }
        }
        }
        """
    )
    context = click.Context(click.Command("mint"))
    context.params["token_metadata_path"] = Path(cwd / "metadata.json")
    param = click.Option(["--name"])
    name = "test"

    with pytest.raises(
        click.BadParameter, match="Token name in metadata JSON must match CLI argument providing token name!"
    ):
        _get_and_validate_asset_name(context, param, name)


def test_mint_token_acfg_token_metadata_mismatch_on_decimals(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "metadata.json").write_text(
        """
        {
        "name": "test2",
        "decimals": 2,
        "description": "Stars",
        "properties": {
            "author": "Al",
            "traits": {
            "position": "center",
            "colors": 4
            }
        }
        }
        """
    )
    context = click.Context(click.Command("mint"))
    context.params["token_metadata_path"] = Path(cwd / "metadata.json")
    param = click.Option(["--decimals"])
    decimals = 0

    with pytest.raises(
        click.BadParameter, match="The value for decimals in the metadata JSON must match the decimals argument"
    ):
        _get_and_validate_decimals(context, param, decimals)
