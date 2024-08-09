import base64
import hashlib
import json
import logging
import mimetypes
import pathlib
import re
from dataclasses import asdict

from algokit_utils import Account
from algosdk import encoding, transaction
from algosdk.transaction import wait_for_confirmation
from algosdk.v2client import algod
from multiformats import CID

from algokit.core.tasks.ipfs import upload_to_pinata
from algokit.core.tasks.mint.models import AssetConfigTxnParams, TokenMetadata

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
    reserve_address = str(encoding.encode_address(digest))  # type: ignore[no-untyped-call]
    assert encoding.is_valid_address(reserve_address)  # type: ignore[no-untyped-call]
    return reserve_address


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


def _create_asset_txn(
    *,
    asset_config_params: AssetConfigTxnParams,
    token_metadata: TokenMetadata,
    use_metadata_hash: bool = True,
) -> transaction.AssetConfigTxn:
    """
    Create an instance of the AssetConfigTxn class by setting the parameters and metadata
    for the asset configuration transaction.

    Args:
        asset_config_params (AssetConfigTxnParams): An instance of the AssetConfigTxnParams class
        that contains the parameters for the asset configuration transaction.
        token_metadata (TokenMetadata): An instance of the TokenMetadata class that contains the metadata for the asset.
        use_metadata_hash (bool, optional): A boolean flag indicating whether to use the metadata hash
        in the asset configuration transaction. Defaults to True.

    Returns:
        AssetConfigTxn: An instance of the AssetConfigTxn class representing the asset configuration transaction.
    """
    json_metadata = token_metadata.to_json()
    metadata = json.loads(json_metadata)

    if use_metadata_hash:
        if "extra_metadata" in metadata:
            h = hashlib.new("sha512_256")
            h.update(b"arc0003/amj")
            h.update(json_metadata.encode("utf-8"))
            json_metadata_hash = h.digest()

            h = hashlib.new("sha512_256")
            h.update(b"arc0003/am")

            h.update(json_metadata_hash)
            h.update(base64.b64decode(metadata["extra_metadata"]))
            asset_config_params.metadata_hash = h.digest()
        else:
            h = hashlib.new("sha256")
            h.update(json_metadata.encode("utf-8"))
            asset_config_params.metadata_hash = h.digest()
    else:
        asset_config_params.metadata_hash = b""

    return transaction.AssetConfigTxn(**asdict(asset_config_params))  # type: ignore[no-untyped-call]


def mint_token(  # noqa: PLR0913
    *,
    client: algod.AlgodClient,
    jwt: str,
    creator_account: Account,
    unit_name: str,
    total: int,
    token_metadata: TokenMetadata,
    mutable: bool,
    image_path: pathlib.Path | None = None,
) -> tuple[int, str]:
    """
    Mint new token on the Algorand blockchain.

    Args:
        client (algod.AlgodClient): An instance of the `algod.AlgodClient` class representing the Algorand node.
        jwt (str): The JWT for accessing the Piñata API.
        creator_account (Account): An instance of the `Account` class representing the account that
        will create the token.
        asset_name (str): A string representing the name of the token.
        unit_name (str): A string representing the unit name of the token.
        total (int): An integer representing the total supply of the token.
        token_metadata (TokenMetadata): An instance of the `TokenMetadata` class representing the metadata of the token.
        mutable (bool): A boolean indicating whether the token is mutable or not.
        image_path (pathlib.Path | None, optional): A `pathlib.Path` object representing the path to the
        image file associated with the token. Defaults to None.
        decimals (int | None, optional): An integer representing the number of decimal places for the token.
        Defaults to 0.

    Returns:
        tuple[int, str]: A tuple containing the asset index and transaction ID of the minted token.

    Raises:
        ValueError: If the token name in the metadata JSON does not match the provided asset name.
        ValueError: If the decimals in the metadata JSON does not match the provided decimals amount.
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

    asset_config_params = AssetConfigTxnParams(
        sender=creator_account.address,
        sp=client.suggested_params(),
        reserve=_reserve_address_from_cid(metadata_cid) if mutable else "",
        unit_name=unit_name,
        asset_name=token_metadata.name,
        url=_create_url_from_cid(metadata_cid) + "#arc3" if mutable else "ipfs://" + metadata_cid + "#arc3",
        manager=creator_account.address if mutable else "",
        total=total,
        decimals=token_metadata.decimals,
    )

    logger.debug(f"Asset config params: {asset_config_params.to_json()}")
    asset_config_txn = _create_asset_txn(
        asset_config_params=asset_config_params,
        token_metadata=token_metadata,
        use_metadata_hash=not mutable,
    )
    signed_asset_config_txn = asset_config_txn.sign(creator_account.private_key)  # type: ignore[no-untyped-call]
    asset_config_txn_id = client.send_transaction(signed_asset_config_txn)
    response = wait_for_confirmation(client, asset_config_txn_id, 4)

    return response["asset-index"], asset_config_txn_id
