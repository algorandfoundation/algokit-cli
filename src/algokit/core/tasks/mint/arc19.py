import hashlib
import mimetypes
import pathlib
import re

import multihash
from algokit_utils import Account
from algosdk import encoding
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk.v2client import algod
from multiformats_cid.cid import make_cid

from algokit.core.tasks.ipfs import upload_to_web3_storage
from algokit.core.tasks.mint.arc3 import TokenMetadata, create_asset_txn


def reserve_address_from_cid(cid: str):
    decoded_cid = multihash.decode(make_cid(cid).multihash)
    reserve_address = encoding.encode_address(decoded_cid.digest)
    assert encoding.is_valid_address(reserve_address)
    return reserve_address


def version_from_cid(cid: str):
    return make_cid(cid).version


def codec_from_cid(cid: str):
    return make_cid(cid).codec


def hash_from_cid(cid: str):
    return multihash.decode(make_cid(cid).multihash).name


def create_url_from_cid(cid: str):
    version = version_from_cid(cid)
    codec = codec_from_cid(cid)
    hash = hash_from_cid(cid)
    url = f"template-ipfs://{{ipfscid:{version}:{codec}:reserve:{hash}}}"
    valid = re.compile(
        r"template-ipfs://{ipfscid:(?P<version>[01]):(?P<codec>[a-z0-9\-]+):(?P<field>[a-z0-9\-]+):(?P<hash>[a-z0-9\-]+)}"
    )
    assert bool(valid.match(url))
    return url


def create_acgf_txn(
    client: algod.AlgodClient,
    nft_metadata: TokenMetadata,
    metadata_cid: str,
    unit_name: str,
    sender: str,
    manager: str,
) -> AssetConfigTxn:
    url_prefix_arc19 = create_url_from_cid(metadata_cid)
    reserve_address_arc19 = reserve_address_from_cid(metadata_cid)

    return create_asset_txn(
        token_metadata=nft_metadata,
        unit_name=unit_name,
        asset_name=nft_metadata.name,
        url=url_prefix_arc19,
        sender=sender,
        sp=client.suggested_params(),
        manager=manager,
        reserve=reserve_address_arc19,
        metadata_hash=False,
    )


def file_integrity(filename: pathlib.Path) -> str:
    with filename.open("rb") as f:
        file_bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(file_bytes).hexdigest()
        return "sha-256" + readable_hash


def file_mimetype(filename: pathlib.Path) -> str:
    extension = pathlib.Path(filename).suffix
    return mimetypes.types_map[extension]


def mint_arc19_token(
    client: algod.AlgodClient,
    api_key: str,
    acct_sender: Account,
    metadata_file: pathlib.Path,
    image_file: pathlib.Path,
    unit_name: str,
) -> int:
    nft_metadata = TokenMetadata.from_json_file(metadata_file)
    nft_metadata.image_integrity = file_integrity(image_file)
    nft_metadata.image_mimetype = file_mimetype(image_file)
    nft_metadata_path = nft_metadata.to_file_path()
    nft_metadata.image = "ipfs://" + upload_to_web3_storage(image_file, api_key=api_key)

    metadata_cid = upload_to_web3_storage(nft_metadata_path, api_key=api_key, name=metadata_file.name)

    txn = create_acgf_txn(client, nft_metadata, metadata_cid, unit_name, acct_sender.address, acct_sender.address)

    txid = client.send_transaction(txn.sign(acct_sender.private_key))
    res = wait_for_confirmation(client, txid, 4)
    return res["asset-index"]
