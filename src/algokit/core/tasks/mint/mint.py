import base64
import hashlib
import json
import logging
import mimetypes
import pathlib
import re

from algokit_common import address_from_public_key, sha512_256
from algokit_utils.clients import AlgodClient, algod_models
from algokit_utils.transact import get_transaction_id, make_basic_account_transaction_signer
from algokit_utils.transactions.builders.asset import build_asset_create_transaction
from algokit_utils.transactions.types import AssetCreateParams
from multiformats import CID

from algokit.core.signing_account import SigningAccount
from algokit.core.tasks.ipfs import upload_to_pinata
from algokit.core.tasks.mint.models import TokenMetadata

logger = logging.getLogger(__name__)


def _reserve_address_from_cid(cid: str) -> str:
    """
    Returns the reserve address associated with a given CID (Content Identifier).

    Args:
        cid (str): The CID for which the reserve address needs to be determined.

    Returns:
        str: The reserve address associated with the given CID.
    """

    # Workaround to fix `multiformats` package issue, remove first two bytes before using `encode_address`.
    # Initial fix using `py-multiformats-cid` and `multihash.decode` was dropped due to PEP 517 incompatibility.
    digest = CID.decode(cid).digest[2:]
    return address_from_public_key(digest)


def _create_url_from_cid(cid: str) -> str:
    """
    Creates an ARC19 asset template URL based on the given CID (Content Identifier).

    Args:
        cid (str): The CID for which the URL needs to be created.

    Returns:
        str: The URL created based on the given CID.

    Raises:
        AssertionError: If the constructed URL does not match the expected format.
    """

    cid_object = CID.decode(cid)
    version = cid_object.version
    codec = cid_object.codec.name
    hash_function_name = cid_object.hashfun.name

    url = f"template-ipfs://{{ipfscid:{version}:{codec}:reserve:{hash_function_name}}}"
    valid = re.compile(
        r"template-ipfs://{ipfscid:(?P<version>[01]):(?P<codec>[a-z0-9\-]+):(?P<field>[a-z0-9\-]+):(?P<hash>[a-z0-9\-]+)}"
    )
    assert bool(valid.match(url))
    return url


def _file_integrity(filename: pathlib.Path) -> str:
    """
    Calculate the SHA-256 hash of a file to ensure its integrity.

    Args:
        filename (pathlib.Path): The path to the file for which the integrity needs to be calculated.

    Returns:
        str: The integrity of the file in the format "sha-256<hash>".
    """
    with filename.open("rb") as f:
        file_bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(file_bytes).hexdigest()
        return "sha-256" + readable_hash


def _file_mimetype(filename: pathlib.Path) -> str:
    """
    Returns the MIME type of a file based on its extension.

    Args:
        filename (pathlib.Path): The path to the file.

    Returns:
        str: The MIME type of the file.
    """
    extension = pathlib.Path(filename).suffix
    return mimetypes.types_map[extension]


def _wait_for_confirmation(client: AlgodClient, txid: str, rounds: int) -> algod_models.PendingTransactionResponse:
    """Wait for transaction confirmation.

    Args:
        client: AlgodClient instance
        txid: Transaction ID to wait for
        rounds: Maximum number of rounds to wait

    Returns:
        algod_models.PendingTransactionResponse: Transaction confirmation info

    Raises:
        Exception: If transaction is rejected or not confirmed in time
    """
    status = client.status()
    last_round = getattr(status, "last_round", 0)
    current_round = last_round

    while current_round <= last_round + rounds:
        txinfo = client.pending_transaction_information(txid)
        confirmed_round = getattr(txinfo, "confirmed_round", None)
        if confirmed_round is not None and confirmed_round > 0:
            return txinfo
        pool_error = getattr(txinfo, "pool_error", None)
        if pool_error:
            raise Exception(f"Transaction rejected: {pool_error}")
        current_round += 1
        client.status_after_block(current_round)

    raise Exception(f"Transaction {txid} not confirmed after {rounds} rounds")


def _compute_metadata_hash(
    *,
    token_metadata: TokenMetadata,
    use_metadata_hash: bool = True,
) -> bytes:
    """
    Compute the metadata hash for an asset.

    Args:
        token_metadata (TokenMetadata): An instance of the TokenMetadata class that contains the metadata for the asset.
        use_metadata_hash (bool, optional): A boolean flag indicating whether to use the metadata hash.
        Defaults to True.

    Returns:
        bytes: The computed metadata hash, or empty bytes if use_metadata_hash is False.
    """
    if not use_metadata_hash:
        return b""

    json_metadata = token_metadata.to_json()
    json_metadata_bytes = json_metadata.encode("utf-8")
    metadata = json.loads(json_metadata)

    if "extra_metadata" in metadata:
        json_metadata_hash = sha512_256(b"arc0003/amj" + json_metadata_bytes)

        return sha512_256(b"arc0003/am" + json_metadata_hash + base64.b64decode(metadata["extra_metadata"]))
    else:
        return hashlib.sha256(json_metadata_bytes).digest()


