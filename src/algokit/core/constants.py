import os
from typing import TypedDict

# ===============================
#           Constants
# ===============================

ALGOKIT_CONFIG = ".algokit.toml"
DEFAULT_ALGOD_SERVER = "http://localhost"
DEFAULT_ALGOD_TOKEN = "a" * 64
DEFAULT_ALGOD_PORT = 4001
DEFAULT_INDEXER_PORT = 8980
DEFAULT_WAIT_FOR_ALGOD = 60
DEFAULT_HEALTH_TIMEOUT = 1
ALGOD_HEALTH_URL = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/v2/status"
GITPOD_URL = os.environ.get("GITPOD_WORKSPACE_URL")

LOCALNET = "localnet"
MAINNET = "mainnet"
BETANET = "betanet"
TESTNET = "testnet"

DEFAULT_NETWORKS = [LOCALNET, MAINNET, BETANET, TESTNET]

DEPLOYER_KEY = "DEPLOYER_MNEMONIC"
DISPENSER_KEY = "DISPENSER_MNEMONIC"

# ===============================
# Network configuration constants
# ===============================


class AlgorandNetworkConfigurationRequired(TypedDict):
    ALGOD_SERVER: str


class AlgorandNetworkConfiguration(AlgorandNetworkConfigurationRequired, total=False):
    ALGOD_PORT: str
    ALGOD_TOKEN: str

    INDEXER_SERVER: str
    INDEXER_PORT: str
    INDEXER_TOKEN: str


class AlgorandNetworkConfigurationWithKMD(AlgorandNetworkConfiguration, total=False):
    KMD_TOKEN: str
    KMD_URL: str
    KMD_PORT: str


localnet_config: dict[str, AlgorandNetworkConfigurationWithKMD] = {
    LOCALNET: {
        "ALGOD_SERVER": GITPOD_URL.replace("https://", "https://4001-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "INDEXER_SERVER": GITPOD_URL.replace("https://", "https://8980-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "ALGOD_PORT": str(443 if GITPOD_URL else DEFAULT_ALGOD_PORT),
        "ALGOD_TOKEN": DEFAULT_ALGOD_TOKEN,
        "INDEXER_PORT": str(443 if GITPOD_URL else DEFAULT_INDEXER_PORT),
        "INDEXER_TOKEN": DEFAULT_ALGOD_TOKEN,
        "KMD_TOKEN": DEFAULT_ALGOD_TOKEN,
        "KMD_PORT": str(443 if GITPOD_URL else DEFAULT_ALGOD_PORT + 1),
        "KMD_URL": GITPOD_URL.replace("https://", "https://4002-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
    }
}

other_networks_config: dict[str, AlgorandNetworkConfiguration] = {
    TESTNET: {
        "ALGOD_TOKEN": "",
        "ALGOD_SERVER": "https://testnet-api.algonode.cloud",
        "ALGOD_PORT": "",
        "INDEXER_TOKEN": "",
        "INDEXER_SERVER": "https://testnet-idx.algonode.cloud",
        "INDEXER_PORT": "",
    },
    BETANET: {
        "ALGOD_TOKEN": "",
        "ALGOD_SERVER": "https://betanet-api.algonode.cloud",
        "ALGOD_PORT": "",
        "INDEXER_TOKEN": "",
        "INDEXER_SERVER": "https://betanet-idx.algonode.cloud",
        "INDEXER_PORT": "",
    },
    MAINNET: {
        "ALGOD_TOKEN": "",
        "ALGOD_SERVER": "https://mainnet-api.algonode.cloud",
        "ALGOD_PORT": "",
        "INDEXER_TOKEN": "",
        "INDEXER_SERVER": "https://mainnet-idx.algonode.cloud",
        "INDEXER_PORT": "",
    },
}

ALGORAND_NETWORKS: dict[str, AlgorandNetworkConfiguration | AlgorandNetworkConfigurationWithKMD] = {
    **localnet_config,
    **other_networks_config,
}
