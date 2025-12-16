"""SigningAccount compatibility class for CLI.

This module provides a SigningAccount class that mimics the old algokit-utils
SigningAccount interface for CLI compatibility during the migration to the
new decoupled architecture.
"""

from dataclasses import dataclass, field

from algokit_utils.transact import TransactionSigner, make_basic_account_transaction_signer


@dataclass
class SigningAccount:
    """A simple account with signing capability.

    This class provides compatibility with the old algokit-utils SigningAccount
    interface while working with the new decoupled architecture.

    Attributes:
        address: The Algorand address of the account.
        private_key: The private key of the account (base64-encoded string or hex string).
    """

    address: str
    private_key: str
    _signer: TransactionSigner | None = field(default=None, repr=False, compare=False)

    @property
    def signer(self) -> TransactionSigner:
        """Get a transaction signer for this account."""
        if self._signer is None:
            object.__setattr__(self, "_signer", make_basic_account_transaction_signer(self.private_key))
        return self._signer  # type: ignore[return-value]
