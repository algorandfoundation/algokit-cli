import json
import logging
from dataclasses import dataclass

import keyring

logger = logging.getLogger(__name__)

WALLET_ALIAS_KEYRING_NAMESPACE = "algokit_wallet_alias"
WALLET_ALIASES_KEYRING_NAMESPACE = "algokit_wallet_aliases"
WALLET_ALIASES_KEYRING_USERNAME = "all_aliases"


@dataclass
class WalletAliasKeyringData:
    alias: str
    address: str
    private_key: str | None


def _get_alias_keys() -> list[str]:
    try:
        response = keyring.get_password(WALLET_ALIASES_KEYRING_NAMESPACE, username=WALLET_ALIASES_KEYRING_USERNAME)

        if not response:
            return []

        alias_keys: list[str] = json.loads(response)
        return alias_keys
    except Exception as ex:
        logger.debug("Failed to get alias keys from keyring", exc_info=ex)
        return []


def _add_alias_key(alias_name: str) -> None:
    alias_keys = _get_alias_keys()

    if alias_name not in alias_keys:
        alias_keys.append(alias_name)

    keyring.set_password(
        WALLET_ALIASES_KEYRING_NAMESPACE,
        username=WALLET_ALIASES_KEYRING_USERNAME,
        password=json.dumps(alias_keys),
    )


def _remove_alias_key(alias_name: str) -> None:
    alias_keys = _get_alias_keys()

    if alias_name in alias_keys:
        alias_keys.remove(alias_name)

    keyring.set_password(
        WALLET_ALIASES_KEYRING_NAMESPACE,
        username=WALLET_ALIASES_KEYRING_USERNAME,
        password=json.dumps(alias_keys),
    )


def add_alias(alias_name: str, address: str, private_key: str | None) -> None:
    """Add an address or account to be stored against a named alias in keyring."""
    keyring.set_password(
        WALLET_ALIAS_KEYRING_NAMESPACE,
        alias_name,
        json.dumps(
            WalletAliasKeyringData(
                alias=alias_name,
                address=address,
                private_key=private_key,
            ).__dict__
        ),
    )
    _add_alias_key(alias_name)


def get_alias(alias_name: str) -> WalletAliasKeyringData | None:
    """Get the address or account stored against a named alias in keyring."""
    try:
        response = keyring.get_password(WALLET_ALIAS_KEYRING_NAMESPACE, alias_name)

        if not response:
            return None

        return WalletAliasKeyringData(**json.loads(response))
    except Exception as ex:
        logger.debug("Failed to get alias from keyring", exc_info=ex)
        return None


def get_aliases() -> list[WalletAliasKeyringData]:
    try:
        alias_keys = _get_alias_keys()
        response = []

        for alias_name in alias_keys:
            alias_data = get_alias(alias_name)
            if alias_data:
                response.append(alias_data)

        return response
    except Exception as ex:
        logger.debug("Failed to get aliases from keyring", exc_info=ex)
        return []


def remove_alias(alias_name: str) -> None:
    """Remove an address or account stored against a named alias in keyring."""
    keyring.delete_password(WALLET_ALIAS_KEYRING_NAMESPACE, alias_name)
    _remove_alias_key(alias_name)
