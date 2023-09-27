import json
import logging
from dataclasses import dataclass

import keyring

logger = logging.getLogger(__name__)

WALLET_ALIAS_KEYRING_NAMESPACE = "algokit_alias"
WALLET_ALIASES_KEYRING_NAMESPACE = "algokit_aliases"
WALLET_ALIASES_KEYRING_USERNAME = "aliases"

# Windows Credentials locker has a max limit of 1280 chars per password length.
# Given that each alias is at most 20 chars, around ~50 alias keys can be stored within single password field.
# Hence the limitation of 50 aliases.
WALLET_ALIASING_MAX_LIMIT = 50


@dataclass
class WalletAliasKeyringData:
    alias: str
    address: str
    private_key: str | None


class WalletAliasingLimitError(Exception):
    pass


def _get_alias_keys() -> list[str]:
    try:
        response = keyring.get_password(
            service_name=WALLET_ALIASES_KEYRING_NAMESPACE, username=WALLET_ALIASES_KEYRING_USERNAME
        )

        if not response:
            return []

        alias_keys: list[str] = json.loads(response)
        return alias_keys
    except Exception as ex:
        logger.debug("Failed to get alias keys from keyring", exc_info=ex)
        return []


def _update_alias_keys(alias_keys: list[str]) -> None:
    keyring.set_password(
        service_name=WALLET_ALIASES_KEYRING_NAMESPACE,
        username=WALLET_ALIASES_KEYRING_USERNAME,
        password=json.dumps(alias_keys, separators=(",", ":")),
    )


def _add_alias_key(alias_name: str) -> None:
    alias_keys = _get_alias_keys()

    if len(alias_keys) >= WALLET_ALIASING_MAX_LIMIT:
        raise WalletAliasingLimitError("You have reached the maximum number of aliases.")

    if alias_name not in alias_keys:
        alias_keys.append(alias_name)

    _update_alias_keys(alias_keys)


def _remove_alias_key(alias_name: str) -> None:
    alias_keys = _get_alias_keys()

    if alias_name in alias_keys:
        alias_keys.remove(alias_name)

    _update_alias_keys(alias_keys)


def add_alias(alias_name: str, address: str, private_key: str | None) -> None:
    """
    Add an address or account to be stored against a named alias in keyring.

    Args:
        alias_name (str): The name of the alias to be added.
        address (str): The address or account to be stored against the alias.
        private_key (str | None): The private key associated with the address or account.
        It can be None if no private key is available.

    Raises:
        WalletAliasingLimitError: If the maximum number of aliases has been reached.

    """

    try:
        _add_alias_key(alias_name)
        keyring.set_password(
            service_name=WALLET_ALIAS_KEYRING_NAMESPACE,
            username=alias_name,
            password=json.dumps(
                WalletAliasKeyringData(
                    alias=alias_name,
                    address=address,
                    private_key=private_key,
                ).__dict__
            ),
        )
    except Exception as ex:
        logger.debug("Failed to add alias to keyring", exc_info=ex)
        raise ex


def get_alias(alias_name: str) -> WalletAliasKeyringData | None:
    """
    Get the address or account stored against a named alias in the keyring.

    Args:
        alias_name (str): The name of the alias to retrieve.

    Returns:
        WalletAliasKeyringData | None: An instance of the WalletAliasKeyringData class if the alias exists,
        otherwise None.

    Example Usage:
        alias_data = get_alias("my_alias")
        if alias_data:
            print(alias_data.address)
    """

    try:
        response = keyring.get_password(service_name=WALLET_ALIAS_KEYRING_NAMESPACE, username=alias_name)

        if not response:
            return None

        return WalletAliasKeyringData(**json.loads(response))
    except Exception as ex:
        logger.debug(f"`{alias_name}` does not exist", exc_info=ex)
        return None


def get_aliases() -> list[WalletAliasKeyringData]:
    """
    Retrieves a list of wallet aliases and their associated data from a keyring.

    Returns:
        A list of WalletAliasKeyringData objects representing the aliases and their associated data.
    """

    try:
        alias_keys = _get_alias_keys()
        response: list[WalletAliasKeyringData] = []

        for alias_name in alias_keys:
            alias_data = get_alias(alias_name)
            if alias_data:
                response.append(alias_data)

        return response
    except Exception as ex:
        logger.debug("Failed to get aliases from keyring", exc_info=ex)
        return []


def remove_alias(alias_name: str) -> None:
    """
    Remove an address or account stored against a named alias in keyring.

    :param alias_name: The name of the alias to be removed.
    :type alias_name: str
    """

    keyring.delete_password(service_name=WALLET_ALIAS_KEYRING_NAMESPACE, username=alias_name)
    _remove_alias_key(alias_name)
