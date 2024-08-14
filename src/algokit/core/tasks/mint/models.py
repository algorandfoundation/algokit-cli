import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from algosdk.transaction import SuggestedParams

MIN_BG_COLOR_LENGTH = 6  # Based on ARC-0003 spec, must be a 6 character hex without a pre-pended #


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
    decimals: int
    description: str | None = None
    properties: Properties | None = None
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

    def __post_init__(self) -> None:
        if self.image_mimetype and not self.image_mimetype.startswith("image/"):
            raise ValueError("image_mimetype must start with 'image/'")
        if self.external_url_mimetype and self.external_url_mimetype != "text/html":
            raise ValueError("external_url_mimetype must be 'text/html'")
        if self.background_color and (
            len(self.background_color) != MIN_BG_COLOR_LENGTH
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
                file.write(self.to_json(None))
            return file_path
        except FileNotFoundError as err:
            raise ValueError(f"No such file or directory: '{file_path}'") from err
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to decode JSON from file {file_path}: {err}") from err

    @classmethod
    def from_json_file(cls, file_path: Path | None, name: str, decimals: int = 0) -> "TokenMetadata":
        if not file_path:
            return cls(name=name, decimals=decimals)

        try:
            with file_path.open() as file:
                data = json.load(file)
                data["name"] = name
                data["decimals"] = decimals
            return cls(**data)
        except FileNotFoundError as err:
            raise ValueError(f"No such file or directory: '{file_path}'") from err
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to decode JSON from file {file_path}: {err}") from err


@dataclass
class AssetConfigTxnParams:
    sender: str
    sp: SuggestedParams
    unit_name: str
    asset_name: str
    url: str
    manager: str
    reserve: str
    total: int
    freeze: str | None = ""
    clawback: str | None = ""
    note: str | None = ""
    decimals: int = 0
    default_frozen: bool = False
    lease: str | None = ""
    rekey_to: str | None = ""
    metadata_hash: bytes | None = None
    strict_empty_address_check: bool = False

    def to_json(self, indent: int | None = 4) -> str:
        # Filter out None values before converting to JSON
        data_dict = {k: v for k, v in asdict(self).items() if v is not None and k != "sp"}
        return json.dumps(data_dict, indent=indent)
