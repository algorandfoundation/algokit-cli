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

from algokit.core.tasks.ipfs import upload_to_web3_storage
from algokit.core.tasks.mint.models import AssetConfigTxnParams, TokenMetadata

logger = logging.getLogger(__name__)


def _reserve_address_from_cid(cid: str) -> str:
    # Workaround to fix `multiformats` package issue, remove first two bytes before using `encode_address`.
    # Initial fix using `py-multiformats-cid` and `multihash.decode` was dropped due to PEP 517 incompatibility.
    digest = CID.decode(cid).digest[2:]
    reserve_address = str(encoding.encode_address(digest))  # type: ignore[no-untyped-call]
    assert encoding.is_valid_address(reserve_address)  # type: ignore[no-untyped-call]
    return reserve_address


def _create_url_from_cid(cid: str) -> str:
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
    with filename.open("rb") as f:
        file_bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(file_bytes).hexdigest()
        return "sha-256" + readable_hash


def _file_mimetype(filename: pathlib.Path) -> str:
    extension = pathlib.Path(filename).suffix
    return mimetypes.types_map[extension]


def _create_asset_txn(
    *,
    asset_config_params: AssetConfigTxnParams,
    token_metadata: TokenMetadata,
    use_metadata_hash: bool = True,
) -> transaction.AssetConfigTxn:
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
    api_key: str,
    creator_account: Account,
    asset_name: str,
    unit_name: str,
    total: int,
    token_metadata: TokenMetadata,
    mutable: bool,
    image_path: pathlib.Path | None = None,
    decimals: int | None = 0,
) -> tuple[int, str]:
    if not token_metadata.name or token_metadata.name != asset_name:
        raise ValueError("Token name in metadata JSON must match CLI argument providing token name!")

    if token_metadata.decimals and token_metadata.decimals != decimals:
        raise ValueError("Token metadata JSON and CLI arguments providing decimals amount must be equal!")

    if image_path:
        token_metadata.image_integrity = _file_integrity(image_path)
        token_metadata.image_mimetype = _file_mimetype(image_path)
        logger.info("Uploading image to Web3 Storage...")
        token_metadata.image = "ipfs://" + upload_to_web3_storage(image_path, api_key=api_key)
        logger.info(f"Image uploaded to Web3 Storage: {token_metadata.image}")

    logger.info("Uploading metadata to Web3 Storage...")
    metadata_cid = upload_to_web3_storage(
        token_metadata.to_file_path(),
        api_key=api_key,
    )
    logger.info(f"Metadata uploaded to Web3 Storage: {metadata_cid}")

    asset_config_params = AssetConfigTxnParams(
        sender=creator_account.address,
        sp=client.suggested_params(),
        reserve=_reserve_address_from_cid(metadata_cid) if mutable else "",
        unit_name=unit_name,
        asset_name=asset_name,
        url=_create_url_from_cid(metadata_cid) + "#arc3" if mutable else "ipfs://" + metadata_cid + "#arc3",
        manager=creator_account.address if mutable else "",
        total=total,
        decimals=decimals,
    )

    asset_config_txn = _create_asset_txn(
        asset_config_params=asset_config_params,
        token_metadata=token_metadata,
        use_metadata_hash=not mutable,
    )
    signed_asset_config_txn = asset_config_txn.sign(creator_account.private_key)  # type: ignore[no-untyped-call]
    asset_config_txn_id = client.send_transaction(signed_asset_config_txn)
    response = wait_for_confirmation(client, asset_config_txn_id, 4)

    return response["asset-index"], asset_config_txn_id
