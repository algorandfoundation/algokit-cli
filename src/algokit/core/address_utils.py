"""Address utilities for the CLI.

This module provides address validation and derivation utilities using algokit_common.
"""

import base64

from algokit_utils.common import (
    ADDRESS_LENGTH,
    address_from_public_key,
    public_key_from_address,
)

# Standard Algorand address length (58 characters)
ALGORAND_ADDRESS_LENGTH = ADDRESS_LENGTH


def is_valid_address(address: str) -> bool:
    """Check if an address is a valid Algorand address.

    Args:
        address: The address string to validate.

    Returns:
        True if the address is valid, False otherwise.
    """
    if len(address) != ADDRESS_LENGTH:
        return False

    try:
        # public_key_from_address will raise if invalid
        public_key_from_address(address)
        return True
    except Exception:
        return False


def address_from_private_key(private_key: str) -> str:
    """Derive the address from a private key.

    The private key is expected to be a base64-encoded string of 64 bytes
    (32-byte seed + 32-byte public key).

    Args:
        private_key: Base64-encoded private key string.

    Returns:
        The Algorand address corresponding to the private key.
    """
    # Decode the base64 private key
    key_bytes = base64.b64decode(private_key)

    # Extract the public key (last 32 bytes of the 64-byte key)
    public_key = key_bytes[32:64]

    # Derive the address from the public key
    return address_from_public_key(public_key)
