from algokit_utils import Account
from algosdk import transaction

DUMMY_SUGGESTED_PARAMS = transaction.SuggestedParams(  # type: ignore[no-untyped-call]
    fee=0,
    first=33652328,
    last=33653328,
    gen="testnet-v1.0",
    gh="SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
    min_fee=1000,
    flat_fee=True,
    consensus_version="https://github.com/algorandfoundation/specs/tree/abd3d4823c6f77349fc04c3af7b1e99fe4df699f",
)
DUMMY_ACCOUNT = Account(
    private_key="iLsfFiRDwi0ijFdvdyO1PGkYxooOanbJSgpJ4pPKjKZluk70pvuPX4dYD1Jir85uZP+AImM/8SBmdPRpBSTFAg==",
    address="MW5E55FG7OHV7B2YB5JGFL6ONZSP7ABCMM77CIDGOT2GSBJEYUBOF3UYKA",
)