def mint_token(  # noqa: PLR0913
    *,
    client: AlgodClient,
    jwt: str,
    creator_account: SigningAccount,
    unit_name: str,
    total: int,
    token_metadata: TokenMetadata,
    mutable: bool,
    image_path: pathlib.Path | None = None,
) -> tuple[int, str]:
    """
    Mint new token on the Algorand blockchain.

    Args:
        client (AlgodClient): An instance of the `AlgodClient` class representing the Algorand node.
        jwt (str): The JWT for accessing the Piñata API.
        creator_account (SigningAccount): An instance of the `SigningAccount` class representing the account that
        will create the token.
        unit_name (str): A string representing the unit name of the token.
        total (int): An integer representing the total supply of the token.
        token_metadata (TokenMetadata): An instance of the `TokenMetadata` class representing the metadata of the token.
        mutable (bool): A boolean indicating whether the token is mutable or not.
        image_path (pathlib.Path | None, optional): A `pathlib.Path` object representing the path to the
        image file associated with the token. Defaults to None.

    Returns:
        tuple[int, str]: A tuple containing the asset index and transaction ID of the minted token.
    """

    if image_path:
        token_metadata.image_integrity = _file_integrity(image_path)
        token_metadata.image_mimetype = _file_mimetype(image_path)
        logger.info("Uploading image to pinata...")
        token_metadata.image = "ipfs://" + upload_to_pinata(image_path, jwt=jwt)
        logger.info(f"Image uploaded to pinata: {token_metadata.image}")

    logger.info("Uploading metadata to pinata...")
    metadata_cid = upload_to_pinata(
        token_metadata.to_file_path(),
        jwt=jwt,
    )
    logger.info(f"Metadata uploaded to pinata: {metadata_cid}")

    # Compute metadata hash
    metadata_hash = _compute_metadata_hash(
        token_metadata=token_metadata,
        use_metadata_hash=not mutable,
    )

    # Build asset creation parameters
    asset_create_params = AssetCreateParams(
        sender=creator_account.address,
        total=total,
        decimals=token_metadata.decimals,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=token_metadata.name,
        url=_create_url_from_cid(metadata_cid) + "#arc3" if mutable else "ipfs://" + metadata_cid + "#arc3",
        metadata_hash=metadata_hash if metadata_hash else None,
        manager=creator_account.address if mutable else None,
        reserve=_reserve_address_from_cid(metadata_cid) if mutable else None,
        freeze=None,
        clawback=None,
    )

    logger.debug(
        "Asset config params: "
        + json.dumps(
            {
                "sender": asset_create_params.sender,
                "unit_name": asset_create_params.unit_name or "",
                "asset_name": asset_create_params.asset_name or "",
                "url": asset_create_params.url or "",
                "manager": asset_create_params.manager or "",
                "reserve": asset_create_params.reserve or "",
                "total": asset_create_params.total,
                "freeze": asset_create_params.freeze or "",
                "clawback": asset_create_params.clawback or "",
                "metadata_hash": base64.b64encode(asset_create_params.metadata_hash).decode("ascii")
                if asset_create_params.metadata_hash
                else None,
                "note": "",
                "decimals": asset_create_params.decimals,
                "default_frozen": asset_create_params.default_frozen or False,
                "lease": "",
                "rekey_to": "",
                "strict_empty_address_check": False,
            },
            indent=4,
        )
    )

    # Build the transaction
    suggested_params = client.suggested_params()
    built_txn = build_asset_create_transaction(
        params=asset_create_params,
        suggested_params=suggested_params,
        default_validity_window=1000,
        default_validity_window_is_explicit=False,
        is_localnet=False,
    )

    # Sign the transaction
    signer = make_basic_account_transaction_signer(creator_account.private_key)
    signed_txn_bytes = signer([built_txn.txn], [0])[0]

    # Send the transaction (signer returns encoded signed transaction bytes)
    txid = get_transaction_id(built_txn.txn)
    client.send_raw_transaction(signed_txn_bytes)

    # Wait for confirmation
    response = _wait_for_confirmation(client, txid, 4)

    asset_index = getattr(response, "asset_index", None)
    if asset_index is None:
        raise Exception("Asset creation failed: no asset-index in response")

    return asset_index, txid
