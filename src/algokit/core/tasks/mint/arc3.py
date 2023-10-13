import base64
import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from algosdk import transaction


@dataclass
class Properties:
    arbitrary_attributes: dict[str, str | int | float | dict | list]


@dataclass
class LocalizationIntegrity:
    locale_hashes: dict[str, str]


@dataclass
class Localization:
    uri: str
    default: str
    locales: list[str]
    integrity: LocalizationIntegrity


@dataclass
class TokenMetadata:
    name: str
    description: str
    properties: Properties
    decimals: int = 0
    image: str | None = None
    image_integrity: str | None = None
    image_mimetype: str | None = None
    background_color: str | None = None
    external_url: str | None = None
    external_url_integrity: str | None = None
    external_url_mimetype: str | None = None
    animation_url: str | None = None
    animation_url_integrity: str | None = None
    animation_url_mimetype: str | None = None
    localization: Localization | None = None
    extra_metadata: str | None = None

    def __post_init__(self):
        if self.image_mimetype and not self.image_mimetype.startswith("image/"):
            raise ValueError("image_mimetype must start with 'image/'")
        if self.external_url_mimetype and self.external_url_mimetype != "text/html":
            raise ValueError("external_url_mimetype must be 'text/html'")
        if self.background_color and (
            len(self.background_color) != 6
            or not all(char.isdigit() or char.islower() for char in self.background_color)
        ):
            raise ValueError("background_color must be a six-character hexadecimal without a pre-pended #.")

    def to_json(self, indent: int | None = 4) -> str:
        # Filter out None values before converting to JSON
        data_dict = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data_dict, indent=indent)

    # Persist to a tmp directory and return the path
    def to_file_path(self) -> Path:
        file_path = Path(tempfile.mkstemp()[1])
        try:
            with file_path.open("w") as file:
                json.dump(asdict(self), file)
            return file_path
        except FileNotFoundError as err:
            raise ValueError(f"No such file or directory: '{file_path}'") from err
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to decode JSON from file {file_path}: {e}") from err

    @classmethod
    def from_json_file(cls: type["TokenMetadata"], file_path: Path) -> "TokenMetadata":
        try:
            with file_path.open() as file:
                data = json.load(file)
            return cls(**data)
        except FileNotFoundError as err:
            raise ValueError(f"No such file or directory: '{file_path}'") from err
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to decode JSON from file {file_path}: {e}") from err


def create_asset_txn(
    *,
    token_metadata: TokenMetadata,
    sender: str,
    sp: object,
    unit_name: str,
    asset_name: str,
    url: str,
    manager: str,
    reserve: str,
    freeze: str = "",
    clawback: str = "",
    note: str = "",
    total: int = 1,
    default_frozen: bool = False,
    lease: str = "",
    rekey_to: str = "",
    metadata_hash: bool = True,
) -> transaction.AssetConfigTxn:
    metadata = json.loads(token_metadata.to_json())

    if metadata_hash:
        h = hashlib.new("sha512_256")
        h.update(b"arc0003/amj")
        h.update(metadata.encode("utf-8"))
        json_metadata_hash = h.digest()

        h = hashlib.new("sha512_256")
        h.update(b"arc0003/am")

        h.update(json_metadata_hash)
        if "extra_metadata" in metadata:
            h.update(base64.b64decode(metadata["extra_metadata"]))
        am = h.digest()
    else:
        am = ""

    transaction_dict = {
        "sender": sender,
        "sp": sp,
        "total": total,
        "default_frozen": default_frozen,
        "manager": manager,
        "reserve": reserve,
        "freeze": freeze,
        "clawback": clawback,
        "unit_name": unit_name,
        "asset_name": asset_name,
        "url": url,
        "metadata_hash": am,
        "note": note,
        "lease": lease,
        "strict_empty_address_check": False,
        "rekey_to": rekey_to,
    }

    return transaction.AssetConfigTxn(**transaction_dict)
