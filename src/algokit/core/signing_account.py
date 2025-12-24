"""SigningAccount compatibility class for CLI.

This module provides a SigningAccount class that mimics the old algokit-utils
SigningAccount interface for CLI compatibility during the migration to the
new decoupled architecture.
"""

from algokit_utils.transact import make_basic_account_transaction_signer


class SigningAccount:
    """A simple account with signing capability.

    This class provides compatibility with the old algokit-utils SigningAccount
    interface while working with the new decoupled architecture.

    Attributes:
        address: The Algorand address of the account.
        signer: A TransactionSigner from supplied private key
    """

    def __init__(self, address: str, private_key: str) -> None:
        self.address = address
        self.signer = make_basic_account_transaction_signer(private_key)
